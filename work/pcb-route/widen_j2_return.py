import pcbnew as p
P='hardware/carrier-revb/pitclaw-carrier.kicad_pcb'
b=p.LoadBoard(P)
p.SaveBoard('work/pcb-route/before-j2-ground-fix.kicad_pcb',b)
def xy(v):return(p.ToMM(v.x)-100,p.ToMM(v.y)-50)
def v(x,y):return p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+50))
# Move only the final servo approach to the front above the fan trace.
remove=[]
for t in b.GetTracks():
 if t.GetNetname()=='/SERVO_SIG':
  if isinstance(t,p.PCB_VIA):
   x,y=xy(t.GetPosition())
   if abs(x-17.1868)<.01 and abs(y-79.01)<.01:remove.append(t)
  elif t.GetLayer()==p.B_Cu:
   a,z=xy(t.GetStart()),xy(t.GetEnd())
   if min(a[1],z[1])>=79:remove.append(t)
 if t.GetNetname()=='/GND' and not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu:
  a,z=xy(t.GetStart()),xy(t.GetEnd())
  if min(a[1],z[1])>=82.85 and max(a[0],z[0])<=26.51:remove.append(t)
def route(net,layer,width,points):
 for a,z in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet(net));b.Add(t)
route('/SERVO_SIG',p.B_Cu,.3,[(7.98,84.1),(7.98,83.0),(9,81.98),(9,80.6)])
# Use the exact surviving front-trace endpoint, avoiding a quantization gap.
end=next(xy(t.GetEnd()) if xy(t.GetEnd())[1]>78 else xy(t.GetStart()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/SERVO_SIG' and t.GetLayer()==p.F_Cu and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])>78)
route('/SERVO_SIG',p.F_Cu,.3,[(9,80.6),(end[0]-(80.6-end[1]),80.6),end])
via=p.PCB_VIA(b);via.SetPosition(v(9,80.6));via.SetWidth(p.FromMM(.8));via.SetDrill(p.FromMM(.4));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('/SERVO_SIG'));b.Add(via)
route('/GND',p.B_Cu,1.2,[(10.012,84.1),(10.012,82.5),(24.552,82.5),(26.5,84.448),(26.5,85.8)])
# Remove after creating new objects; deleted SWIG wrapper lifetimes are fragile.
for item in remove:b.Remove(item)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(P,b)
print('Replaced',len(remove),'segments/vias; final track/via count',len(b.GetTracks()))
