#!/usr/bin/env python3
"""Check the current routed carrier, native connectivity and retained circuit.

Use --reports-dir /tmp/... for an isolated inspection while CAD is in progress.
Passing this checker does not qualify physical loads, fit or thermal behavior.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import pcbnew as pcb
from adafruit5807_geometry import CFG, holes, module_body, reserved_rectangles, keepout_polygon, usb_face

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("netlist",nargs="?",type=Path,help="Optional native netlist output path")
parser.add_argument("--reports-dir",type=Path,default=root/"verification",
                    help="Directory for native ERC/DRC and successful verification reports")
args=parser.parse_args()
reports=args.reports_dir
reports.mkdir(parents=True,exist_ok=True)
# KiCad can reset a project when a derivative board is saved under a different
# name. Refuse weakened fabrication rules even if their native DRC reports zero.
source_hashes={ext:hashlib.sha256((root/f'pitclaw-carrier.kicad_{ext}').read_bytes()).hexdigest()
               for ext in ('pcb','sch','pro')}
project=json.loads((root/'pitclaw-carrier.kicad_pro').read_text())
rules=project['board']['design_settings']['rules']
for rule,minimum in {'min_clearance':.3,'min_copper_edge_clearance':.5,
                     'min_hole_clearance':.28,'min_hole_to_hole':.45,
                     'min_silk_clearance':.15,'min_text_height':1.0,
                     'min_text_thickness':.15,'min_track_width':.3}.items():
    assert rules.get(rule,0)>=minimum,('Manufacturing rule weakened',rule,rules.get(rule),minimum)
assert all(c['clearance']>=.3 for c in project['net_settings']['classes']), 'Netclass clearance weakened'
# Always inspect current CAD, not yesterday's successful reports. Keep the
# optional netlist output path for existing callers.
cli=os.environ.get("PITCLAW_KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
netlist=args.netlist or reports/"schematic-netlist.xml"
netlist.parent.mkdir(parents=True,exist_ok=True)
for report in ("summary.json", "README.md"):
    (reports/report).unlink(missing_ok=True)
subprocess.run([cli,"sch","export","netlist","--format","kicadxml","--output",str(netlist),str(root/"pitclaw-carrier.kicad_sch")],check=True)
subprocess.run([cli,"sch","erc","--format","json","--severity-all","--output",str(reports/"erc.json"),str(root/"pitclaw-carrier.kicad_sch")],check=True)
subprocess.run([cli,"pcb","drc","--format","json","--severity-all","--schematic-parity","--output",str(reports/"drc.json"),str(root/"pitclaw-carrier.kicad_pcb")],check=True)
expected=json.loads((root/"verification/expected-pin-nets.json").read_text())
xml=ET.parse(netlist).getroot()
schematic={}
for net in xml.findall("./nets/net"):
    for node in net.findall("node"):
        key=(node.attrib["ref"],node.attrib["pin"])
        assert key not in schematic, ("Pin appears in multiple nets",key)
        schematic[key]=net.attrib["name"]
board=pcb.LoadBoard(str(root/"pitclaw-carrier.kicad_pcb"))
footprints={f.GetReference():f for f in board.GetFootprints()}
assert len(footprints)==len(list(board.GetFootprints())), "Duplicate footprint references"
electrical={ref for ref,f in footprints.items() if not f.GetAttributes() & pcb.FP_BOARD_ONLY}
assert electrical==set(expected), ("Unexpected/missing electrical footprints",electrical ^ set(expected))
checks=0
for ref,pins in expected.items():
    assert {p.GetNumber() for p in footprints[ref].Pads() if p.GetNumber()}==set(pins), ("Unexpected/missing electrical pads",ref)
    for num,net in pins.items():
        got=schematic.get((ref,num),"")
        if net is None:
            assert not got or got.startswith("unconnected-"), ("Unexpected schematic connection",ref,num,got)
        else:
            assert got=="/"+net, ("Schematic net mismatch",ref,num,net,got)
        checks+=1
        pads=[p for p in footprints[ref].Pads() if p.GetNumber()==num]
        assert len(pads)==1, ("Missing/duplicate pad",ref,num)
        got=pads[0].GetNetname()
        assert got==schematic.get((ref,num),""), ("PCB net mismatch",ref,num,net,got)
copper_items=list(board.GetTracks())
vias=[item for item in copper_items if isinstance(item,pcb.PCB_VIA)]
tracks=[item for item in copper_items if not isinstance(item,pcb.PCB_VIA)]
assert tracks, "Carrier must contain actual routed tracks"

def track_statistics(items):
    widths={}
    for track in items:
        width=round(pcb.ToMM(track.GetWidth()),4)
        bucket=widths.setdefault(width,{"count":0,"length_mm":0.0})
        bucket["count"]+=1
        bucket["length_mm"]+=pcb.ToMM(track.GetLength())
    return {"track_count":len(items),
            "length_mm":round(sum(pcb.ToMM(t.GetLength()) for t in items),3),
            "layers":dict(sorted(Counter(board.GetLayerName(t.GetLayer()) for t in items).items())),
            "widths":[{"width_mm":w,"count":d["count"],"length_mm":round(d["length_mm"],3)}
                      for w,d in sorted(widths.items())]}

# Trunk presence is a sanity check, not a blanket minimum width: short pad
# escapes and low-current resistor/capacitor branches can legitimately narrow.
# Report every width and its length so the actual load paths can be reviewed.
power_targets={"PD_12V":2.0,"WALL_12V":2.0,"+12V":2.0,"FAN_OUT":1.2,
               "+5V":1.2,"+5V_WT32":1.2}
power_routing={}
for net,target in power_targets.items():
    items=[t for t in tracks if t.GetNetname().lstrip("/")==net]
    assert items,("Power net lacks routed tracks",net)
    wide_length=sum(pcb.ToMM(t.GetLength()) for t in items if pcb.ToMM(t.GetWidth())>=target-1e-5)
    assert wide_length>=2.0,("Power net lacks a substantive planned-width trunk",net,target,wide_length)
    stats=track_statistics(items)
    stats.update({"planned_trunk_width_mm":target,"length_at_or_above_trunk_width_mm":round(wide_length,3),
                  "via_count":sum(v.GetNetname().lstrip("/")==net for v in vias),
                  "narrow_sections":[{"width_mm":round(pcb.ToMM(t.GetWidth()),4),
                      "length_mm":round(pcb.ToMM(t.GetLength()),3),"layer":board.GetLayerName(t.GetLayer()),
                      "start_mm":[round(pcb.ToMM(t.GetStart().x)-100,4),round(pcb.ToMM(t.GetStart().y)-50,4)],
                      "end_mm":[round(pcb.ToMM(t.GetEnd().x)-100,4),round(pcb.ToMM(t.GetEnd().y)-50,4)]}
                      for t in items if pcb.ToMM(t.GetWidth())<target-1e-5]})
    power_routing[net]=stats
ground_zones=[]
for zone in board.Zones():
    if zone.GetIsRuleArea() or zone.GetNetname().lstrip("/")!="GND": continue
    layers=[]
    for layer in zone.GetLayerSet().CuStack():
        filled=zone.GetFilledPolysList(layer)
        layers.append({"layer":board.GetLayerName(layer),"filled_regions":filled.OutlineCount(),
                       "filled_area_mm2":round(filled.Area()/1e12,3)})
    ground_zones.append({"name":zone.GetZoneName(),"filled":zone.IsFilled(),"layers":layers})
assert ground_zones and any(l["filled_area_mm2"]>0 for z in ground_zones for l in z["layers"]), \
       "The routed carrier must retain actual filled ground copper"

def ground_corridor_review():
    """Inspect saved copper geometry; no thermal or voltage-drop claim.

    Erosion removes corridors narrower than the specified width, with a
    0.01 mm numerical allowance so an exactly nominal-width track retains
    nonzero polygon area. Pad landings
    are allowed to meet a surviving region within the erosion distance plus
    0.05 mm, so short pad necks are not mistaken for long return bottlenecks.
    PTH landings are represented by their outer copper shape; this does not
    model drill resistance or qualify their current capacity.
    """
    refs=(("J1","2"),("J9","2"),("J2","4"),("U2","2"),("C1","2"),
          ("C2","2"),("C3","2"),("C4","2"),("D2","2"),
          ("J7","2"),("J8","2"),("J8","5"))
    landings={f"{ref}:{num}":next(p for p in footprints[ref].Pads() if p.GetNumber()==num)
              for ref,num in refs}
    ground_vias=[v for v in vias if v.GetNetname().lstrip('/')=='GND']
    for i,via in enumerate(sorted(ground_vias,key=lambda v:(v.GetPosition().x,v.GetPosition().y)),1):
        landings[f"GND_via_{i}"]=via
    # Only power-section plated pads and actual GND vias may bridge layers in
    # the power-return graph. The ADC/DEBUG landings are reported but cannot
    # serve as the sole layer transition for a power return.
    bridges=set(landings)-{'J7:2','J8:2','J8:5'}
    widths_to_check=(0,.5,1.0,1.2,1.5,2.0)
    result={"method":"Saved GND fills + GND tracks + outer pad/via copper, eroded separately per layer with 0.01 mm corridor-width numerical allowance; landing tolerance is erosion distance + 0.05 mm. Power-section PTH pads and actual GND vias may join surviving regions across layers; ADC/DEBUG pads are not power-return bridges. PTH/via drill resistance, copper thickness, current sharing, temperature and voltage drop are not modeled.","corridor_width_numerical_allowance_mm":.01,"layers":{}}
    for layer in (pcb.F_Cu,pcb.B_Cu):
        copper=pcb.SHAPE_POLY_SET()
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetNetname().lstrip('/')=='GND' and zone.GetLayerSet().Contains(layer):
                copper.BooleanAdd(zone.GetFilledPolysList(layer))
        for footprint in footprints.values():
            for pad in footprint.Pads():
                if pad.GetNetname().lstrip('/')=='GND' and pad.GetLayerSet().Contains(layer):
                    shape=pcb.SHAPE_POLY_SET()
                    pad.TransformShapeToPolygon(shape,layer,0,pcb.FromMM(.001),pcb.ERROR_INSIDE)
                    copper.BooleanAdd(shape)
        for track in tracks+ground_vias:
            if track.GetNetname().lstrip('/')=='GND' and track.GetLayerSet().Contains(layer):
                shape=pcb.SHAPE_POLY_SET()
                track.TransformShapeToPolygon(shape,layer,0,pcb.FromMM(.001),pcb.ERROR_INSIDE)
                copper.BooleanAdd(shape)
        copper.Simplify()
        widths={}
        for width in widths_to_check:
            eroded=pcb.SHAPE_POLY_SET(copper)
            erosion=max(0,(width-.01)/2)
            if width:
                eroded.Deflate(pcb.FromMM(erosion),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcb.FromMM(.001))
            groups=[]
            for i in range(eroded.OutlineCount()):
                region=eroded.UnitSet(i)
                touching=[name for name,pad in landings.items()
                          if region.Collide(pad.GetEffectiveShape(layer),pcb.FromMM(erosion+.05))]
                if touching:
                    groups.append({"area_mm2":round(region.Area()/1e12,3),"landings":sorted(touching)})
            widths[str(width)]=groups
        result['layers'][board.GetLayerName(layer)]=widths
    networks={}
    for width in widths_to_check:
        graph={name:set() for name in bridges}
        for layer in result['layers'].values():
            for region in layer[str(width)]:
                names=set(region['landings']) & bridges
                for name in names: graph[name].update(names-{name})
        visited={'J1:2'};pending=['J1:2']
        while pending:
            for name in graph[pending.pop()]-visited:
                visited.add(name);pending.append(name)
        networks[str(width)]=sorted(visited)
    result['power_return_reachable_from_J1_by_corridor_mm']=networks
    main={'J1:2','J9:2','U2:2','C1:2','C3:2','D2:2'}
    assert main<=set(networks['2.0']), \
        ('Main power returns lost the reviewed 2 mm two-layer corridor',main-set(networks['2.0']))
    assert main|{'J2:4'}<=set(networks['1.2']), \
        ('J2 combined blower/servo return lacks a 1.2 mm two-layer corridor',
         (main|{'J2:4'})-set(networks['1.2']))
    result['main_power_return_corridor_mm']=2.0
    result['j2_combined_return_corridor_mm']=1.2
    return result

ground_corridors=ground_corridor_review()
# Direct-drive piezo simplification is intentional. These deleted references must
# not silently return through a stale BOM or generated CAD file.
removed={'Q3','R7','R19','F1','F2','F3','F4','D1','C5','C7','C13','R17','R18','JP2'}
assert removed.isdisjoint(expected)
assert expected['R6']=={'1':'GPIO14_BUZZ','2':'BUZZ_DIRECT'}
assert expected['BZ1']=={'1':'BUZZ_DIRECT','2':'GND'}
# The jack switches its sleeve. K1 selects the positive source exclusively;
# D3 suppresses its raw-wall-powered coil. Check the manufacturer's actual
# pin map independently of generator-generated expected nets.
assert expected['J1']=={'1':'PD_12V','2':'GND'}
assert expected['J9']=={'1':'WALL_12V','2':'GND','3':None}
assert expected['K1']=={'1':'WALL_12V','2':'+12V','3':'WALL_12V','4':'PD_12V','5':'GND'}
assert expected['D3']=={'1':'WALL_12V','2':'GND'}
assert 'D4' not in expected
# Include break-before-make's open interval as well as both static contact
# positions, with empty/inserted jack and all combinations of powered inputs.
# This is a topology test; timing, bounce, contact inrush and brownout are bench tests.
source_states=0
for inserted in (False,True):
    for pd_on in (False,True):
        for wall_on in (False,True):
            if wall_on and not inserted: continue
            for selected,edge in (("OPEN",None),("PD",("2","4")),("WALL",("2","3"))):
                parent={n:n for n in schematic.values()}
                def group(n):
                    while parent[n]!=n: n=parent[n]
                    return n
                def join(a,b): parent[group(a)]=group(b)
                if not inserted: join(schematic['J9','2'],schematic['J9','3'])
                if edge: join(*(schematic['K1',pin] for pin in edge))
                pd=group(schematic['J1','1']);wall=group(schematic['J9','1'])
                gnd=group(schematic['J1','2']);load=group(schematic['U2','1'])
                assert len({pd,wall,gnd})==3, ("Source short/backfeed",inserted,selected)
                assert load!=gnd, ("Load short",inserted,selected)
                assert (load==pd)==(selected=="PD")
                assert (load==wall)==(selected=="WALL")
                # Only one source reaches the load, even with both live.
                supplying=int(pd_on and load==pd)+int(wall_on and load==wall)
                assert supplying<=1
                source_states+=1
assert source_states==18
def placed(f, xy):
    # Independent transformation of drawing dimensions, valid for any placement.
    a=math.radians(f.GetOrientationDegrees()); x,y=xy
    return (pcb.ToMM(f.GetPosition().x)-100+x*math.cos(a)+y*math.sin(a),
            pcb.ToMM(f.GetPosition().y)-50-x*math.sin(a)+y*math.cos(a))
j9=footprints['J9'];j9pads={p.GetNumber():p for p in j9.Pads()}
for num,xy in {'1':(0,0),'2':(-5.9,0),'3':(-2.8,4.7)}.items():
    x,y=placed(j9,xy); p=j9pads[num]
    assert abs(pcb.ToMM(p.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(p.GetPosition().y)-50-y)<1e-5
# G5Q manufacturer bottom view translated to the component-side footprint.
k1=footprints['K1'];k1pads={p.GetNumber():p for p in k1.Pads()}
assert str(k1.GetFPID().GetLibItemName())=='Omron_G5Q1_SPDT_MaxBody'
for n,xy in {'1':(0,0),'2':(10.16,0),'3':(17.78,0),
             '4':(15.24,-7.62),'5':(0,-7.62)}.items():
    x,y=placed(k1,xy);p=k1pads[n]
    assert abs(pcb.ToMM(p.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(p.GetPosition().y)-50-y)<1e-5
    assert abs(pcb.ToMM(p.GetDrillSize().x)-1.3)<1e-5
# Manufacturer converter dimensions/polarity, independent of placement.
assert expected['U2']=={'1':'+12V','2':'GND','3':'+5V'}
u2=footprints['U2'];u2pads={p.GetNumber():p for p in u2.Pads()}
for num,xx in [('1',0),('2',2.54),('3',5.08)]:
    x,y=placed(u2,(xx,0));p=u2pads[num]
    assert abs(pcb.ToMM(p.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(p.GetPosition().y)-50-y)<1e-5
    assert all(abs(pcb.ToMM(n)-1.4)<1e-5 for n in (p.GetDrillSize().x,p.GetDrillSize().y))
    assert all(abs(pcb.ToMM(n)-2.0)<1e-5 for n in (p.GetSize().x,p.GetSize().y))
u2_body=[v for g in u2.GraphicalItems() if isinstance(g,pcb.PCB_SHAPE) and g.GetLayer()==pcb.F_Fab for v in (g.GetStart(),g.GetEnd())]
assert u2_body
actual_body=(min(pcb.ToMM(v.x)-100 for v in u2_body),min(pcb.ToMM(v.y)-50 for v in u2_body),max(pcb.ToMM(v.x)-100 for v in u2_body),max(pcb.ToMM(v.y)-50 for v in u2_body))
corners=[placed(u2,xy) for xy in [(-4.46,-1.44),(9.54,-1.44),(9.54,6.16),(-4.46,6.16)]]
body=(min(x for x,y in corners),min(y for x,y in corners),max(x for x,y in corners),max(y for x,y in corners))
assert all(abs(a-b)<1e-5 for a,b in zip(actual_body,body)),('TSR 2N body envelope',actual_body)
# The user's short-end connector arrangement, checked from the actual footprints.
for ref,x in [('J4',13),('J5',30),('J6',47)]:
    face=placed(footprints[ref],(3,0))
    assert all(abs(a-b)<1e-5 for a,b in zip(face,(x,-3))),('Probe face',ref,face)
for ref,local,face in [('J2',(3.56,-7.62),(9.5,93.5)),('J9',(-13.6,0),(26.5,93.5))]:
    assert all(abs(a-b)<1e-5 for a,b in zip(placed(footprints[ref],local),face)),('Power face',ref)
assert all(abs(a-b)<1e-5 for a,b in zip(usb_face(),(44.5,91.5)))
# Flat Q1 is required by the thinner case. Independently check the current
# Infineon TO-220 envelope, G/D/S lead row, and live-tab copper reservation.
q1=footprints['Q1']
assert str(q1.GetFPID().GetLibItemName())=='IRF5305_TO220_Horizontal_TabDown'
q1pads={p.GetNumber():p for p in q1.Pads()}
for n,x in [('1',43.3),('2',45.84),('3',48.38)]:
    p=q1pads[n]
    assert abs(pcb.ToMM(p.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(p.GetPosition().y)-50-41)<1e-5
    assert abs(pcb.ToMM(p.GetDrillSize().x)-1.4)<1e-5
    assert abs(pcb.ToMM(p.GetSize().x)-2.1)<1e-5
q1body=[(40.505,18.49),(51.175,18.49),(51.175,35),(40.505,35)]
q1edges={frozenset((q1body[i],q1body[(i+1)%4])) for i in range(4)}
fabedges=set()
for g in q1.GraphicalItems():
    if isinstance(g,pcb.PCB_SHAPE) and g.GetLayer()==pcb.F_Fab and g.GetShape()==pcb.SHAPE_T_SEGMENT:
        fabedges.add(frozenset((round(pcb.ToMM(v.x)-100,4),round(pcb.ToMM(v.y)-50,4)) for v in (g.GetStart(),g.GetEnd())))
assert q1edges<=fabedges, 'Missing/moved horizontal Q1 body outline'
q1zones=[z for z in board.Zones() if z.GetZoneName()=='Q1_LIVE_TAB_NO_COPPER']
assert len(q1zones)==1
qz=q1zones[0]
assert qz.GetIsRuleArea() and qz.GetLayerSet().Contains(pcb.F_Cu)
assert qz.GetDoNotAllowTracks() and qz.GetDoNotAllowVias() and qz.GetDoNotAllowPads() and qz.GetDoNotAllowCopperPour()
outline=qz.Outline().COutline(0)
actual=[(round(pcb.ToMM(outline.CPoint(i).x)-100,4),round(pcb.ToMM(outline.CPoint(i).y)-50,4)) for i in range(outline.PointCount())]
assert actual==[(40.005,17.99),(51.675,17.99),(51.675,39.5),(40.005,39.5)]
assert not [z for z in board.Zones() if z.GetZoneName()=='MINI100_BODY_NO_COPPER']
# Adafruit-published module outline and two-hole pattern.
x1,y1,x2,y2=module_body()
pd_corners=[(round(100+x1,4),round(50+y1,4)),(round(100+x2,4),round(50+y1,4)),
            (round(100+x2,4),round(50+y2,4)),(round(100+x1,4),round(50+y2,4))]
pd_edges={frozenset((pd_corners[i],pd_corners[(i+1)%4])) for i in range(4)}
drawn_edges=set()
for item in board.GetDrawings():
    if isinstance(item,pcb.PCB_SHAPE) and item.GetLayer()==pcb.Dwgs_User and item.GetShape()==pcb.SHAPE_T_SEGMENT:
        endpoints=tuple((round(pcb.ToMM(p.x),4),round(pcb.ToMM(p.y),4)) for p in (item.GetStart(),item.GetEnd()))
        drawn_edges.add(frozenset(endpoints))
assert pd_edges <= drawn_edges, "Missing/moved Adafruit 5807 body reservation"
assert abs(usb_face()[1]-91.5)<1e-6
for ref,(x,y) in zip(("H5","H6"),holes()):
    f=footprints[ref];p=list(f.Pads())[0]
    assert abs(pcb.ToMM(f.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(f.GetPosition().y)-50-y)<1e-5
    assert p.GetAttribute()==pcb.PAD_ATTRIB_NPTH
    assert abs(pcb.ToMM(p.GetDrillSize().x)-CFG["carrier_hole_diameter_mm"])<1e-5
    assert p.GetNetname()==""
zones=[z for z in board.Zones() if z.GetZoneName()=="ADAFRUIT_5807_NO_COPPER"]
assert len(zones)==1, "Missing or duplicate Adafruit 5807 keepout"
z=zones[0]
assert z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetDoNotAllowVias() and z.GetDoNotAllowCopperPour()
assert z.GetLayerSet().Contains(pcb.F_Cu) and z.GetLayerSet().Contains(pcb.B_Cu)
outline=z.Outline().COutline(0)
actual_polygon=[(round(pcb.ToMM(outline.CPoint(i).x)-100,4),round(pcb.ToMM(outline.CPoint(i).y)-50,4)) for i in range(outline.PointCount())]
assert actual_polygon==[tuple(round(v,4) for v in pt) for pt in keepout_polygon()], "5807 keepout outline is stale"
collisions=[]
for ref in list(expected)+["H1","H2","H3","H4"]:
    f=footprints[ref];f.BuildCourtyardCaches();bb=f.GetCourtyard(pcb.F_Cu).BBox()
    bounds=tuple(pcb.ToMM(v) for v in (bb.GetX()-pcb.FromMM(100),bb.GetY()-pcb.FromMM(50),bb.GetRight()-pcb.FromMM(100),bb.GetBottom()-pcb.FromMM(50)))
    # Courtyards may touch the conservative copper margin; reject only an
    # intersection with the actual module/mount hardware envelope.
    for r in reserved_rectangles(-CFG["keepout_margin_mm"]):
        if max(bounds[0],r[0]) < min(bounds[2],r[2]) and max(bounds[1],r[1]) < min(bounds[3],r[3]):
            collisions.append(ref)
assert not collisions,("Component courtyard intersects reserved Adafruit 5807 region",collisions)
for h,(x,y) in zip(["H1","H2","H3","H4"],[(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)]):
    f=footprints[h]
    assert abs(pcb.ToMM(f.GetPosition().x)-100-x)<1e-5
    assert abs(pcb.ToMM(f.GetPosition().y)-50-y)<1e-5
    p=list(footprints[h].Pads())[0]
    assert abs(pcb.ToMM(p.GetDrillSize().x)-3.2)<1e-6
    assert p.GetAttribute()==pcb.PAD_ATTRIB_NPTH
washer_keepouts=[]
for i in range(1,5):
    name=f"CARRIER_TOP_WASHER_{i}"
    matched=[z for z in board.Zones() if z.GetZoneName()==name]
    assert len(matched)==1,("Missing/duplicate top mounting-hardware keepout",name)
    zone=matched[0]
    assert zone.GetIsRuleArea() and zone.GetLayerSet().Contains(pcb.F_Cu),name
    assert zone.GetDoNotAllowTracks() and zone.GetDoNotAllowVias() \
        and zone.GetDoNotAllowPads() and zone.GetDoNotAllowCopperPour(),name
    center=footprints[f"H{i}"].GetPosition()
    poly=zone.Outline()
    assert poly.OutlineCount()==1,("Unexpected washer keepout outline count",name)
    outline=poly.COutline(0)
    assert outline.PointCount()>=16,("Washer keepout must approximate a circle",name)
    # The polygon must cover a 7.4 mm disk, not merely have that bounding box.
    for j in range(outline.PointCount()):
        a=outline.CPoint(j);b=outline.CPoint((j+1)%outline.PointCount())
        ax,ay=pcb.ToMM(a.x-center.x),pcb.ToMM(a.y-center.y)
        bx,by=pcb.ToMM(b.x-center.x),pcb.ToMM(b.y-center.y)
        assert 3.7-1e-5<=math.hypot(ax,ay)<=3.8,("Washer keepout vertex radius",name,j)
        dx,dy=bx-ax,by-ay
        assert dx*dx+dy*dy>0,("Duplicate washer keepout vertices",name,j)
        u=max(0,min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy)))
        assert math.hypot(ax+u*dx,ay+u*dy)>=3.7-1e-5,("Washer keepout chord undercuts hardware margin",name,j)
    # The NPTH exemption must stay inside its drill-clearance region. Square
    # cutouts expose corners under the washer and therefore fail this check.
    for hole_idx in range(poly.HoleCount(0)):
        hole=poly.CHole(0,hole_idx)
        for j in range(hole.PointCount()):
            p=hole.CPoint(j)
            assert math.hypot(pcb.ToMM(p.x-center.x),pcb.ToMM(p.y-center.y))<=1.70001, \
                ("Washer keepout hole exposes copper under metal hardware",name)
    for degrees in range(0,360,15):
        a=math.radians(degrees)
        sample=pcb.VECTOR2I(center.x+pcb.FromMM(3.6*math.cos(a)),center.y+pcb.FromMM(3.6*math.sin(a)))
        assert poly.Contains(sample),("Washer annulus is not protected",name,degrees)
    washer_keepouts.append({"name":name,"mount":f"H{i}","layer":"F.Cu",
                            "protected_outer_diameter_mm":7.4,"npth_exemption_max_radius_mm":1.7})
    # The corresponding underside boss may have the same NPTH exemption;
    # guard against reintroducing the square opening there as well.
    boss=[z for z in board.Zones() if z.GetZoneName()==f"CARRIER_BASE_BOSS_SWEEP_{i}"]
    assert len(boss)==1,("Missing/duplicate underside mounting-boss sweep",i)
    bp=boss[0].Outline()
    for oi in range(bp.OutlineCount()):
        for hi in range(bp.HoleCount(oi)):
            hole=bp.CHole(oi,hi)
            for j in range(hole.PointCount()):
                p=hole.CPoint(j)
                assert math.hypot(pcb.ToMM(p.x-center.x),pcb.ToMM(p.y-center.y))<=1.70001, \
                    ("Boss keepout hole exceeds mounting-drill clearance",i)
erc=json.loads((reports/"erc.json").read_text())
ev=[v for sheet in erc["sheets"] for v in sheet["violations"]]
assert not ev, ("Native ERC violations",ev)
drc=json.loads((reports/"drc.json").read_text())
assert not drc["violations"], ("Native DRC violations",drc["violations"])
assert "unconnected_items" in drc,"Native DRC did not report connectivity"
assert not drc["unconnected_items"], ("Unrouted/unconnected native PCB items",drc["unconnected_items"])
assert "schematic_parity" in drc, "Run native DRC with --schematic-parity"
assert not drc["schematic_parity"], ("Native PCB/schematic parity issues",drc["schematic_parity"])
selection=json.loads((root/"bom/selection.json").read_text())
parts={ref:p for p in selection["parts"] for ref in p["refs"]}
assert set(parts)==set(expected), "BOM reference set differs from circuit"
for component in xml.findall("./components/comp"):
    ref=component.attrib["ref"]
    if ref not in parts: continue
    fields={f.attrib["name"]:f.text for f in component.findall("./fields/field")}
    assert fields["MPN"]==parts[ref]["mpn"], ("BOM/schematic MPN mismatch",ref)
    assert fields["DigiKey"]==parts[ref]["sku"], ("BOM/schematic SKU mismatch",ref)
    fp_id=footprints[ref].GetFPID()
    assert str(fp_id.GetLibNickname())+":"+str(fp_id.GetLibItemName())==component.findtext("footprint"), ("Footprint mismatch",ref)
dc=Counter(v["type"] for v in drc["violations"])
assert all(hashlib.sha256((root/f'pitclaw-carrier.kicad_{ext}').read_bytes()).hexdigest()==digest
           for ext,digest in source_hashes.items()), 'CAD or rules changed while checks were running'
report={"status":"ROUTED ENGINEERING PROTOTYPE - PHYSICAL QUALIFICATION PENDING","logical_pin_checks":checks,
    "pcb_sha256":hashlib.sha256((root/"pitclaw-carrier.kicad_pcb").read_bytes()).hexdigest(),
    "schematic_sha256":hashlib.sha256((root/"pitclaw-carrier.kicad_sch").read_bytes()).hexdigest(),
    "project_rules_sha256":hashlib.sha256((root/"pitclaw-carrier.kicad_pro").read_bytes()).hexdigest(),
    "schematic_pin_map_sha256":hashlib.sha256(json.dumps(sorted((ref,pin,net.lstrip('/')) for (ref,pin),net in schematic.items()),separators=(',',':')).encode()).hexdigest(),
    "electrical_footprints":len(expected),"unassigned_footprints":[],
    "adc_socket_status":"10-pin module from user link; pitch, body offsets and fit still need physical verification",
    "pd_module":"Adafruit 5807 HUSB238","pd_body_mm":CFG["source_board_outline_mm"],
    "pd_body_status":"Official PCB outline/hole geometry applied; physical cable and enclosure fit testing remain",
    "pd_mount_revision":CFG["revision"],"pd_mount_holes_mm":holes(),"pd_mount_drill_mm":CFG["carrier_hole_diameter_mm"],
    "usb_face_overhang_mm":round(usb_face()[1]-92,4),
    "pd_mount_courtyard_collisions":collisions,"pd_mount_copper_keepout_layers":["F.Cu","B.Cu"],
    "routed_tracks":len(tracks),"routed_vias":len(vias),"copper_item_count":len(copper_items),
    "track_statistics":track_statistics(tracks),"power_routing":power_routing,
    "ground_track_statistics":track_statistics([t for t in tracks if t.GetNetname().lstrip('/')=='GND']),
    "ground_zones":ground_zones,"ground_corridor_review":ground_corridors,"top_washer_keepouts":washer_keepouts,
    "routing_check_scope":"Native zero-unconnected/DRC/parity plus planned-width trunk presence; narrow branches and pad neckdowns require load-path review, not a blanket minimum-width assertion.",
    "erc_violations":len(ev),"schematic_parity_issues":len(drc["schematic_parity"]),
    "q1_mount":{"orientation":"horizontal, tab down", "body_max_mm":[10.67,16.51,4.83], "fitted_height_budget_mm":6.5, "under_body_support_mm":1, "live_tab_copper_keepout_checked":True, "physical_forming_and_thermal_checks":"required"},
    "bom_revision":selection["revision"],"bom_reference_checks":len(parts),
    "buzzer_drive":"GPIO14 through R6 330 ohm to passive BZ1; Q3/R7/R19 removed; 4 kHz firmware tone",
    "simplifications":{"removed_references":sorted(removed),"source_oring_diode":"not fitted; K1 selects one positive input at a time","adc_module_requirements":["local supply bypassing","SDA pull-up to VDD","SCL pull-up to VDD"],"probe_bias_resistors":"10 kohm 1%; per-channel calibration required"},
    "power_source_selector":{"part":"G5Q-1 DC12 + SB140 coil flyback","nc_rating_a":3,"no_rating_a":5,"coil_w":0.4,"PD":"K1 de-energized: pins 2-4","WALL":"K1 energized: pins 2-3","transition":"open contact interval; controller may restart","jack_switch":"J9 pins 2-3 normally closed; pin 3 unused","state_checks":source_states,"barrel":"regulated 12 V, 5.5 x 2.1 mm, center positive","limitations":"Topology only; verify contact inrush, brownout, release delay and loaded transfer physically"},
    "converter":{"manufacturer":"Traco Power","part":"TSR 2-2450N","input_v":[6.5,36],"output_v":5,"output_a":2,"body_mm":[14,7.6,10.2],"pinout":{"1":"VIN","2":"GND","3":"VOUT"}},
    "converter_pin_coordinates_mm":{n:[round(pcb.ToMM(p.GetPosition().x)-100,4),round(pcb.ToMM(p.GetPosition().y)-50,4)] for n,p in u2pads.items()},
    "fuses":0,"power_protection_assumption":"Use only protected/current-limited regulated 12 V sources rated no more than 3 A; no branch-selective overcurrent protection is fitted.",
    "output_contact_limit":{"connector":"J2 RJHSE5080","rating_a_per_contact":1.5,"shared_return_pin":4,"shared_return_load":"blower + servo; validate combined current and cable/contact heating"},
    "drc_violations_by_type":dict(dc),"unconnected_items":len(drc["unconnected_items"]),
    "mount_pattern_mm":[51,58],"carrier_clearance_holes_mm":3.2, "mechanical_revision":"carrier-enclosure-r6", "connector_edges":"power +Y short end: RJ45/barrel flush, USB-C flush with floor of 2 mm exterior recess; probes -Y short end",
    "interpretation":"Measured routing and native checks pass; physical load, temperature, source transfer and fit qualification remain. Copper width reports are not current-capacity certification."}
(reports/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
md="# Actual routed verification\n\n**Routed engineering prototype; physical qualification remains.**\n\n"
md+=f"- Logical schematic checks: {checks} pin/net pairs agree with the design description.\n"
md+=f"- PCB: {len(expected)} electrical footprints agree with those logical net assignments.\n"
md+="- J8: 10-pin socket for the user-linked blue module; physical fit not yet verified.\n"
md+="- U2: Traco TSR 2-2450N fixed 5 V / 2 A SIP-3; pinout, body envelope and coordinates checked independently.\n"
md+="- Q1: horizontal TO-220 body, G/D/S lead row, 1.4 mm drills and F.Cu live-tab keepout checked. 6.5 mm fitted envelope includes 1 mm insulating support; forming and thermal sample checks remain.\n"
md+="- K1 automatically selects wall power when energized, USB-PD otherwise. JP2 is removed. Eighteen jack/relay/source cases checked for source shorts and simultaneous input paths. Transfer timing, inrush and brownout require physical validation.\n"
md+="- Simplification: D1, C5, C7, C13, R17 and R18 are absent by assertion, along with the previously removed F1-F4/Q3/R7/R19.\n"
md+="- Protection: use only protected/current-limited regulated 12 V sources rated no more than 3 A; there is no onboard or branch-selective overcurrent protection.\n"
md+="- ADC module release gate: confirm local supply bypassing and SDA/SCL pull-ups to VDD before assembly.\n"
md+="- BZ1: direct GPIO14 drive through R6 330 ohm; Q3, R7 and R19 are absent by assertion. Test 4 kHz audibility in the enclosure.\n"
md+="- Adafruit 5807 HUSB238: official 20.32 x 23.495 mm PCB outline and two-hole pattern applied.\n"
md+=f"- 5807 mounting: 2.4 mm NPTH holes at {holes()}; USB-C face is {92-usb_face()[1]:.3f} mm inside the carrier power edge.\n"
md+="- 5807 mounting: F.Cu/B.Cu track/via/pour keepout present; no electrical-component or carrier-hole courtyard intersects the reserved region.\n"
md+=f"- Native KiCad ERC: {len(ev)} violations. This does not verify module hardware or performance.\n"
md+=f"- Native PCB/schematic parity: {len(drc['schematic_parity'])} issues. BOM manufacturer and DigiKey identifiers agree for {len(parts)} references.\n"
md+=f"- Native KiCad DRC: {len(drc['violations'])} reported violations plus {len(drc['unconnected_items'])} unconnected items.\n"
md+=f"- Copper routing: {len(tracks)} track/arc segments, {len(vias)} vias, {track_statistics(tracks)['length_mm']:.3f} mm total segment length.\n"
md+="- Native DRC requires zero unconnected items. Planned power-trunk widths are present; narrower pad escapes and low-current branches are reported individually in summary.json for review.\n"
md+="- Four F.Cu top-washer keepouts cover Ø7.4 mm; circular NPTH exemptions stay within 1.7 mm radius. Underside boss exemptions are checked against the same limit.\n"
md+="- J2: 1.5 A/contact. Pin 4 carries combined blower and servo return; validate actual load, cable drop and contact heating.\n"
md+="- Four 3.2 mm NPTH M3 carrier mounts, 51 x 58 mm pattern; independently fastened to the bottom. WT32 mounts separately to the top via its retainer.\n\n"
md+="| Power net | Tracks | Total length, mm | Width: length, mm |\n|---|---:|---:|---|\n"
for net,s in power_routing.items():
    widths=", ".join(f"{w['width_mm']:g}: {w['length_mm']:.3f}" for w in s["widths"])
    md+=f"| {net} | {s['track_count']} | {s['length_mm']:.3f} | {widths} |\n"
md+="\nGround zones are measured from actual saved fills:\n\n"
for zone in ground_zones:
    for layer in zone['layers']:
        md+=f"- {zone['name'] or 'Unnamed GND zone'} / {layer['layer']}: {layer['filled_regions']} filled regions, {layer['filled_area_mm2']:.3f} mm².\n"
md+="- Ground geometry: J1/J9/U2/C1/C3/D2 remain connected through regions surviving the 2 mm corridor check, joining layers at power-section PTH pads or GND vias. J2's combined blower/servo return also reaches that network at 1.2 mm corridor width. ADC/DEBUG pads are excluded as power-return layer bridges. A 0.01 mm width allowance avoids collapsing exactly nominal-width tracks to zero-area lines; short pad landings are allowed within the erosion distance + 0.05 mm. This checks geometry, not copper temperature, current sharing, PTH/via resistance or voltage drop.\n"
md+=f"\nPCB SHA-256: `{report['pcb_sha256']}`.\n\nNormalized native schematic pin-map SHA-256: `{report['schematic_pin_map_sha256']}`.\n"
if dc:
    md+="| DRC category | Count |\n|---|---:|\n"+"".join(f"| {t} | {n} |\n" for t,n in sorted(dc.items()))
md+="\nReports are retained without exclusions. Resolve actual violations and all README\nrelease gates before ordering. No electrical load, temperature, antenna, or physical\nfit test has been performed.\n"
(reports/"README.md").write_text(md)
print(json.dumps(report,indent=2))
