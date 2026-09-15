#!/usr/bin/env python3
"""Render actual native Fusion guide sections to guide-clearance.svg/png.
Requires numpy/trimesh; PNG conversion additionally requires Node and sharp.
"""
from pathlib import Path
import argparse,hashlib,html,math,shutil,subprocess
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
BOTTOM=HERE/'native-stl/carrier-bottom.stl'
FASCIA=HERE/'native-stl/probe-fascia.stl'
BLUE='#7893ad';ORANGE='#efb16c';INK='#243647';DIM='#0d6875'

def plane(mesh,axis,value):
    normal=np.zeros(3);normal[axis]=1
    origin=np.zeros(3);origin[axis]=value
    return trimesh.intersections.mesh_plane(mesh,normal,origin)

def crossing(lines,axis,value,result):
    out=[]
    for a,b in lines:
        delta=b[axis]-a[axis]
        if abs(delta)<1e-10:continue
        t=(value-a[axis])/delta
        if -1e-8<=t<=1+1e-8:out.append(float(a[result]+t*(b[result]-a[result])))
    unique=[]
    for x in sorted(out):
        if not unique or abs(x-unique[-1])>1e-5:unique.append(x)
    return unique

def loops(lines):
    # Stitch actual triangle-plane edges; no CAD outlines are substituted.
    vertices={};edges=set();adj={}
    for a,b in lines:
        ka=tuple(np.round(a,5));kb=tuple(np.round(b,5))
        if ka==kb:continue
        vertices[ka]=a;vertices[kb]=b
        edge=tuple(sorted([ka,kb]))
        if edge in edges:continue
        edges.add(edge);adj.setdefault(ka,[]).append(kb);adj.setdefault(kb,[]).append(ka)
    if any(len(v)!=2 for v in adj.values()):raise RuntimeError('Native section did not form closed contours')
    result=[]
    while edges:
        start,nxt=next(iter(edges));path=[start];prev=None;cur=start
        while True:
            options=[n for n in adj[cur] if tuple(sorted([cur,n])) in edges]
            if not options:break
            n=options[0];edges.remove(tuple(sorted([cur,n])));cur=n;path.append(cur)
            if cur==start:break
        if path[-1]!=start:raise RuntimeError('Open native section contour')
        result.append([vertices[k] for k in path])
    return result

class SVG:
    def __init__(self):
        self.items=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1220" viewBox="0 0 1400 1220">',
                    '<defs><marker id="dim" markerWidth="5" markerHeight="5" refX="2.5" refY="2.5" orient="auto-start-reverse"><path d="M5,0 L0,2.5 L5,5" fill="none" stroke="'+DIM+'" stroke-width="1"/></marker></defs>',
                    '<rect width="1400" height="1220" fill="#f7f9fb"/>']
    def add(self,s):self.items.append(s)
    def text(self,x,y,s,size=18,weight='normal',anchor='start',color=INK):
        self.add(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(s)}</text>')
    def line(self,a,b,color=INK,width=1,dash=None):
        extra=f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<path d="M{a[0]:.4f},{a[1]:.4f} L{b[0]:.4f},{b[1]:.4f}" fill="none" stroke="{color}" stroke-width="{width}"{extra}/>')
    def dim(self,a,b):
        self.add(f'<path d="M{a[0]:.4f},{a[1]:.4f} L{b[0]:.4f},{b[1]:.4f}" fill="none" stroke="{DIM}" stroke-width="1.8" marker-start="url(#dim)" marker-end="url(#dim)"/>')
    def badge(self,x,y,label):
        self.add(f'<circle cx="{x}" cy="{y}" r="12" fill="white" stroke="{DIM}" stroke-width="1.6"/>');self.text(x,y+5,label,14,'bold','middle',DIM)
    def contours(self,paths,mapping,fill):
        d=[]
        for p in paths:
            xy=[mapping(q) for q in p]
            d.append('M'+' L'.join(f'{x:.5f},{y:.5f}' for x,y in xy)+' Z')
        self.add(f'<path d="{" ".join(d)}" fill="{fill}" fill-rule="evenodd" stroke="{INK}" stroke-width="1.3" stroke-linejoin="round"/>')

def assert_near(a,b,tol=.003):
    if abs(a-b)>tol:raise RuntimeError(f'Native dimension {a} does not match {b}')

def section_panel(svg,bottom,fascia,y,left,title,below):
    bx=plane(bottom,1,y);fx=plane(fascia,1,y)
    x0=left+25;top=165;scale=42
    xy=lambda q:(x0+(q[0]-31)*scale,top+(11.5-q[2])*scale)
    svg.text(left+25,130,title,25,'bold')
    ident='clip'+str(left)
    svg.add(f'<defs><clipPath id="{ident}"><rect x="{x0}" y="{top}" width="525" height="483"/></clipPath></defs>')
    svg.add(f'<rect x="{x0}" y="{top}" width="525" height="483" fill="white" stroke="#cbd5df"/>')
    for x in [32,34,36,38,40,42]:
        a=xy([x,0,0]);b=xy([x,0,11.5]);svg.line(a,b,'#e6ebef');svg.text(a[0],a[1]+25,str(x),15,anchor='middle')
    for z in [0,2,4,6,8,10]:
        a=xy([31,0,z]);b=xy([43.5,0,z]);svg.line(a,b,'#e6ebef');svg.text(a[0]-10,a[1]+5,str(z),15,anchor='end')
    svg.add(f'<g clip-path="url(#{ident})">');svg.contours(loops(bx),xy,BLUE);svg.contours(loops(fx),xy,ORANGE);svg.add('</g>')
    svg.text(x0+525,top+515,'X (mm)',15,anchor='end');svg.text(x0-7,top-13,'Z (mm)',15)
    # Exact measured sloping faces and their normal separation.
    x=34.8;male=max(crossing(fx,0,x,2));r0=min(z for z in crossing(bx,0,x,2) if z>4)
    x1=35.2;r1=min(z for z in crossing(bx,0,x1,2) if z>4)
    slope=(r1-r0)/(x1-x);normal=np.array([-slope,0,1])/math.sqrt(1+slope*slope)
    gap=(r0-male)/math.sqrt(1+slope*slope);assert_near(gap,.4)
    a=np.array([x,y,male]);b=a+normal*gap;svg.dim(xy(a),xy(b));point=xy((a+b)/2);label=(point[0]-35,point[1]-37);svg.line(point,label,DIM,1);svg.badge(*label,'1')
    me=min(v for v in crossing(fx,2,4.7,0) if v>33.3);ce=min(v for v in crossing(bx,2,4.7,0) if v>33.3);assert_near(ce-me,.3)
    a=xy([me,y,4.7]);b=xy([ce,y,4.7]);svg.dim(a,b);label=(b[0]+36,b[1]+5);svg.line(((a[0]+b[0])/2,a[1]),label,DIM);svg.badge(*label,'2')
    x=35.1;floor=min(crossing(bx,0,x,2),key=lambda z:abs(z-(3.8-below)));foot=min(crossing(fx,0,x,2));assert_near(foot-floor,below)
    a=xy([x,y,floor]);b=xy([x,y,foot]);label=(a[0]-44,a[1]+31)
    if below:svg.dim(a,b)
    else:svg.add(f'<circle cx="{a[0]}" cy="{a[1]}" r="3.2" fill="{DIM}"/>')
    svg.line(((a[0]+b[0])/2,(a[1]+b[1])/2),label,DIM);svg.badge(*label,'3')
    row=714
    for yy,num,text in [(row,'1','Roof: 0.40 mm normal'),(row+31,'2','Side: 0.30 mm'),(row+62,'3',f'Below: {below:.2f} mm' if below else 'Bearing contact: 0.00 mm')]:
        svg.badge(left+40,yy-5,num);svg.text(left+61,yy,text,19)

def longitudinal(svg,bottom,fascia):
    bx=plane(bottom,0,35);fx=plane(fascia,0,35)
    left=80;top=885;width=1240;height=210
    # Vertically enlarged section makes the measured0.3mm gap readable.
    mapping=lambda q:(left+(q[1]+52.1)/9.1*width,top+(4.05-q[2])/.85*height)
    svg.text(65,833,'Two support lands keep the fascia at its original height',27,'bold')
    svg.text(65,862,'YZ section at X = 35 mm  ·  vertical scale enlarged',18)
    svg.add(f'<defs><clipPath id="longitudinal"><rect x="{left}" y="{top}" width="{width}" height="{height}"/></clipPath></defs>')
    svg.add(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="white" stroke="#cbd5df"/>')
    svg.add('<g clip-path="url(#longitudinal)">');svg.contours(loops(bx),mapping,BLUE);svg.contours(loops(fx),mapping,ORANGE);svg.add('</g>')
    for y in [-52,-50,-48,-46,-44,-43]:
        px=mapping([35,y,3.2])[0];svg.text(px,1120,str(y),16,anchor='middle')
    svg.text(1320,1144,'Y (mm), toward the inside →',16,anchor='end')
    for y,label in [(-49.6,'Front bearing land'),(-43.5,'Rear bearing land')]:
        floor=min(crossing(bx,1,y,2),key=lambda z:abs(z-3.8));foot=min(crossing(fx,1,y,2));assert_near(floor,3.8);assert_near(foot,floor)
        a=mapping([35,y,floor]);svg.add(f'<circle cx="{a[0]}" cy="{a[1]}" r="3.3" fill="{DIM}"/>');svg.line(a,(a[0],a[1]-38),DIM,1.5);svg.text(a[0],a[1]-48,label,17,'bold','middle',INK)
    y=-46.7;floor=min(crossing(bx,1,y,2),key=lambda z:abs(z-3.5));foot=min(crossing(fx,1,y,2));assert_near(foot-floor,.3)
    a=mapping([35,y,floor]);b=mapping([35,y,foot]);svg.dim(a,b);svg.text(a[0]+20,(a[1]+b[1])/2+7,'0.30 mm running clearance',20,'bold',color=DIM)
    svg.text(70,1180,'Actual native STL sections. Contact is shown only at the two measured Z = 3.8 mm lands.',17)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--svg-only',action='store_true');args=parser.parse_args()
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BOTTOM,FASCIA]}
    bottom=trimesh.load(BOTTOM,force='mesh');fascia=trimesh.load(FASCIA,force='mesh')
    svg=SVG();svg.text(40,49,'R13 guide clearance — actual Fusion geometry',32,'bold')
    svg.add(f'<rect x="43" y="73" width="22" height="16" rx="2" fill="{BLUE}" stroke="{INK}"/>');svg.text(74,88,'Bottom shell',18)
    svg.add(f'<rect x="248" y="73" width="22" height="16" rx="2" fill="{ORANGE}" stroke="{INK}"/>');svg.text(279,88,'Fascia',18)
    svg.text(1360,88,'Dimensions in millimeters',17,anchor='end')
    section_panel(svg,bottom,fascia,-47,40,'Running section · Y = −47',.3)
    section_panel(svg,bottom,fascia,-43.5,730,'Seating land · Y = −43.5',0)
    longitudinal(svg,bottom,fascia)
    svg.text(70,1207,'Native source hashes: bottom '+before[BOTTOM.name][:12]+' · fascia '+before[FASCIA.name][:12],13,color='#526170')
    svg.add('</svg>');output=HERE/'guide-clearance.svg';output.write_text('\n'.join(svg.items)+'\n')
    if not args.svg_only:
        node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
        sharp=HERE.parents[1]/'work/bom-build/node_modules/sharp'
        script="require(process.argv[1])(process.argv[2],{density:144}).resize(1400,1220).png().toFile(process.argv[3]).catch(e=>{console.error(e);process.exit(1)})"
        subprocess.run([node,'-e',script,str(sharp),str(output),str(HERE/'guide-clearance.png')],check=True)
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BOTTOM,FASCIA]}
    if before!=after:raise RuntimeError('Native source mesh changed during rendering')
    print('Rendered actual native sections:',output)

if __name__=='__main__':main()
