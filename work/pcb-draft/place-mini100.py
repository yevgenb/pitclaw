import pcbnew as p
import itertools, math
b=p.LoadBoard('hardware/carrier-revb/pitclaw-carrier.kicad_pcb')
fs={f.GetReference():f for f in b.GetFootprints()}
def box(f):
    f.BuildCourtyardCaches();v=f.GetCourtyard(p.F_Cu).BBox()
    return tuple(p.ToMM(k) for k in (v.GetX(),v.GetY(),v.GetRight(),v.GetBottom()))
def overlaps(a,b):
    return max(a[0],b[0])<min(a[2],b[2])+.05 and max(a[1],b[1])<min(a[3],b[3])+.05
fixed=[box(f) for r,f in fs.items() if r not in ('C3','C5')]
fixed.extend([(129.5,117,154.5,145)])
candidates={}
for r in ('C3','C5'):
    f=fs[r];pos=f.GetPosition();bb=box(f)
    offsets=[bb[0]-p.ToMM(pos.x),bb[1]-p.ToMM(pos.y),bb[2]-p.ToMM(pos.x),bb[3]-p.ToMM(pos.y)]
    out=[]
    for x,y in itertools.product([v/2 for v in range(3,116)],[v/2 for v in range(5,181)]):
        q=(100+x+offsets[0],50+y+offsets[1],100+x+offsets[2],50+y+offsets[3])
        if q[0]<100.5 or q[2]>159.5 or q[1]<50.5 or q[3]>141.5 or any(overlaps(q,v) for v in fixed):continue
        cost=(x-16)**2+(y-69)**2
        out.append((cost,x,y,q))
    candidates[r]=sorted(out)
    print(r,len(out),sorted(out)[:8])
solutions=[]
for a,c in itertools.product(candidates['C3'],candidates['C5']):
    if not overlaps(a[3],c[3]):solutions.append((a[0]+c[0],a[1:3],c[1:3]))
print('Best',sorted(solutions)[:8])
