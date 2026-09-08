import pcbnew as p,json
from pathlib import Path
b=p.LoadBoard('hardware/carrier-revb/pitclaw-carrier.kicad_pcb')
v=lambda x,y:p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+50))
xy=lambda v:[p.ToMM(v.x)-100,p.ToMM(v.y)-50]
fps={f.GetReference():f for f in b.GetFootprints()}
landings={f'{r}:{n}':next(t for t in fps[r].Pads() if t.GetNumber()==n) for r,n in [('J1','2'),('J9','2'),('U2','2'),('C2','2'),('C4','2')]}
regions={};scene={};obstacles={}
for layer in [p.F_Cu,p.B_Cu]:
 copper=p.SHAPE_POLY_SET();obs=[]
 for z in b.Zones():
  if not z.GetLayerSet().Contains(layer):continue
  if not z.GetIsRuleArea() and z.GetNetname()=='/GND':copper.BooleanAdd(z.GetFilledPolysList(layer))
  elif z.GetIsRuleArea() and z.GetDoNotAllowVias():obs.append(z.Outline())
 for f in fps.values():
  for pad in f.Pads():
   if not pad.GetLayerSet().Contains(layer):continue
   shape=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(shape,layer,0,p.FromMM(.001),p.ERROR_INSIDE)
   if pad.GetNetname()=='/GND':copper.BooleanAdd(shape)
   else:obs.append(pad.GetEffectiveShape(layer))
 for t in b.GetTracks():
  if not t.GetLayerSet().Contains(layer):continue
  shape=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(shape,layer,0,p.FromMM(.001),p.ERROR_INSIDE)
  if t.GetNetname()=='/GND':copper.BooleanAdd(shape)
  else:obs.append(t.GetEffectiveShape(layer))
 copper.Simplify();copper.Deflate(p.FromMM(.995),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.001))
 regs=[];polys=[]
 for i in range(copper.OutlineCount()):
  poly=copper.UnitSet(i);names=[n for n,t in landings.items() if poly.Collide(t.GetEffectiveShape(layer),p.FromMM(1.045))]
  regs.append((names,poly))
  o=poly.COutline(0);holes=[]
  for j in range(poly.HoleCount(0)):
   h=poly.CHole(0,j);holes.append([xy(h.CPoint(k)) for k in range(h.PointCount())])
  polys.append(dict(names=names,points=[xy(o.CPoint(j)) for j in range(o.PointCount())],holes=holes))
 regions[layer]=regs;obstacles[layer]=obs;scene[b.GetLayerName(layer)]=polys

candidates=[]
for x0 in range(20,68):
 for y0 in range(110,166):
  x,y=x0/2,y0/2
  shape=p.SHAPE_CIRCLE(v(x,y),p.FromMM(.6))
  if any(p.SHAPE.Collide(shape,o,p.FromMM(.301)) for obs in obstacles.values() for o in obs):continue
  names={layer:sorted({n for ns,poly in regs if poly.Collide(shape,p.FromMM(1.045)) for n in ns}) for layer,regs in regions.items()}
  union=set(sum(list(names.values()),[]))
  if len(union)>=2 and (('J1:2' in union and ('U2:2' in union or 'J9:2' in union)) or ('U2:2' in union and 'J9:2' in union)):
   candidates.append([x,y,{b.GetLayerName(k):v for k,v in names.items()}])
Path('work/jlc-release/ground-regions.json').write_text(json.dumps(scene))
print(json.dumps(candidates,indent=1))
