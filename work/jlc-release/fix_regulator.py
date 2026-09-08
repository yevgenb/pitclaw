from pathlib import Path
import pcbnew as pcb

root=Path(__file__).resolve().parents[2]/'hardware/carrier-revb'
vec=lambda x,y: pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
board=pcb.LoadBoard(str(root/'pitclaw-carrier.kicad_pcb'))
fps={f.GetReference():f for f in board.GetFootprints()}
desc='Traco TSR 2N manufacturer outline: 14x7.6x10.2mm SIP-3, 2.54mm pitch. Pin 1 VIN, 2 GND, 3 VOUT. Offset pin row; 1.4mm drills clear tolerated square pins.'

def correct(f):
    origin=f.GetPosition()
    for g in f.GraphicalItems():
        if not isinstance(g,pcb.PCB_SHAPE): continue
        layer=g.GetLayer()
        if layer not in (pcb.F_Fab,pcb.F_SilkS,pcb.F_CrtYd): continue
        old=(-4.96,-4.3,10.04,4.3) if layer==pcb.F_CrtYd else (-4.46,-3.8,9.54,3.8)
        new=(-5.21,-2.19,10.29,6.91) if layer==pcb.F_CrtYd else (-4.46,-1.44,9.54,6.16)
        for getter,setter in [(g.GetStart,g.SetStart),(g.GetEnd,g.SetEnd)]:
            p=getter()-origin
            x,y=pcb.ToMM(p.x),pcb.ToMM(p.y)
            assert min(abs(x-old[0]),abs(x-old[2]))<1e-5
            assert min(abs(y-old[1]),abs(y-old[3]))<1e-5
            setter(origin+vec(new[0] if abs(x-old[0])<1e-5 else new[2],new[1] if abs(y-old[1])<1e-5 else new[3]))
    for p in f.Pads():
        p.SetDrillSize(vec(1.4,1.4));p.SetSize(vec(2,2))
    f.SetLibDescription(desc)

u2=fps['U2']
assert u2.GetPosition()==vec(117,121.5)
old_pads=[p.GetPosition() for p in u2.Pads()]
correct(u2)
u2.SetPosition(vec(117,120.75))
for t in board.GetTracks():
    if isinstance(t,pcb.PCB_VIA): continue
    for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
        p=getter()
        if any(p==q for q in old_pads): setter(p+vec(0,-.75))
for p in fps['J8'].Pads():p.SetDrillSize(vec(1.05,1.05))

# Keep custom library manufacturing geometry aligned with the native board.
for path in (root/'PitClaw.pretty').glob('*.kicad_mod'):
    f=pcb.FootprintLoad(str(path.parent),path.stem)
    if path.stem=='TRACO_TSR_2N_SIP3': correct(f)
    if path.stem=='ADS1115_Blue_1x10_DRAFT':
        for p in f.Pads():p.SetDrillSize(vec(1.05,1.05))
    f.Reference().SetTextSize(vec(1,1));f.Reference().SetTextThickness(pcb.FromMM(.15))
    for g in f.GraphicalItems():
        if g.GetLayer() in (pcb.F_SilkS,pcb.B_SilkS) and isinstance(g,pcb.PCB_SHAPE):
            g.SetWidth(max(g.GetWidth(),pcb.FromMM(.15)))
    pcb.FootprintSave(str(path.parent),f)
pcb.ZONE_FILLER(board).Fill(board.Zones())
pcb.SaveBoard(str(root/'pitclaw-carrier.kicad_pcb'),board)
print('Updated U2 geometry/placement, J8 holes, and local library legend rules.')
