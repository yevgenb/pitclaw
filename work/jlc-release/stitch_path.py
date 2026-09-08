exec(open('work/jlc-release/find_ground_stitches.py').read().split('candidates=[]')[0])
from collections import deque,defaultdict
graph=defaultdict(set);locs=defaultdict(list);names=defaultdict(list)
for layer,regs in regions.items():
 for i,(ns,poly) in enumerate(regs):
  for name in ns:names[name].append((layer,i))
for ns in names.values():
 for a in ns:
  for z in ns:
   if a!=z:graph[a].add(z);locs[a,z].append('existing')
for x0 in range(4,117):
 for y0 in range(8,180):
  x,y=x0/2,y0/2
  if 12.04<x<27.04 and 68.81<y<77.41:continue
  shape=p.SHAPE_CIRCLE(v(x,y),p.FromMM(.6))
  if any(p.SHAPE.Collide(shape,o,p.FromMM(.301)) for obs in obstacles.values() for o in obs):continue
  hits={ly:[(ly,i) for i,(ns,poly) in enumerate(rr) if poly.Collide(v(x,y))] for ly,rr in regions.items()}
  for a in hits[p.F_Cu]:
   for z in hits[p.B_Cu]:graph[a].add(z);graph[z].add(a);locs[a,z].append((x,y));locs[z,a].append((x,y))
q=deque((a,[a]) for a in names['J1:2']);seen=set(names['J1:2'])
while q:
 node,path=q.popleft()
 if node in names['U2:2']:
  print('path',path)
  for a,z in zip(path,path[1:]):print(a,z,locs[a,z])
  break
 for z in graph[node]-seen:seen.add(z);q.append((z,path+[z]))
else:print('No path',len(seen))
