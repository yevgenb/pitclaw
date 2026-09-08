from pathlib import Path
import pcbnew as p
import math
R=Path('hardware/carrier-revb'); W=Path('work/pcb-route')
b=p.LoadBoard(str(W/'retry-base.kicad_pcb'))
assert p.ImportSpecctraSES(b,str(W/'retry.ses'))
for t in b.GetTracks():t.SetLocked(False)
# Correct the edge clearance of the manually retained bias-branch via.
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA) and t.GetPosition().x<p.FromMM(100.9):
        old=t.GetPosition();new=p.VECTOR2I(p.FromMM(100.95),old.y)
        for s in b.GetTracks():
            if isinstance(s,p.PCB_VIA):continue
            if s.GetStart()==old:s.SetStart(new)
            if s.GetEnd()==old:s.SetEnd(new)
        t.SetPosition(new)
# A round opening keeps all copper under metal hardware prohibited.
for z in b.Zones():
    if not z.GetZoneName().startswith(('CARRIER_TOP_WASHER_','CARRIER_BASE_BOSS_SWEEP_')):continue
    o=z.Outline();a=o.COutline(0)
    pts=[(a.CPoint(i).x,a.CPoint(i).y) for i in range(a.PointCount())]
    i=int(z.GetZoneName().rsplit('_',1)[1])-1;x,y=[(4.5,4.5),(55.5,4.5),(4.5,62.5),(55.5,62.5)][i]
    o.RemoveAllContours();o.NewOutline()
    for px,py in pts:o.Append(px,py)
    h=o.NewHole(0)
    for n in range(32):
        a=-n*2*math.pi/32;o.Append(p.FromMM(100+x+1.7*math.cos(a)),p.FromMM(50+y+1.7*math.sin(a)),0,h)
for layer,name in [(p.F_Cu,'GND_FRONT'),(p.B_Cu,'GND_BACK')]:
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/GND'));z.SetZoneName(name)
    z.SetLocalClearance(p.FromMM(.3));z.SetMinThickness(p.FromMM(.3));z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.6));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
    o=z.Outline();o.NewOutline()
    for x,y in [(100.5,50.5),(159.5,50.5),(159.5,141.5),(100.5,141.5)]:o.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
for t in b.GetDrawings():
    if hasattr(t,'GetText') and t.GetText()=='UNROUTED - NOT FOR FABRICATION':t.SetText('ROUTED PROTOTYPE / PHYSICAL VALIDATION REQUIRED')
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(R/'pitclaw-carrier.kicad_pcb'),b)
print('tracks including vias',len(b.GetTracks()))
