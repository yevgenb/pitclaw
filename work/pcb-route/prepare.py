from pathlib import Path
import json, math
import pcbnew as p
R=Path('hardware/carrier-revb'); W=Path('work/pcb-route')
assert not p.LoadBoard(str(R/'pitclaw-carrier.kicad_pcb')).GetTracks(), 'Routed board exists'
board=p.LoadBoard(str(W/'original/pitclaw-carrier.kicad_pcb'))
assert not board.GetTracks(), 'Refuse to overwrite routing'
fp={f.GetReference():f for f in board.GetFootprints()}
def pt(x,y): return p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+50))
for ref,x,y,a in [('C2',15,65,0),('C4',30.5,70,270)]:
    fp[ref].SetOrientationDegrees(a);fp[ref].SetPosition(pt(x,y))
for i,(x,y) in enumerate([(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)],1):
    z=p.ZONE(board);z.SetIsRuleArea(True);z.SetZoneName('CARRIER_TOP_WASHER_'+str(i))
    ls=p.LSET();ls.AddLayer(p.F_Cu);z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowFootprints(False)
    o=z.Outline();o.NewOutline()
    # Circumscribed 32-gon gives at least 3.7 mm radial protection.
    for n in range(32):
        a=n*2*math.pi/32;v=pt(x+3.7/math.cos(math.pi/32)*math.cos(a),y+3.7/math.cos(math.pi/32)*math.sin(a));o.Append(v.x,v.y)
    h=o.NewHole(0)
    for dx,dy in [(-1.65,-1.65),(-1.65,1.65),(1.65,1.65),(1.65,-1.65)]:
        v=pt(x+dx,y+dy);o.Append(v.x,v.y,0,h)
    board.Add(z)
proj=json.loads((R/'pitclaw-carrier.kicad_pro').read_text())
default=proj['net_settings']['classes'][0]
classes=[default]
assign={'Power12':['/+12V','/PD_12V','/WALL_12V','/FAN_OUT'], 'Power5':['/+5V','/+5V_WT32']}
for name,width in [('Power12',2.0),('Power5',1.2)]:
    classes.append(dict(default,name=name,track_width=width,via_diameter=1.2,via_drill=.6))
proj['net_settings']['classes']=classes
proj['net_settings']['netclass_patterns']=[{'netclass':k,'pattern':n} for k,ns in assign.items() for n in ns]
(R/'pitclaw-carrier.kicad_pro').write_text(json.dumps(proj,indent=2)+'\n')
ns=board.GetDesignSettings().m_NetSettings
for c in classes:
    nc=p.NETCLASS(c['name']);nc.SetClearance(p.FromMM(c['clearance']));nc.SetTrackWidth(p.FromMM(c['track_width']));nc.SetViaDiameter(p.FromMM(c['via_diameter']));nc.SetViaDrill(p.FromMM(c['via_drill']))
    if c['name']=='Default': ns.SetDefaultNetclass(nc)
    else: ns.SetNetclass(c['name'],nc)
for k,names in assign.items():
    for n in names:ns.SetNetclassPatternAssignment(n,k)
ns.RecomputeEffectiveNetclasses()
for n,net in board.GetNetsByName().items():
    if n:net.SetNetClass(ns.GetEffectiveNetClass(n))
p.SaveBoard(str(R/'pitclaw-carrier.kicad_pcb'),board)
p.SaveBoard(str(W/'prepared.kicad_pcb'),board)
print('DSN export',p.ExportSpecctraDSN(board,str(W/'carrier.dsn')))
