"""Local routing repair from the explicitly preserved post-footprint baseline."""
from pathlib import Path
import pcbnew as p

root=Path(__file__).resolve().parents[2]
path=root/'hardware/carrier-revb/pitclaw-carrier.kicad_pcb'
project=path.with_suffix('.kicad_pro')
project_bytes=project.read_bytes()
b=p.LoadBoard(str(root/'work/jlc-release/pre-local-u2-route.kicad_pcb'))
v=lambda x,y:p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+50))
remove_ids={
 # Old Q2-to-U2 thin ground chain crosses the corrected VIN landing.
 '1a2eebc4-0602-480b-b289-0cac5cccc0da',
 '57d4bf46-4a70-44c2-9b79-185728211cc9',
 'd88bc061-8b97-4121-a9ed-3af0493d4d85',
 'bb06cce4-2f35-4a16-aa5c-5912e4f9e369',
 '3d92e665-841a-483c-bcae-ed0131a16337',
 'cc54d3a3-5271-4fcc-95b3-175a7a80ff6d',
 'f55fd23a-7d44-4920-8519-f7dbecd47418',
 # Servo segment under the converter and its local approach to the jack.
 '8346e6d5-da7a-4889-b4e2-e99dbe0387ae',
 'f2a93dc6-ce0f-427e-929c-cb6ca6c48c5e',
 'b5ea3841-9b0e-44eb-a36e-e8fca8e68acc',
 'd6070665-13df-4b67-b0c1-69e15466b97d',
 # Keep the raw-wall feed at the converter edge, retaining the back return.
 '1dfd742e-9299-4f9c-b708-cdfe344197a3',
 '5ad3ede2-dd28-4472-9f17-e2933945fdb7',
}
found=set()
removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in remove_ids:
  found.add(t.m_Uuid.AsString());removed.append(t)
assert found==remove_ids,remove_ids-found

def route(net,layer,width,points):
 for a,z in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetLayer(layer)
  t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet(net));b.Add(t)

route('/WALL_12V',p.F_Cu,2.0,
      [(30.34,64.11),(26.5,67.95),(26.5,79.9)])
route('/SERVO_SIG',p.F_Cu,.3,
      [(23.4444,62.4284),(23.4444,66.5)])
route('/SERVO_SIG',p.B_Cu,.3,
      [(23.4444,66.5),(22.0444,67.9),(11,67.9),(11,71.6),
       (4,71.6),(2,73.6),(2,77),(3,78)])
route('/SERVO_SIG',p.F_Cu,.3,
      [(3,78),(5.6,80.6),(9,80.6)])
for x,y in [(23.4444,66.5),(3,78)]:
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.8));t.SetDrill(p.FromMM(.4))
 t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/SERVO_SIG'));b.Add(t)
for x,y in [(18,78.5),(20,78.5)]:
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(1.2));t.SetDrill(p.FromMM(.6))
 t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/GND'));b.Add(t)
# Direct regulator ground fanout opens into the front ground plane.
route('/GND',p.F_Cu,2.0,[(19.54,70.75),(19.54,75.8)])
route('/GND',p.B_Cu,.3,[(5.5,74),(5.5,75.8)])
fps={f.GetReference():f for f in b.GetFootprints()}
fps['J9'].Reference().SetPosition(v(26.5,89.5))
for t in removed:b.Remove(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(path),b)
# Saving a board loaded under another basename can create a default project;
# preserve the authoritative live design rules explicitly.
project.write_bytes(project_bytes)
print('Replaced',len(found),'local segments; total track/via items',len(b.GetTracks()))
