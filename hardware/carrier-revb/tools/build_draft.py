#!/usr/bin/env python3
"""Draw the S4 schematic without changing the PCB or project settings.

The default and --schematic-only modes preserve the board. The explicit
--rebuild-unrouted-pcb option also creates the original PCB starting point, but
refuses any existing board with copper tracks, vias or copper-pour zones.
Requires KiCad 9's Python with pcbnew.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
SHARE = Path(os.environ.get("PITCLAW_KICAD_SHARE",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
NAME = "pitclaw-carrier"
parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--schematic-only", action="store_true", help="redraw schematic only (default); preserve PCB/project/footprints")
mode.add_argument("--rebuild-unrouted-pcb", action="store_true", help="also rebuild the original unrouted board; never overwrite routing")
args = parser.parse_args()
if args.rebuild_unrouted_pcb:
    board_path = ROOT / (NAME + ".kicad_pcb")
    if board_path.exists():
        existing = pcb.LoadBoard(str(board_path))
        if len(existing.GetTracks()) or any(not z.GetIsRuleArea() for z in existing.Zones()):
            parser.error("PCB contains routing or copper pours; refusing to rebuild it. Use --schematic-only.")
NS = uuid.UUID("27b13da5-06d9-4979-8d12-8761a109cf3b")
def uid(key): return str(uuid.uuid5(NS, key))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def vec(x, y): return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))

# Small S-expression reader preserves quoted strings while resolving library
# inheritance. Native graphical symbols are copied from installed KiCad libs.
class Quoted(str): pass
def parse(text):
    stack = [[]]
    for t in re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text):
        if t == "(":
            n = []; stack[-1].append(n); stack.append(n)
        elif t == ")": stack.pop()
        else: stack[-1].append(Quoted(json.loads(t)) if t.startswith('"') else t)
    assert len(stack) == 1
    return stack[0][0]
def dump(n):
    if isinstance(n, list): return "(" + " ".join(dump(x) for x in n) + ")"
    return q(n) if isinstance(n, Quoted) else str(n)
def children(n, key): return [a for a in n if isinstance(a, list) and a[0] == key]
def child(n, key): return next(a for a in n if isinstance(a, list) and a[0] == key)
libs = {}
def libsymbol(lib, name):
    if lib not in libs:
        tree = parse((SHARE / "symbols" / (lib + ".kicad_sym")).read_text())
        libs[lib] = {str(s[1]): s for s in children(tree, "symbol")}
    s = copy.deepcopy(libs[lib][name])
    ext = children(s, "extends")
    if ext:
        base = libsymbol(lib, str(ext[0][1])); old = str(base[1]); base[1] = Quoted(name)
        for sub in children(base, "symbol"):
            sub[1] = Quoted(str(sub[1]).replace(old + "_", name + "_", 1))
        overrides = {str(p[1]) for p in children(s, "property")}
        base = [v for v in base if not (isinstance(v, list) and v[0] == "property" and str(v[1]) in overrides)]
        base += children(s, "property")
        return base
    return s

def box_symbol(name, pins):
    """pins: number, label, electrical type, side (L/R)."""
    rows = max(sum(p[3] == side for p in pins) for side in ("L", "R"))
    halfh = max(5.08, (rows + 1) * 1.27)
    items = [f'(symbol {q(name)} (pin_names (offset 0.635)) (in_bom yes) (on_board yes)',
        '(property "Reference" "J" (at 0 0 0) (effects (font (size 1.27 1.27))))',
        f'(property "Value" {q(name)} (at 0 0 0) (effects (font (size 1.27 1.27))))',
        f'(symbol {q(name+"_0_1")} (rectangle (start -12.7 {halfh}) (end 12.7 {-halfh}) (stroke (width 0.254) (type default)) (fill (type background))))',
        f'(symbol {q(name+"_1_1")}']
    counts = {"L": 0, "R": 0}
    for num, label, typ, side in pins:
        y = (rows - 1) * 1.27 - counts[side] * 2.54; counts[side] += 1
        x, angle = (-17.78, 0) if side == "L" else (17.78, 180)
        items.append(f'(pin {typ} line (at {x} {y} {angle}) (length 5.08) (name {q(label)} (effects (font (size 1.0 1.0)))) (number {q(num)} (effects (font (size 1 1)))))')
    return parse("\n".join(items) + "))")

SYMS = {}
for lib, names in {"Device": ["R", "C", "C_Polarized", "D_Schottky", "Speaker"],
    "Connector": ["Barrel_Jack_Switch"],
    "Transistor_BJT": ["2N3904"], "Transistor_FET": ["Q_PMOS_GDS"],
    "Relay": ["G5Q-1"]}.items():
    for n in names: SYMS[n] = libsymbol(lib, n)
SYMS["PowerIn"] = box_symbol("PowerIn", [(1,"PD_OUT+","power_out","R"),(2,"GND","power_out","R")])
SYMS["Buck5V"] = box_symbol("Buck5V", [(1,"VIN+","power_in","L"),(2,"GND","power_in","L"),(3,"VOUT_5V","power_out","R")])
SYMS["EXT"] = box_symbol("EXT", [(n,l,t,"L") for n,l,t in [
    (1,"WT32_5V","power_in"),(2,"GND","passive"),(3,"GPIO10_SDA","bidirectional"),
    (4,"GPIO11_SCL","output"),(5,"GPIO12_FAN","output"),(6,"GPIO13_SERVO","output"),
    (7,"GPIO14_BUZZ","output"),(8,"GPIO21_SPARE","passive")]])
SYMS["Debug3V3"] = box_symbol("Debug3V3", [(1,"DEBUG_2_3V3","power_out","L"),(2,"DEBUG_7_GND","passive","L")])
SYMS["RJ45"] = box_symbol("RJ45", [(n,l,"passive","L") for n,l in enumerate(["NC","NC","SERVO_5V","COMMON_GND","FAN_12V_SW","SERVO_PWM","NC","NC"],1)])
SYMS["Probe"] = box_symbol("Probe", [(1,"SLEEVE","passive","R"),(2,"TIP_A","passive","R"),(3,"TIP_B","passive","R")])
SYMS["Jumper"] = box_symbol("Jumper", [(1,"5V_IN","passive","L"),(2,"WT32_5V","passive","R")])
SYMS["ADC_1x10"] = box_symbol("ADC_1x10", [(n,l,t,side) for n,l,t,side in [
    (1,"VDD","power_in","L"),(2,"GND","power_in","L"),(3,"SCL","input","L"),(4,"SDA","bidirectional","L"),
    (5,"ADDR","input","L"),(6,"ALRT","open_collector","R"),(7,"A0","input","R"),(8,"A1","input","R"),
    (9,"A2","input","R"),(10,"A3","input","R")]])
SYMS["PWR_FLAG"] = libsymbol("power", "PWR_FLAG")

RFP = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
CFP = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
KK2 = "Connector_Molex:Molex_KK-254_AE-6410-02A_1x02_P2.54mm_Vertical"
PARTS = []
def add(ref, value, sym, fp, nets, sch, pos, angle=0, dnp=False):
    PARTS.append(dict(ref=ref,value=value,sym=sym,fp=fp,nets={str(k):v for k,v in nets.items()},
        sch=sch,pos=pos,angle=angle,dnp=dnp,uuid=uid(ref)))
def two(ref,value,sym,fp,n1,n2,sch,pos,angle=0,dnp=False):
    add(ref,value,sym,fp,{1:n1,2:n2},sch,pos,angle,dnp)
def r(ref,val,n1,n2,sch,pos,dnp=False): two(ref,val,"R",RFP,n1,n2,sch,pos,0,dnp)
def c(ref,val,net,sch,pos,diam=None):
    fp = CFP if diam is None else f"Capacitor_THT:CP_Radial_D{diam[0]}mm_P{diam[1]}mm"
    two(ref,val,"C" if diam is None else "C_Polarized",fp,net,"GND",sch,pos)
add("J1","PD module output / 12V ONLY","PowerIn",KK2,{1:"PD_12V",2:"GND"},(35,45),(36,64))
add("J9","54-00133 / 12V CENTER +","Barrel_Jack_Switch","PitClaw:Tensility_54-00133_Horizontal",{1:"WALL_12V",2:"GND",3:None},(70,65),(14,30.5))
# Positive-only SPDT selection keeps the sources exclusive and their grounds common.
# Omron bottom-view drawing: 1/5 coil, 2 COM, 3 NO, 4 NC. Wall energizes coil.
add("K1","G5Q-1 DC12 / WALL PRIORITY","G5Q-1","PitClaw:Omron_G5Q1_SPDT_MaxBody",{1:"WALL_12V",2:"+12V",3:"WALL_12V",4:"PD_12V",5:"GND"},(125,115),(30.34,46.33),270)
two("D3","SB140 / COIL FLYBACK","D_Schottky","Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal","WALL_12V","GND",(235,100),(55,31),270)
c("C1","470u / 35V","+12V",(130,50),(29,82),("10.0","5.00"))
c("C2","100n / 50V","+12V",(175,50),(29,74.5))
add("U2","TSR 2-2450N / 5V 2A","Buck5V","PitClaw:TRACO_TSR_2N_SIP3",{1:"+12V",2:"GND",3:"+5V"},(275,50),(10,69))
c("C3","470u / 16V","+5V",(35,100),(18.5,72),("8.0","3.50"))
c("C4","100n / 50V","+5V",(85,100),(20,60))
add("JP1","REMOVE FOR WT32 USB","Jumper","Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",{1:"+5V",2:"+5V_WT32"},(185,100),(5,28))
add("Q1","IRF5305PBF","Q_PMOS_GDS","PitClaw:IRF5305_TO220_Horizontal_TabDown",{1:"FAN_GATE",2:"FAN_OUT",3:"+12V"},(345,55),(6,48))
r("R1","1k / 0.25W","+12V","FAN_GATE",(390,55),(18,46))
add("Q2","2N3904","2N3904","Package_TO_SOT_THT:TO-92_Inline",{1:"GND",2:"FAN_BASE",3:"FAN_GATE"},(440,55),(18,50))
r("R2","2.2k","GPIO12_FAN","FAN_BASE",(490,55),(5,36))
r("R3","100k","FAN_BASE","GND",(540,55),(18,36))
two("D2","SB140","D_Schottky","Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal","FAN_OUT","GND",(385,105),(6,54))
r("R4","220R","GPIO13_SERVO","SERVO_SIG",(430,105),(21,54))
r("R5","10k","SERVO_SIG","GND",(475,105),(20,57))
add("J2","RJHSE-5080 / CHECK FOOTPRINT","RJ45","PitClaw:RJHSE-5080_DRAFT",{1:None,2:None,3:"+5V",4:"GND",5:"FAN_OUT",6:"SERVO_SIG",7:None,8:None},(552,105),(18.435,84),180)
add("J3","WT32 EXT harness","EXT","Connector_Molex:Molex_KK-254_AE-6410-08A_1x08_P2.54mm_Vertical",{1:"+5V_WT32",2:"GND",3:"SDA",4:"SCL",5:"GPIO12_FAN",6:"GPIO13_SERVO",7:"GPIO14_BUZZ",8:None},(45,175),(12,6))
add("J7","WT32 DEBUG 2 / 7 ONLY","Debug3V3",KK2,{1:"+3V3_A",2:"GND"},(125,170),(40,6))
two("BZ1","PS1240P02BT / PASSIVE PIEZO","Speaker","PitClaw:Piezo_TDK_PS1240P02BT_D12.2_P5","BUZZ_DIRECT","GND",(365,170),(5,18))
r("R6","330R / PIEZO SERIES","GPIO14_BUZZ","BUZZ_DIRECT",(410,170),(5,25))
for i, label in enumerate(["PIT","MEAT 1","MEAT 2"]):
    yy=245+50*i
    add(f"J{4+i}",f"MJ1-2503A / {label}","Probe","PitClaw:MJ1-2503A",{1:"GND",2:f"PROBE{i}",3:f"PROBE{i}"},(45,yy),(60,19+17*i))
    r(f"R{10+i}","10k / 1%","+3V3_A",f"PROBE{i}",(110,yy),(30,37+7*i))
    r(f"R{13+i}","1k",f"PROBE{i}",f"AIN{i}",(170,yy),(42,37+7*i))
    c(f"C{10+i}","100n / 50V",f"AIN{i}",(225,yy),(42,32.5+7*i))
add("J8","ADS1115 BLUE / 1x10 SOCKET","ADC_1x10","PitClaw:ADS1115_Blue_1x10_DRAFT",{1:"+3V3_A",2:"GND",3:"SCL",4:"SDA",5:"GND",6:None,10:"AIN3",9:"AIN2",8:"AIN1",7:"AIN0"},(325,270),(25.24,26))
r("R16","1k","+3V3_A","AIN3",(385,250),(30,33.5))

# Mechanical r2: opposing SHORT connector edges for a landscape enclosure.
# Carrier mounts independently in the bottom shell. Mechanical r3 lays Q1 flat
# and moves only small internal parts. S4 locates RJ45/barrel faces at Y93.5;
# the recessed USB face is at Y91.5. Base-boss sweeps reserve sliding assembly.
placements = {
    'J2': (13.06, 85.88, 180),
    'J9': (26.5, 79.9, 90),
    'J4': (13, 0, 90),
    'J5': (30, 0, 90),
    'J6': (47, 0, 90),
    'J3': (12, 12, 0),
    'J7': (40, 12, 0),
    'J8': (13, 33, 0),
    'C10': (15, 38, 0),
    'R13': (26, 38, 0),
    'R10': (15, 42, 0),
    'C11': (15, 46, 0),
    'R14': (26, 45, 270),
    'R11': (15, 50, 0),
    'C12': (15, 54, 0),
    'R15': (26, 56, 270),
    'R12': (15, 58, 0),
    'R16': (26, 42, 0),
    'C3': (53.25, 14.5, 0),
    'C4': (30.5, 70, 270),
    'U2': (17, 70.75, 0),
    'C1': (43, 59, 0),
    'C2': (15, 65, 0),
    'J1': (54, 51, 0),
    'BZ1': (4.3, 43, 0),
    'Q1': (43.3, 41, 0),
    'R6': (7, 25, 270),
    'R1': (3, 14.5, 270),
    'R2': (7, 14, 270),
    'R3': (3, 52, 0),
    'R4': (3, 25, 270),
    'R5': (3, 56, 0),
    'JP1': (55, 23.5, 0),
    'K1': (30.34, 46.33, 270),
    'D2': (41.5, 45.5, 0),
    'D3': (55, 31, 270),
    'Q2': (5.5, 74, 0),
}
for p in PARTS:
    p["pos"] = placements[p["ref"]][:2]
    p["angle"] = placements[p["ref"]][2]
    if p["ref"] == "Q2": p["fp"] = "Package_TO_SOT_THT:TO-92_Inline_Wide"

# Purchasing selection is the common source for the CAD and priced BOM.
selection = json.loads((ROOT/"bom/selection.json").read_text())
by_ref = {ref: row for row in selection["parts"] for ref in row["refs"]}
assert set(by_ref) == {p["ref"] for p in PARTS}, "BOM / circuit reference mismatch"
for p in PARTS:
    row = by_ref[p["ref"]]
    for key in ("value", "fp"):
        if key in row: p[key] = row[key]
    assert p["dnp"] == row.get("dnp", False), ("DNP mismatch", p["ref"])

# Schematic symbols and net labels.
ROOT.mkdir(parents=True, exist_ok=True)
for sub in ["PitClaw.pretty","previews","verification"]: (ROOT/sub).mkdir(exist_ok=True)
lib_nodes = [dump(s) for s in SYMS.values()]
(ROOT/"PitClaw.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(lib_nodes)+')\n')
embedded=[]
for name,s in SYMS.items():
    sc=copy.deepcopy(s); sc[1]=Quoted("PitClaw:"+name); embedded.append(dump(sc))
# The schematic is drawn in functional blocks; all coordinates are independent
# of the carrier placement dictionary above. Named labels link blocks only.
root_uuid=uid("schematic")
sch=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {root_uuid}) (paper "A2")',
    '(title_block (title "Pit Claw carrier / relay source selection") (date "2026-09-06") (rev "S4") (comment 1 "ENGINEERING PROTOTYPE - VERIFY MODULES, LOADS AND ASSEMBLY BEFORE RELEASE"))',
    '(lib_symbols '+'\n'.join(embedded)+')']
def snap(v): return round(round(v/1.27)*1.27,4)
def text_at(s,x,y,size=1.6):
    sch.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {uid("text"+s+str((x,y)))}))')
def block(title,x1,y1,x2,y2):
    sch.append(f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.254) (type default)) (fill (type none)) (uuid {uid(title+"box")}))')
    text_at(title,x1+4,y1+3,2)
def symbol_pins(s):
    return [p for sub in children(s,"symbol") for p in children(sub,"pin")]
# x, y, schematic angle. Part identities and PCB angles/positions stay intact.
drawing = {
 'J1':(38.1,50.8,0), 'J9':(38.1,91.44,0), 'K1':(106.68,76.2,0), 'D3':(81.28,109.22,270),
 'U2':(254,66.04,0), 'C1':(210.82,85.09,0), 'C2':(228.6,85.09,0),
 'C3':(289.56,85.09,0), 'C4':(309.88,85.09,0), 'JP1':(299.72,116.84,0),
 'Q1':(398.78,60.96,180), 'R1':(426.72,60.96,0), 'Q2':(424.18,88.9,0),
 'R2':(396.24,88.9,90), 'R3':(408.94,109.22,0), 'D2':(370.84,81.28,270),
 'R4':(492.76,142.24,90), 'R5':(515.62,160.02,0), 'J2':(551.18,91.44,0),
 'J3':(116.84,195.58,0), 'J7':(48.26,219.71,0),
 'R6':(243.84,184.15,90), 'BZ1':(292.1,184.15,0),
 'J8':(289.56,302.26,0), 'R16':(274.32,361.95,90),
}
for i in range(3):
    yy=269.24+38.1*i
    drawing.update({f'J{4+i}':(43.18,yy,0), f'R{10+i}':(96.52,yy-7.62,0),
                    f'R{13+i}':(124.46,yy,90), f'C{10+i}':(154.94,yy+12.7,0)})
short_values = {
 'J1':'5807 PD output', 'J9':'54-00133 / center +', 'K1':'G5Q-1 DC12', 'D3':'SB140',
 'U2':'TSR 2-2450N / 5 V 2 A', 'J2':'RJHSE-5080', 'J3':'WT32 EXT / 8-way',
 'J7':'WT32 DEBUG 2 / 7', 'J8':'ADS1115 blue / 1x10', 'JP1':'WT32 5V disconnect',
 'BZ1':'PS1240P02BT', 'R6':'330R', 'C1':'470u / 35V', 'C3':'470u / 16V',
}
# Keep purchased Value fields intact; Drawing value is used only for annotation.
pin_at={}; pin_angle={}; connected=set()
for p in PARTS:
    x,y,angle=drawing[p['ref']]; x,y=snap(x),snap(y); s=SYMS[p['sym']]
    pins=symbol_pins(s)
    isbox=p['sym'] in ('PowerIn','Buck5V','EXT','Debug3V3','RJ45','Probe','Jumper','ADC_1x10')
    if isbox:
        height=max(abs(float(child(pin,'at')[2])) for pin in pins)
        prop_x,prop_y=x,y-height-8.89; justify=''
    elif p['sym']=='G5Q-1': prop_x,prop_y=x+21.59,y-3.81; justify='(justify left)'
    elif p['sym']=='Barrel_Jack_Switch': prop_x,prop_y=x-10.16,y-13.97; justify='(justify left)'
    elif (angle in (90,270) and p['sym']=='R') or (angle in (0,180) and p['sym']=='D_Schottky'):
        prop_x,prop_y=x,y-6.35; justify=''
    else: prop_x,prop_y=x+6.35,y-1.27; justify='(justify left)'
    if p['ref']=='Q1': prop_x,prop_y=x-1.27,y-21.59; justify=''
    if p['ref']=='Q2': prop_x,prop_y=x+6.35,y-1.27
    if p['ref'] in ('C1','C2','C3','C4'): prop_x,prop_y=x+3.81,y-2.54
    if p['ref'] in ('C1','C2'): prop_x,prop_y=x-3.81,y-2.54; justify='(justify right)'
    prop_angle=angle % 180
    props=f'(property "Reference" {q(p["ref"])} (at {prop_x} {prop_y} {prop_angle}) (effects (font (size 1.4 1.4)) {justify}))'
    props+=f'(property "Value" {q(p["value"])} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'
    props+=f'(property "Drawing value" {q(short_values.get(p["ref"],p["value"]))} (at {prop_x} {prop_y+2.54} {prop_angle}) (effects (font (size 1.15 1.15)) {justify}))'
    props+=f'(property "Footprint" {q(p["fp"])} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'
    row=by_ref[p['ref']]
    for field,key in (("Manufacturer","manufacturer"),("MPN","mpn"),("DigiKey","sku"),("Source","url")):
        props+=f'(property {q(field)} {q(row[key])} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'
    sch.append(f'(symbol (lib_id {q("PitClaw:"+p["sym"])}) (at {x} {y} {angle}) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if p["dnp"] else "no"}) (uuid {p["uuid"]}) {props}')
    for pin in pins:
        num=str(child(pin,'number')[1]); sch.append(f'(pin {q(num)} (uuid {uid(p["ref"]+"/"+num)}))')
        u,v,pa=map(float,child(pin,'at')[1:4]); rot=math.radians(angle)
        pin_at[p['ref'],num]=(round(x+u*math.cos(rot)-v*math.sin(rot),4),round(y-u*math.sin(rot)-v*math.cos(rot),4))
        pin_angle[p['ref'],num]=pa+angle
    sch.append(f'(instances (project {q(NAME)} (path {q("/"+root_uuid)} (reference {q(p["ref"])}) (unit 1)))))')
def P(ref,num): return pin_at[ref,str(num)]
wire_segments=[]; junction_points=set(); label_points=set()
def wire(*pts):
    for a,b in zip(pts,pts[1:]):
        a=tuple(round(v,4) for v in a); b=tuple(round(v,4) for v in b)
        if a==b: continue
        assert a[0]==b[0] or a[1]==b[1], ('nonorthogonal',a,b)
        wire_segments.append((a,b))
def joint(x,y):
    junction_points.add((x,y))
    sch.append(f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {uid("junction"+str((x,y)))}))')
def label(net,pt,right=False):
    label_points.add(pt)
    x,y=pt; just='right bottom' if right else 'left bottom'
    sch.append(f'(label {q(net)} (at {x} {y} 0) (effects (font (size 1.15 1.15)) (justify {just})) (uuid {uid("label"+net+str(pt))}))')
def attach(ref,num,*pts):
    connected.add((ref,str(num))); wire(P(ref,num),*pts)
def rail(net,y,refs,x1=None,x2=None):
    pts=[P(r,n) for r,n in refs]; xs=[pt[0] for pt in pts]
    x1=min(xs) if x1 is None else x1; x2=max(xs) if x2 is None else x2
    wire((x1,y),(x2,y)); label(net,(x1,y))
    for (ref,num),(x,_) in zip(refs,pts):
        attach(ref,num,(x,y))
        if x1<x<x2: joint(x,y)
# 01: raw inputs, wall-driven coil and physically exclusive relay contacts.
block('01  INPUT POWER / AUTOMATIC WALL PRIORITY',15,20,190,142)
attach('J1',1,(109.22,P('J1',1)[1]),(109.22,68.58)); connected.add(('K1','4'))
label('PD_12V',(58.42,P('J1',1)[1]))
# Wall feeds NO and coil; the jack's sleeve switch remains explicitly unused.
attach('J9',1,(68.58,P('J9',1)[1]),(68.58,58.42),(114.3,58.42),P('K1',3)); connected.add(('K1','3'))
label('WALL_12V',(68.58,58.42))
attach('K1',1,(101.6,100.33),(68.58,100.33),(68.58,P('J9',1)[1])); joint(68.58,P('J9',1)[1])
attach('D3',1,(81.28,100.33)); joint(81.28,100.33)
label('GND',(81.28,124.46)); attach('D3',2,(81.28,124.46))
attach('K1',2,(111.76,96.52),(163.83,96.52)); label('+12V',(163.83,96.52))
text_at('NC: USB PD     NO: wall     COM: selected +12V',20,129.5,1.35)
text_at('12 V regulated / 3 A maximum sources; common GND.',20,134.5,1.25)
# 02: local input/output bypassing and separate WT32 programming disconnect.
block('02  FIXED 5 V REGULATOR / WT32 DISCONNECT',195,20,350,142)
rail('+12V',53.34,[('C1',1),('C2',1),('U2',1)],205.74,236.22)
rail('GND',100.33,[('C1',2),('C2',2),('C3',2),('C4',2)],205.74,309.88)
attach('U2',2,(236.22,100.33)); joint(236.22,100.33)
rail('+5V',53.34,[('U2',3),('C3',1),('C4',1)],271.78,309.88)
attach('JP1',1,(279.4,116.84)); label('+5V',(279.4,116.84),True)
attach('JP1',2,(335.28,116.84)); label('+5V_WT32',(335.28,116.84))
text_at('Place C2 and C4 at U2 pins. Remove JP1 before',200,127.5,1.25)
text_at('powering the WT32 from its own programming USB.',200,132,1.25)
# 03: PMOS source at the top; reset pull-downs and freewheel return are visible.
block('03  HIGH-SIDE FAN / SERVO / POWERED RJ45',355,20,580,185)
rail('+12V',48.26,[('Q1',3),('R1',1)],378.46,426.72)
attach('Q1',1,(415.29,60.96),(415.29,73.66),(426.72,73.66),P('R1',2)); connected.add(('R1','2'))
attach('Q2',3,(426.72,73.66)); joint(426.72,73.66)
label('FAN_GATE',(426.72,73.66))
attach('Q1',2,(396.24,73.66),(370.84,73.66),P('D2',1)); connected.add(('D2','1'))
label('FAN_OUT',(370.84,73.66))
attach('D2',2,(370.84,119.38)); label('GND',(370.84,119.38))
attach('R2',2,P('Q2',2)); connected.add(('Q2','2'))
label('FAN_BASE',(408.94,88.9))
attach('R3',1,(408.94,88.9)); joint(408.94,88.9)
rail('GND',119.38,[('R3',2),('Q2',1)],408.94,426.72)
attach('R4',2,(515.62,142.24),P('R5',1)); connected.add(('R5','1'))
label('SERVO_SIG',(515.62,142.24))
attach('R5',2,(515.62,172.72)); label('GND',(515.62,172.72))
text_at('GPIO12 HIGH = fan ON; reset = OFF. Start PWM at 100 Hz.',360,166.5,1.25)
text_at('RJ45: 1.5 A/contact; pin 4 carries fan + servo return.',360,176.5,1.3)
# 04: module harnesses. These are connections to the WT32, not the WT32 PCB.
block('04  WT32 DISPLAY / CONTROL HARNESSES',15,150,190,237)
text_at('J3 is the EXT cable. J7 takes only DEBUG pins 2 and 7.',20,164,1.25)
text_at('3.3 V analog excitation and ADC power come from J7.',20,169,1.25)
# 05: passive piezo directly driven through the current-limiting resistor.
block('05  PASSIVE PIEZO',195,150,350,237)
attach('R6',2,P('BZ1',1)); connected.add(('BZ1','1'))
label('BUZZ_DIRECT',(261.62,184.15))
attach('BZ1',2,(281.94,P('BZ1',2)[1]),(281.94,205.74)); label('GND',(281.94,205.74))
text_at('GPIO14 -> 330R -> passive piezo. Use about 4 kHz.',200,218,1.25)
text_at('No DC buzzer or magnetic speaker substitution.',200,224,1.25)
# 06: each NTC and anti-alias filter is fully wired; AIN labels link to J8.
block('06  THREE NTC PROBES / FILTERS / SOCKETED ADS1115',15,242,350,391)
for i in range(3):
    j,rr,rp,cc=f'J{4+i}',f'R{13+i}',f'R{10+i}',f'C{10+i}'
    yy=P(j,2)[1]
    attach(j,2,(83.82,yy),P(rr,1)); connected.add((rr,'1'))
    attach(j,3,(83.82,P(j,3)[1]),(83.82,yy)); joint(83.82,yy)
    attach(rp,2,(96.52,yy)); joint(96.52,yy)
    attach(rr,2,(177.8,yy)); label(f'AIN{i}',(177.8,yy))
    attach(cc,1,(154.94,yy)); joint(154.94,yy)
    label(f'PROBE{i}',(100.33,yy))
    text_at(['PIT','MEAT 1','MEAT 2'][i],20,yy+13.97,1.25)
attach('R16',2,(309.88,361.95)); label('AIN3',(309.88,361.95))
text_at('AIN3 measures excitation through R16.',221,373,1.25)
text_at('ADDR = GND (0x48). ALRT is unused.',221,379,1.25)
text_at('NTC resistance = 10k * raw / (raw_supply - raw). Verify with known resistors before thermal calibration.',20,399,1.35)
# Unwired block interfaces use short native net-label stubs. Unused pins have NC.
for p in PARTS:
    for num,net in p['nets'].items():
        key=(p['ref'],num)
        if key in connected: continue
        px,py=P(*key)
        if net is None:
            sch.append(f'(no_connect (at {px} {py}) (uuid {uid(p["ref"]+num+"nc")}))'); continue
        theta=math.radians(pin_angle[key]); ex=round(px-5.08*math.cos(theta),4); ey=round(py+5.08*math.sin(theta),4)
        wire((px,py),(ex,ey)); label(net,(ex,ey),ex<px-.001)
# The connector/manual jumper and passive relay contacts need power-source flags.
for ref,net,x,y in [('#FLG01','+5V_WT32',330.2,123.19),('#FLG02','+12V',163.83,109.22)]:
    flag_id=uid(ref)
    pin_id=uid(ref+'pin'); sheet_path=q('/'+root_uuid)
    sch.append(f'(symbol (lib_id "PitClaw:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {flag_id}) (property "Reference" {q(ref)} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at {x} {y-5.08} 0) (effects (font (size 1 1)) (hide yes))) (pin "1" (uuid {pin_id})) (instances (project {q(NAME)} (path {sheet_path} (reference {q(ref)}) (unit 1)))))')
    label(net,(x,y))
block('ASSEMBLY / OPERATING NOTES',355,195,580,367)
notes=[
 'POWER SOURCES',
 'MOD1: Adafruit 5807, configured for 12 V / 3 A.',
 'J9: 5.5 x 2.1 mm, regulated 12 V, center positive.',
 'The J9 sleeve switch (pin 3) is unused.',
 'K1: coil pins 1/5; COM 2, NO 3, NC 4.',
 'D3 cathode is on raw WALL_12V; anode is on GND.',
 'Switchover may restart the controller.',
 'No onboard fuses: use protected/current-limited sources.',
 '', 'REGULATOR / ACTUATORS',
 'U2 supplies 5 V / 2 A total for WT32 and servo.',
 'RJ45: 1.5 A/contact; pin 4 is fan + servo return.',
 'This connector is NOT Ethernet or PoE.',
 'Confirm connector, cable and stall-current limits.',
 'Q1: pin 1 gate; pin 2 drain/live tab; pin 3 source.',
 'Q1 mounts flat on a 1 mm insulating support.',
 '', 'ADC / SENSORS',
 'J8 is the owned 28 x 17 mm blue ADS1115 module.',
 'Pin 1 = VDD; pin 10 = A3. Confirm module orientation.',
 'Module must provide local bypass and I2C pull-ups to VDD.',
 'Probe TIP_A and TIP_B contacts are intentionally joined.',
 '', 'BUILD STATUS',
 'Electrical revision S4; native labels connect between blocks.',
 'Module fit, load tests and thermal validation remain required.',
 'See README for release checks before fabrication/assembly.',
]
for i,n in enumerate(notes): text_at(n,360,208+i*5.6,1.35 if n not in ('POWER SOURCES','REGULATOR / ACTUATORS','ADC / SENSORS','BUILD STATUS') else 1.6)
# KiCad stores a distinct wire segment between each junction/label. Emit this
# canonical form ourselves instead of relying on load-time junction splitting.
split_points={p for s in wire_segments for p in s}|junction_points|label_points
emitted=set()
for a,b in wire_segments:
    points=sorted(p for p in split_points if min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1]))
    for start,end in zip(points,points[1:]):
        if (start,end) in emitted: continue
        emitted.add((start,end))
        sch.append(f'(wire (pts (xy {start[0]} {start[1]}) (xy {end[0]} {end[1]})) (stroke (width 0) (type default)) (uuid {uid("wire"+str((start,end)))}))')
sch.append('(embedded_fonts no))')
(ROOT/(NAME+'.kicad_sch')).write_text('\n'.join(sch)+'\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "PitClaw") (type "KiCad") (uri "${KIPRJMOD}/PitClaw.kicad_sym") (options "") (descr "Rev B local symbols")))\n')
# Export/compare native logical connectivity before any optional PCB operation.
cli=os.environ.get('PITCLAW_KICAD_CLI','/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
netlist_path=ROOT/'verification/schematic-netlist.xml'
subprocess.run([cli,'sch','export','netlist','--format','kicadxml','--output',str(netlist_path),str(ROOT/(NAME+'.kicad_sch'))],check=True)
netlist=ET.parse(netlist_path).getroot()
canonical_nets={(node.attrib['ref'],node.attrib['pin']):net.attrib['name'] for net in netlist.findall('./nets/net') for node in net.findall('node')}
for p in PARTS:
    for num,net in p['nets'].items():
        actual=canonical_nets.get((p['ref'],num),'')
        if net is not None:
            assert actual.lstrip('/')==net, ('schematic connectivity changed',p['ref'],num,net,actual)
        else:
            assert actual.startswith('unconnected-'), ('unused pin is connected',p['ref'],num,actual)
(ROOT/'verification/expected-pin-nets.json').write_text(json.dumps({p['ref']:p['nets'] for p in PARTS},indent=2)+'\n')
if not args.rebuild_unrouted_pcb:
    print('Schematic and logical netlist updated; PCB, project settings, footprints and parts list preserved.')
    raise SystemExit(0)
fp_libs = ["Capacitor_THT", "Connector_BarrelJack", "Connector_JST", "Connector_PinHeader_2.54mm",
           "Diode_THT", "Package_TO_SOT_THT", "Resistor_THT"]
(ROOT/"fp-lib-table").write_text('(fp_lib_table (version 7)\n'
    '  (lib (name "PitClaw") (type "KiCad") (uri "${KIPRJMOD}/PitClaw.pretty") (options "") (descr "Rev B draft custom footprints"))\n'
    + ''.join(f'  (lib (name "{name}") (type "KiCad") (uri "${{KICAD9_FOOTPRINT_DIR}}/{name}.pretty") (options "") (descr "KiCad 9 standard library"))\n' for name in fp_libs)
    + ')\n')

# Native footprints. Module and connector geometry is deliberately independent
# of copper routing; draft assumptions are described in README, not hidden.
def makefp(name,descr):
    f=pcb.FOOTPRINT(None); f.SetFPID(pcb.LIB_ID("PitClaw",name)); f.SetLibDescription(descr)
    f.SetAttributes(pcb.FP_THROUGH_HOLE); f.SetReference("REF**"); f.SetValue(name)
    f.Reference().SetPosition(vec(0,-3)); f.Reference().SetTextSize(vec(1,1))
    f.Reference().SetTextThickness(pcb.FromMM(.15))
    f.Value().SetVisible(False)
    return f
def fp_line(f,a,b,layer=pcb.F_SilkS,width=.12):
    if layer in (pcb.F_SilkS,pcb.B_SilkS): width=max(width,.15)
    s=pcb.PCB_SHAPE(f); s.SetShape(pcb.SHAPE_T_SEGMENT); s.SetStart(vec(*a)); s.SetEnd(vec(*b)); s.SetWidth(pcb.FromMM(width)); s.SetLayer(layer); f.Add(s)
def rect(f,x1,y1,x2,y2,layer=pcb.F_Fab):
    for a,b in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]: fp_line(f,a,b,layer)
def pad(f,n,x,y,size=(1.8,1.8),drill=(1,1),npth=False):
    p=pcb.PAD(f); p.SetNumber(str(n)); p.SetPosition(vec(x,y)); p.SetSize(vec(*size)); p.SetDrillSize(vec(*drill))
    p.SetAttribute(pcb.PAD_ATTRIB_NPTH if npth else pcb.PAD_ATTRIB_PTH)
    layers=pcb.LSET.AllCuMask(); layers.AddLayer(pcb.F_Mask); layers.AddLayer(pcb.B_Mask)
    p.SetLayerSet(layers)
    p.SetShape(pcb.PAD_SHAPE_CIRCLE if size[0]==size[1] else pcb.PAD_SHAPE_OVAL)
    if drill[0]!=drill[1]: p.SetDrillShape(pcb.PAD_DRILL_SHAPE_OBLONG)
    if str(n)=="1" and not npth: p.SetShape(pcb.PAD_SHAPE_RECT)
    f.Add(p)
    return p
custom={}
# Omron G5Q-1 data sheet, bottom-view drill map mirrored to component side.
# Five 1.3 mm holes, 7.62 mm between rows. Pin 2 common, 3 NO, 4 NC;
# 1/5 non-polarized coil. The 15.8 mm maximum housing sits on 0.4 mm feet.
f=makefp("Omron_G5Q1_SPDT_MaxBody", "Omron G5Q-1 DC12 SPDT, 20.3x10.3mm maximum housing; 16.2mm maximum seated height including 0.4mm molded feet; 1.3mm recommended drills. Pins1/5 coil,2COM,3NO,4NC.")
rect(f,-1.33,-8.96,18.97,1.34)
rect(f,-1.83,-9.46,19.47,1.84,pcb.F_CrtYd)
rect(f,-1.43,-9.06,19.07,1.44,pcb.F_SilkS)
for number,x,y in [(1,0,0),(2,10.16,0),(3,17.78,0),(4,15.24,-7.62),(5,0,-7.62)]:
    pad(f,number,x,y,(2.3,2.3),(1.3,1.3))
custom["Omron_G5Q1_SPDT_MaxBody"]=f

# Tensility 54-00133 Rev A, 2018-09-26: front to A13.6/B7.7/C10.8.
# Drawing specifies 0.8x1.5mm plated slots; C slot is rotated by 90 degrees.
# Pin A=center positive, B=sleeve/GND, C=unused sleeve-shunt terminal.
f=makefp("Tensility_54-00133_Horizontal", "Tensility54-00133 RevA exact nominal outline14.4x9mm,13.6mm front-to-pinA; 9x10.8mm front face, bore axis6.5mm abovePCB. Manufacturer0.8x1.5mm slots extended to0.8x1.6mm for JLCPCB2:1 slot aspect; sample fit required.")
rect(f,-13.6,-4.5,.8,4.5)
rect(f,-14.1,-5,1.3,5.95,pcb.F_CrtYd)
# The mouth protrudes beyond the PCB; omit silk over the projecting front.
fp_line(f,(-11.5,-4.6),(.8,-4.6))
fp_line(f,(-11.5,4.6),(-4.5,4.6))
pad(f,1,0,0,(1.8,2.5),(.8,1.6))
pad(f,2,-5.9,0,(1.8,2.5),(.8,1.6))
pad(f,3,-2.8,4.7,(2.5,1.8),(1.6,.8))
custom["Tensility_54-00133_Horizontal"]=f

# Infineon IRF5305 Rev 2.1 (2026-07-24), PG-TO220-3-U05 maxima:
# E=10.67, D=16.51, A=4.83, L1=4.06, lead b=1.01/c=0.61 mm.
# The 6 mm body-to-pad distance leaves the bend beyond L1 with an inner
# radius >=0.8 mm. Form supported leads before soldering; do not bend at mold.
# Keep the live drain tab 1 mm above PCB on cured insulating support material;
# retain with small insulating side fillets. No tab screw or PCB hole is used.
f=makefp("IRF5305_TO220_Horizontal_TabDown", "IRF5305PBF flat tab-down, latest Infineon Rev2.1 package maxima 10.67x16.51x4.83mm; 6mm formed-lead offset, 1mm insulated stand-off, 6.5mm assembly height reserve. Drain tab is live. No tab bolt. Physical lead-form/adhesive fit required.")
rect(f,-2.795,-22.51,7.875,-6.0)
rect(f,-3.295,-23.01,8.375,1.55,pcb.F_CrtYd)
# Tab split and its existing package hole are assembly graphics, not PCB drills.
fp_line(f,(-2.795,-15.65),(7.875,-15.65),pcb.F_Fab)
s=pcb.PCB_SHAPE(f);s.SetShape(pcb.SHAPE_T_CIRCLE);s.SetCenter(vec(2.54,-19.53));s.SetEnd(vec(4.58,-19.53));s.SetLayer(pcb.F_Fab);s.SetWidth(pcb.FromMM(.05));f.Add(s)
for i in range(3):
    x=2.54*i
    rect(f,x-.505,-6,x+.505,-1.05,pcb.F_Fab)
    pad(f,i+1,x,0,(2.1,2.1),(1.4,1.4))
fp_line(f,(-2.9,-22.65),(7.98,-22.65))
fp_line(f,(-2.9,-22.65),(-2.9,-5.85))
fp_line(f,(7.98,-22.65),(7.98,-5.85))
custom["IRF5305_TO220_Horizontal_TabDown"]=f

f=makefp("MJ1-2503A","Same Sky 2024-09-12 top-view drawing; verify actual lead/slot tolerances")
rect(f,-8,-2.55,0,2.55); rect(f,0,-2,3,2); rect(f,-8.7,-3,3.5,3,pcb.F_CrtYd)
pad(f,1,-8.1,0,(1.1,2.1),(.5,1.5)); pad(f,2,-6,-1.8,(2.1,1.1),(1.5,.5)); pad(f,3,-6,1.8,(2.1,1.1),(1.5,.5)); pad(f,"",-3.5,0,(1.2,1.2),(1.2,1.2),True)
fp_line(f,(-8,-2.55),(-.5,-2.55));fp_line(f,(-8,2.55),(-.5,2.55));custom["MJ1-2503A"]=f
f=makefp("RJHSE-5080_DRAFT","Amphenol P-RJHSE-X080 RevA includes RJHSE-5080:15.75x14.99x13.21mm,front-to-peg5.08mm,peg-to-pin1 2.54mm; drawing drill array reconciled, physical sample fit remains required.")
rect(f,-4.315,-7.62,11.435,7.37);rect(f,-4.815,-8.12,11.935,7.87,pcb.F_CrtYd)
fp_line(f,(-4.315,7.37),(11.435,7.37))
for side in [-4.315,11.435]:
    fp_line(f,(side,-5.5),(side,-4.5));fp_line(f,(side,-.5),(side,7.37))
for i in range(8): pad(f,i+1,1.016*i,1.78 if i%2 else 0,(1.5,1.5),(.89,.89))
for x in [-2.79,9.91]: pad(f,"",x,-2.54,(3.25,3.25),(3.25,3.25),True)
custom["RJHSE-5080_DRAFT"]=f
f=makefp("ADS1115_Blue_1x10_DRAFT","User-linked Components101 blue module: 28x17mm, VDD GND SCL SDA ADDR ALRT A0 A1 A2 A3; 2.54mm pitch and edge offsets need physical fit check")
rect(f,-2.54,-15.5,25.46,1.5)
rect(f,-3.04,-16,25.96,2,pcb.F_CrtYd)
rect(f,-1.27,-1.27,24.13,1.27,pcb.F_SilkS)
for i in range(10): pad(f,i+1,2.54*i,0,drill=(1.05,1.05))
custom["ADS1115_Blue_1x10_DRAFT"]=f
f=makefp("TRACO_TSR_2N_SIP3","Traco TSR 2N manufacturer outline: 14x7.6x10.2mm SIP-3, 2.54mm pitch. Pin 1 VIN, 2 GND, 3 VOUT. Offset pin row; 1.4mm drills clear tolerated square pins.")
rect(f,-4.46,-1.44,9.54,6.16)
rect(f,-5.21,-2.19,10.29,6.91,pcb.F_CrtYd)
rect(f,-4.46,-1.44,9.54,6.16,pcb.F_SilkS)
for i in range(3): pad(f,i+1,2.54*i,0,(2.0,2.0),(1.4,1.4))
custom["TRACO_TSR_2N_SIP3"]=f
f=makefp("C_TDK_FG28X7R1H104KNT06_P5","TDK FG28X7R1H104KNT06 radial MLCC, 4x2.5mm body, 5.5mm maximum seated height; 5mm pitch. Lead-form/sample fit check required.")
rect(f,.5,-1.3,4.5,1.3);rect(f,-1.3,-1.8,6.3,1.8,pcb.F_CrtYd)
fp_line(f,(.5,-1.6),(4.5,-1.6));fp_line(f,(.5,1.6),(4.5,1.6))
pad(f,1,0,0,(1.8,1.8),(.9,.9));pad(f,2,5,0,(1.8,1.8),(.9,.9))
custom["C_TDK_FG28X7R1H104KNT06_P5"]=f
f=makefp("Piezo_TDK_PS1240P02BT_D12.2_P5","TDK PS1240P02BT manufacturer drawing: D12.2, 5mm pitch, 0.6mm leads, 7.8mm maximum seated height. Passive externally driven piezo.")
for layer, radius in [(pcb.F_Fab,6.1),(pcb.F_SilkS,6.2),(pcb.F_CrtYd,6.6)]:
    s=pcb.PCB_SHAPE(f);s.SetShape(pcb.SHAPE_T_CIRCLE);s.SetCenter(vec(2.5,0));s.SetEnd(vec(2.5+radius,0));s.SetLayer(layer);s.SetWidth(pcb.FromMM(.05 if layer==pcb.F_CrtYd else .12));f.Add(s)
pad(f,1,0,0,(1.8,1.8),(1,1));pad(f,2,5,0,(1.8,1.8),(1,1))
custom["Piezo_TDK_PS1240P02BT_D12.2_P5"]=f
io=pcb.PCB_IO_MGR.PluginFind(pcb.PCB_IO_MGR.KICAD_SEXP)
for name,f in custom.items(): io.FootprintSave(str(ROOT/"PitClaw.pretty"),f)

b=pcb.BOARD(); b.SetCopperLayerCount(2)
settings=b.GetDesignSettings(); settings.SetBoardThickness(pcb.FromMM(1.6)); settings.m_MinClearance=pcb.FromMM(.3)
settings.m_TrackMinWidth=pcb.FromMM(.3); settings.m_ViasMinSize=pcb.FromMM(.8); settings.m_MinThroughDrill=pcb.FromMM(.4)
nets={}
for n in sorted(set(canonical_nets.values())):
    net=pcb.NETINFO_ITEM(b,n); b.Add(net);nets[n]=net
for p in PARTS:
    if not p["fp"]: continue
    lib,fn=p["fp"].split(":")
    path=ROOT/"PitClaw.pretty" if lib=="PitClaw" else SHARE/"footprints"/(lib+".pretty")
    f=pcb.FootprintLoad(str(path),fn)
    if f is None: raise RuntimeError("Missing footprint: "+p["fp"])
    f.SetFPID(pcb.LIB_ID(lib,fn)); f.SetReference(p["ref"]);f.SetValue(p["value"])
    kp=pcb.KIID_PATH();kp.push_back(pcb.KIID(root_uuid));kp.push_back(pcb.KIID(p["uuid"]));f.SetPath(kp)
    if p["dnp"]: f.SetAttributes(f.GetAttributes() | pcb.FP_DNP)
    f.SetOrientationDegrees(p["angle"]);f.SetPosition(vec(100+p["pos"][0],50+p["pos"][1]))
    f.Reference().SetTextSize(vec(1,1));f.Reference().SetTextThickness(pcb.FromMM(.15));f.Value().SetVisible(False)
    f.Reference().SetLayer(pcb.F_Fab)  # Assembly references; silkscreen placement is a later release step.
    for graphic in f.GraphicalItems():
        if hasattr(graphic,"GetText"): graphic.SetLayer(pcb.F_Fab)
    for pp in f.Pads():
        number=pp.GetNumber()
        if not number: continue
        net=canonical_nets.get((p["ref"],number))
        if net is not None: pp.SetNet(nets[net])
    b.Add(f)
def board_line(a,bp,layer=pcb.Edge_Cuts,width=.05):
    s=pcb.PCB_SHAPE(b);s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(vec(100+a[0],50+a[1]));s.SetEnd(vec(100+bp[0],50+bp[1]));s.SetWidth(pcb.FromMM(width));s.SetLayer(layer);b.Add(s)
for a,bb in [((0,0),(60,0)),((60,0),(60,92)),((60,92),(0,92)),((0,92),(0,0))]: board_line(a,bb)
for i,(x,y) in enumerate([(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)],1):
    f=makefp("Mount_M3_D3.2_CLEARANCE","Independent carrier-to-base M3 mount; 7mm top hardware envelope, 9mm underside insert boss")
    f.SetReference("H"+str(i));pad(f,"",0,0,(3.2,3.2),(3.2,3.2),True)
    for layer,radius in [(pcb.F_CrtYd,3.5),(pcb.B_CrtYd,4.5)]:
        s=pcb.PCB_SHAPE(f);s.SetShape(pcb.SHAPE_T_CIRCLE);s.SetCenter(vec(0,0));s.SetEnd(vec(radius,0));s.SetLayer(layer);s.SetWidth(pcb.FromMM(.05));f.Add(s)
    f.SetAttributes(pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES | pcb.FP_BOARD_ONLY)
    io.FootprintSave(str(ROOT/"PitClaw.pretty"),f)
    f.SetPosition(vec(100+x,50+y));b.Add(f)
# The carrier slides 4 mm towards the power wall before lowering onto posts.
# Each 9 mm boss sweeps from native y+4 back to y. Conservative bounding
# rectangles reserve the entire underside sweep, including solder tails;
# the actual mechanical collision checker uses rounded bosses and pad fillets.
for i,(x,y) in enumerate([(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)],1):
    zone=pcb.ZONE(b); zone.SetIsRuleArea(True)
    zone.SetZoneName("CARRIER_BASE_BOSS_SWEEP_"+str(i))
    layers=pcb.LSET(); layers.AddLayer(pcb.B_Cu); zone.SetLayerSet(layers)
    zone.SetDoNotAllowTracks(True); zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowCopperPour(True); zone.SetDoNotAllowPads(True)
    zone.SetDoNotAllowFootprints(False)  # The mount's own NPTH lies in its boss.
    outline=zone.Outline(); outline.NewOutline()
    for px,py in [(x-4.5,y-4.5),(x+4.5,y-4.5),(x+4.5,y+8.5),(x-4.5,y+8.5)]:
        outline.Append(pcb.FromMM(100+px),pcb.FromMM(50+py))
    # Exclude only the existing 3.2 mm mechanical drill, with 0.10 mm margin.
    # Its native hole-clearance rule still prevents copper or another pad here.
    hole=outline.NewHole(0)
    for n in range(32):
        angle=n*2*math.pi/32
        px,py=x+1.70*math.cos(angle),y+1.70*math.sin(angle)
        outline.Append(pcb.FromMM(100+px),pcb.FromMM(50+py),0,hole)
    b.Add(zone)
# Top washers need copper clearance as well as the existing component keepout.
# The 1.70 mm circular cutout admits the NPTH, never exposed washer corners.
for i,(x,y) in enumerate([(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)],1):
    zone=pcb.ZONE(b); zone.SetIsRuleArea(True)
    zone.SetZoneName('CARRIER_TOP_WASHER_'+str(i))
    layers=pcb.LSET(); layers.AddLayer(pcb.F_Cu); zone.SetLayerSet(layers)
    zone.SetDoNotAllowTracks(True); zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowPads(True); zone.SetDoNotAllowCopperPour(True)
    zone.SetDoNotAllowFootprints(False)
    outline=zone.Outline(); outline.NewOutline()
    for n in range(32):
        angle=n*2*math.pi/32; radius=3.7/math.cos(math.pi/32)
        outline.Append(pcb.FromMM(100+x+radius*math.cos(angle)),pcb.FromMM(50+y+radius*math.sin(angle)))
    hole=outline.NewHole(0)
    for n in range(32):
        angle=n*2*math.pi/32
        outline.Append(pcb.FromMM(100+x+1.70*math.cos(angle)),pcb.FromMM(50+y+1.70*math.sin(angle)),0,hole)
    b.Add(zone)
# Q1's flat drain tab and formed leads are live FAN_OUT. Reserve the top
# copper beneath them; the PCB dielectric still permits a bottom ground plane.
# This rectangle is local to Q1 and stops 1.5 mm before its pad centers.
q1 = next(f for f in b.GetFootprints() if f.GetReference() == "Q1")
assert abs(q1.GetOrientationDegrees()) < 1e-6
zone = pcb.ZONE(b); zone.SetIsRuleArea(True)
zone.SetZoneName("Q1_LIVE_TAB_NO_COPPER")
layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu); zone.SetLayerSet(layers)
zone.SetDoNotAllowTracks(True); zone.SetDoNotAllowVias(True)
zone.SetDoNotAllowCopperPour(True); zone.SetDoNotAllowPads(True)
# Q1 itself must occupy the reservation; its full courtyard excludes other parts.
zone.SetDoNotAllowFootprints(False)
outline=zone.Outline(); outline.NewOutline()
for x,y in [(-3.295,-23.01),(8.375,-23.01),(8.375,-1.5),(-3.295,-1.5)]:
    outline.Append(q1.GetPosition().x+pcb.FromMM(x),q1.GetPosition().y+pcb.FromMM(y))
b.Add(zone)
# Passive base ledges support the connector end between enclosure screws.
# Keep soldered leads, vias and copper off these two underside contact patches.
for i, (x1, y1, x2, y2) in enumerate([(2,90.7,5,92),(56,90.7,59,92)], 1):
    zone = pcb.ZONE(b)
    zone.SetIsRuleArea(True)
    zone.SetZoneName("CARRIER_POWER_EDGE_SUPPORT_" + str(i))
    layers = pcb.LSET(); layers.AddLayer(pcb.B_Cu); zone.SetLayerSet(layers)
    zone.SetDoNotAllowTracks(True); zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowCopperPour(True); zone.SetDoNotAllowPads(True)
    zone.SetDoNotAllowFootprints(True)
    outline = zone.Outline(); outline.NewOutline()
    for x, y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:
        outline.Append(pcb.FromMM(100+x), pcb.FromMM(50+y))
    b.Add(zone)
def boardtext(t,x,y,size=1,layer=pcb.Dwgs_User):
    if layer in (pcb.F_SilkS,pcb.B_SilkS): size=max(size,1)
    tx=pcb.PCB_TEXT(b);tx.SetText(t);tx.SetPosition(vec(100+x,50+y));tx.SetTextSize(vec(size,size));tx.SetTextThickness(pcb.FromMM(.15));tx.SetLayer(layer);b.Add(tx)
boardtext("ADS1115 28x17\n1x10 / 2.54mm\nFIT CHECK REQUIRED",24.5,24,.85)
boardtext("UNROUTED - NOT FOR FABRICATION",30,-5,1.3)
boardtext("60 x 92 mm / M3 CARRIER MOUNTS / ENCLOSURE FIT REQUIRED",30,-2.5,.9)
boardtext("12V CONTROL\nNOT ETHERNET",9.5,98,.8)
boardtext("USB-C PD\n12V ONLY",44.5,98,.8)
boardtext("12V DC\n5.5x2.1 C+",26.5,98,.8)
for i,l in enumerate(["PIT","MEAT 1","MEAT 2"]):boardtext(l,13+17*i,-9,.9)
boardtext("PIT CLAW B-DRAFT",33,90.2,.8,pcb.F_SilkS)
# Apply the documented 5807 board outline, two mounting holes and socket protrusion.
from adafruit5807_geometry import update_board
update_board(b)
boardtext("B-T2F0-A5807-S4 / AUTOMATIC WALL PRIORITY / TSR2-2450N / NO FUSES",30,104,1)
boardtext("U2: PIN 1 VIN / 2 GND / 3 5V / FIXED 2A",30,106,0.8)
boardtext("TSR 2-2450N\n5V / 2A",19.5,71.5,.7)
boardtext("Q1 FLAT / LIVE TAB\n1 mm INSULATED SUPPORT",45.84,26.75,.65)
boardtext("K1 WALL PRIORITY\n16.2 mm MAX SEATED",34.15,55.15,.65)
pcb.SaveBoard(str(ROOT/(NAME+".kicad_pcb")),b)
project={"meta":{"filename":NAME+".kicad_pro","version":1},
    "board":{"design_settings":{"rules":{"min_clearance":.3,"min_track_width":.3,"min_via_diameter":.8,"min_through_hole_diameter":.4,"min_hole_clearance":.28,"min_hole_to_hole":.45,"min_silk_clearance":.15,"min_text_height":1.0,"min_text_thickness":.15},"rule_severities":{"unconnected_items":"error"}}},
    "net_settings":{"classes":[{"name":"Default","clearance":.3,"track_width":.3,"via_diameter":.8,"via_drill":.4,"microvia_diameter":.3,"microvia_drill":.1,"diff_pair_width":.3,"diff_pair_gap":.3,"diff_pair_via_gap":.3}],"meta":{"version":4}},
    "schematic":{"drawing":{"default_line_thickness":6},"meta":{"version":1}}}
(ROOT/(NAME+".kicad_pro")).write_text(json.dumps(project,indent=2)+"\n")
(ROOT/"verification"/"expected-pin-nets.json").write_text(json.dumps({p["ref"]:p["nets"] for p in PARTS},indent=2)+"\n")
(ROOT/"parts.md").write_text("# Rev B-T2F0-A5807-S4 assembly parts\n\nDigiKey selection checked 2026-09-05/06; see bom/ for priced purchasing lists.\nEngineering draft, not fabrication approval.\nU2 is the soldered TSR 2-2450N converter; J8 sockets the owned ADC module.\nMOD1 is the screw-mounted Adafruit 5807 breakout and connects to J1 by a short\n20-22 AWG power pair. J9 is the switched 5.5 x 2.1 mm, center-positive 12 V\nbarrel inlet. K1 automatically selects wall power when its raw 12 V coil is\nenergized; otherwise its normally closed contact selects USB PD. The SPDT\ncontacts select only one positive input at a time; grounds remain common.\nJ9 pin 3 is unused because its switch closes to sleeve/GND. D3 protects the\nrelay coil: banded cathode to WALL_12V, anode to GND. A source change can restart\nthe controller; verify switching and supply brownout behavior on the assembly.\n\n| Ref | Value | Manufacturer part number | Footprint | Assembly |\n|---|---|---|---|---|\n"+"".join(f'| {p["ref"]} | {p["value"]} | {by_ref[p["ref"]]["mpn"]} | {p["fp"]} | {"DNP" if p["dnp"] else "THT"} |\n' for p in PARTS)+"\nK1 uses the exact SPDT G5Q-1 DC12: pins 1/5 coil, 2 COM, 3 NO, 4 NC.\nReserve 16.2mm seated height, including its 0.4mm molded feet. Wall input\npowers pin 1 and NO; pin 5 is GND, NC is PD_12V, COM is +12V.\n\nQ1 mounts flat with the live drain tab downward. Form the leads before soldering;\nuse a 6mm body-to-pad-row distance, bend only beyond the widened 4.06mm lead\nsection, and use an inner bend radius of at least 0.8mm. Clamp/support the leads\nbetween the bend and package; do not bend against the plastic body. Reserve\n6.5mm seated height including a 1mm insulating under-body support. Cure small\nelectrically insulating, electronics-compatible adhesive support/side fillets\nagainst a 1mm temporary spacing jig before soldering to retain Q1 for transport.\nRemove the jig after curing. Do not install a tab bolt. Fit-check the lead form,\nminimum under-body gap, adhesion and thermal behavior with the actual part.\n\nAlso required: WT32; owned blue 10-pin ADS1115; Adafruit 5807 MOD1; ADC\nfree-edge insulating support; insulating adhesive for Q1; 2x M2x10 provisional screws, 2x 3mm nylon spacers,\n4x M2 washers (5mm maximum OD) and 2x M2 nuts under the carrier; one adhesive insulating rear\nmodule support; harness mates, contacts, wire and one shunt for JP1; 4 M3 carrier screws into heat-set inserts in the bottom shell; WT32 mounts\nseparately inside the top bezel using an internal retainer and four small screws\nmatched to the WT32 rear blind bosses (diameter, thread and length require\nsample verification). Enclosure closure uses separate M3 screws/inserts.\nConfirm the owned ADC module has local bypassing and suitable SDA/SCL pull-ups\nto VDD before assembly. Use only protected/current-limited regulated 12 V input\nsources rated no more than 3 A; this revision has no onboard fuses. See\nbom/README.md for assembly cautions.\n")
print(f"Generated {sum(bool(p['fp']) for p in PARTS)} electrical footprints, {sum(n.startswith('/') for n in nets)} named nets, four independent M3 carrier holes plus two M2 Adafruit 5807 holes, zero routed tracks. Module/cable physical fit testing remains required.")
