#!/usr/bin/env python3
"""Measure exported coupon running gaps, ramps and separated support lands."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b,t=.001):
    if abs(a-b)>t:raise ValueError(f'{a:.6f}mm differs from expected {b:.6f}mm')
def crossings(segments,axis,value,result_axis):
    result=[]
    for a,b in segments:
        delta=b[axis]-a[axis]
        if abs(delta)<1e-9:continue
        t=(value-a[axis])/delta
        if -1e-8<=t<=1+1e-8:result.append(float(a[result_axis]+t*(b[result_axis]-a[result_axis])))
    unique=[]
    for x in sorted(result):
        if not unique or abs(x-unique[-1])>1e-5:unique.append(x)
    return unique

def main():
    files=['bottom.stl','fascia.stl','sources/candidate.scad']
    report={'status':'RUNNING','sources_sha256':{n:sha(ROOT/n) for n in files},
        'verifier_sha256':sha(Path(__file__)),'scope':'Actual exported coupon sections; full-model nominal geometry is checked separately.','sections':[]}
    try:
        bottom=trimesh.load(ROOT/'bottom.stl',force='mesh');bottom.apply_translation([26.5,-37,0])
        fascia=trimesh.load(ROOT/'fascia.stl',force='mesh')
        fascia.apply_transform([[1,0,0,23],[0,0,1,-52],[0,-1,0,13.7],[0,0,0,1]])
        for label,y,expected_floor in [('front relief',-51.5,3.5),('front ramp',-50.3,3.65),('front land',-49.6,3.8),('falling ramp',-48.9,3.65),('middle relief',-47,3.5),('rear ramp',-44.3,3.65),('rear land',-43.5,3.8)]:
            b=trimesh.intersections.mesh_plane(bottom,[0,1,0],[0,y,0]);f=trimesh.intersections.mesh_plane(fascia,[0,1,0],[0,y,0])
            rows=[]
            for x in [33.5,34,35,35.8]:
                bz=crossings(b,0,x,2);fz=crossings(f,0,x,2)
                male_bottom=min(fz);male_top=max(fz)
                floor=min(bz,key=lambda z:abs(z-expected_floor))
                roof=min(z for z in bz if z>4)
                near(male_bottom,3.8);near(male_top,41.8-x);near(floor,expected_floor)
                normal=(roof-male_top)/math.sqrt(2);near(normal,.4)
                rows.append({'x_mm':x,'runner_bottom_z_mm':male_bottom,'receiver_floor_z_mm':floor,'lower_gap_mm':male_bottom-floor,'roof_normal_gap_mm':normal})
            male_edge=min(x for x in crossings(f,2,4.5,0) if x>33.3)
            wall=min(x for x in crossings(b,2,4.5,0) if x>33.3)
            near(male_edge,36);near(wall,36.2);near(wall-male_edge,.2)
            report['sections'].append({'label':label,'y_mm':y,'samples':rows,'side_gap_mm':wall-male_edge})
        if report['sources_sha256']!={n:sha(ROOT/n) for n in files}:raise ValueError('Input changed during measurement')
        report['status']='PASS: measured running gaps and two support lands'
    except Exception as error:report['status']='FAIL';report['error']=str(error)
    (ROOT/'running-clearance-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],report.get('error',''))
    for row in report['sections']:print(row['label'],row['y_mm'],'floor',row['samples'][0]['receiver_floor_z_mm'],'lower gap',row['samples'][0]['lower_gap_mm'])
    return 0 if report['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
