#!/usr/bin/env python3
"""Check actual exported guide sections at the face and inside the case."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def crossings(section,axis,value,result_axis):
    hits=[]
    for loop in section:
        for a,b in zip(loop[:-1],loop[1:]):
            delta=b[axis]-a[axis]
            if abs(delta)<1e-9:
                continue
            t=(value-a[axis])/delta
            if -1e-8<=t<=1+1e-8:
                hits.append(float(a[result_axis]+t*(b[result_axis]-a[result_axis])))
    unique=[]
    for value in sorted(hits):
        if not unique or abs(value-unique[-1])>1e-5:
            unique.append(value)
    return unique

def near(a,b,tolerance=.001):
    if abs(a-b)>tolerance:
        raise ValueError(f"Actual guide dimension {a:.6f} differs from {b:.6f} mm")

def main():
    files=['carrier-case.scad','carrier-bottom.stl','probe-fascia.stl']
    report={'status':'RUNNING','sources_sha256':{n:digest(ROOT/n) for n in files},
            'verifier_sha256':digest(Path(__file__)),
            'scope':'Sections through exported solids, independent of the CAD profile declarations.',
            'section_y_mm':[-51.8,-47],'sections':[]}
    try:
        bottom=trimesh.load(ROOT/'carrier-bottom.stl',force='mesh')
        fascia=trimesh.load(ROOT/'probe-fascia.stl',force='mesh')
        fascia.apply_transform(np.array([[1,0,0,0],[0,0,1,-52],[0,-1,0,0],[0,0,0,1]],float))
        for y in report['section_y_mm']:
            f=trimesh.intersections.mesh_plane(fascia,plane_origin=[0,y,0],plane_normal=[0,1,0])
            b=trimesh.intersections.mesh_plane(bottom,plane_origin=[0,y,0],plane_normal=[0,1,0])
            if len(f)==0 or len(b)==0:
                raise ValueError('Missing actual solid section')
            rows=[]
            for sign in [-1,1]:
                for absolute_x in [33.5,34,35,35.8]:
                    x=sign*absolute_x
                    fz=crossings(f,0,x,2);bz=crossings(b,0,x,2)
                    male_bottom=min(fz);male_top=max(fz)
                    cavity_floor=min(bz,key=lambda z:abs(z-3.8))
                    cavity_roof=min(z for z in bz if z>cavity_floor+.01)
                    near(male_bottom,3.8);near(cavity_floor,3.8)
                    near(male_top,41.8-absolute_x);near(cavity_roof,42.3-absolute_x)
                    vertical_gap=cavity_roof-male_top
                    near(vertical_gap,.5)
                    rows.append({'x_mm':x,'male_bottom_z_mm':male_bottom,
                        'male_top_z_mm':male_top,'cavity_floor_z_mm':cavity_floor,
                        'cavity_roof_z_mm':cavity_roof,'vertical_roof_gap_mm':vertical_gap,
                        'normal_roof_gap_mm':vertical_gap/math.sqrt(2)})
            side_gaps=[]
            for sign in [-1,1]:
                fx=sorted(sign*x for x in crossings(f,2,4.5,0) if sign*x>33.3)
                bx=sorted(sign*x for x in crossings(b,2,4.5,0) if sign*x>33.3)
                male_edge=fx[0];cavity_edge=bx[0]
                near(male_edge,36);near(cavity_edge,36.4)
                near(cavity_edge-male_edge,.4)
                side_gaps.append(cavity_edge-male_edge)
            report['sections'].append({'y_mm':y,'profile_samples':rows,
                                      'left_right_side_gap_mm':side_gaps})
        variations=[]
        for a,b in zip(report['sections'][0]['profile_samples'],report['sections'][1]['profile_samples']):
            for key in ['male_bottom_z_mm','male_top_z_mm','cavity_floor_z_mm','cavity_roof_z_mm']:
                variations.append(abs(a[key]-b[key]))
        maximum=max(variations)
        near(maximum,0)
        report['maximum_front_to_inner_profile_variation_mm']=maximum
        report['sources_unchanged']=report['sources_sha256']=={n:digest(ROOT/n) for n in files}
        if not report['sources_unchanged']:
            raise ValueError('An input changed during section verification')
        report['status']='PASS: matching front and inner guide profiles'
    except Exception as error:
        report['status']='FAIL';report['error']=str(error)
    (ROOT/'guide-section-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],report.get('error',''))
    if report['status'].startswith('PASS'):
        print('Front/inner maximum variation:',report['maximum_front_to_inner_profile_variation_mm'],'mm')
        print('Side gap:0.4 mm; roof gap:0.5 mm vertical /',.5/math.sqrt(2),'mm normal')
    return 0 if report['status'].startswith('PASS') else 1

if __name__=='__main__':
    raise SystemExit(main())
