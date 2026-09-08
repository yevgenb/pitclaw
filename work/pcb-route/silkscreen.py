import sys
import pcbnew as p
b=p.LoadBoard(sys.argv[1])
positions={'J4':(8.8,2),'J5':(25.8,2),'J6':(42.8,2),'J3':(21,8.9),'J7':(41,9),
 'C3':(55,9.2),'C1':(45.5,52.8),'Q1':(45.84,16.8),'Q2':(7.8,70.5),'U2':(19.5,68.8),
 'JP1':(55,21.4),'J1':(55.2,47.5),'J8':(24.4,30.9),'J9':(26.5,77.2),'J2':(9.5,80.5),
 'BZ1':(4.3,40),'K1':(34.15,54)}
for f in b.GetFootprints():
 if f.GetAttributes() & p.FP_BOARD_ONLY:continue
 ref=f.GetReference();xy=positions.get(ref)
 if xy is None:
  pads=[a for a in f.Pads() if a.GetNumber()]
  xy=(sum(p.ToMM(a.GetPosition().x)-100 for a in pads)/len(pads),sum(p.ToMM(a.GetPosition().y)-50 for a in pads)/len(pads))
 t=f.Reference();t.SetLayer(p.F_SilkS);t.SetVisible(True);t.SetKeepUpright(False)
 t.SetTextAngle(p.EDA_ANGLE(90 if ref in ['R1','R2','R4','R6','R14','R15','D3','C4'] else 0,p.DEGREES_T))
 t.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));t.SetTextThickness(p.FromMM(.12));t.SetPosition(p.VECTOR2I(p.FromMM(xy[0]+100),p.FromMM(xy[1]+50)))
for text,x,y in [('PD 12V',55,55.8),('3V3',41.25,16.2),('NOT ETHERNET',9.5,82),('WALL 12V',25.6,90.7)]:
 t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));t.SetTextThickness(p.FromMM(.12));t.SetPosition(p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+50)));b.Add(t)
p.SaveBoard(sys.argv[2],b)
