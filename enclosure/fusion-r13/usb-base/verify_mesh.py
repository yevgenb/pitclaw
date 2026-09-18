"""Measure the exported base: print orientation, seat heights, holes and solder windows."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import trimesh
OUT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(OUT))
from verify_running_clearance import crossings

def main():
    source=OUT/'native-stl/adafruit5807-base.stl'
    m=trimesh.load(source,force='mesh');m.apply_translation([14.5,-25.362,-9.1])
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1 and m.volume>0
    assert np.allclose(m.extents,[23.32,24.995,4.2],atol=.003)
    assert abs(m.bounds[0,2])<.001
    holes=[]
    for u in (2.413,17.653):
        x,y=10.16-u,20.955
        for z in (.4,1.5,2.8):
            seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);xs=crossings(seg,1,y,0)
            left=max(v for v in xs if v<x);right=min(v for v in xs if v>x)
            assert abs((right-left)-2.4)<.005
            holes.append({'uvz_mm':[u,y,z],'diameter_mm':right-left})
    seats=[]
    for u,v,expected in [(10.16,.55,3),(.4,10,3),(19.92,10,3),(4.213,20.955,3),(15.853,20.955,3),(10.16,10,.8)]:
        points,_,_=m.ray.intersects_location([[10.16-u,v,8]],[[0,0,-1]])
        height=float(max(points[:,2]));assert abs(height-expected)<.002,(u,v,height)
        seats.append({'uv_mm':[u,v],'height_mm':height})
    for u,v in [(8.36,4.572),(11.86,4.572),(5.84,17.858),(5.84,22.038),(14.48,17.858),(14.48,22.038),(7.27,18.358),(13.05,18.358)]:
        pts,_,_=m.ray.intersects_location([[10.16-u,v,8]],[[0,0,-1]])
        assert len(pts)==0,(u,v,pts)
    target=OUT/'stl/adafruit5807-base.stl';m.export(target)
    report={'status':'PASS','dimensions_mm':m.extents.tolist(),'single_watertight_solid':True,'native_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'print_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'hole_sections':holes,'bearing_and_floor_samples':seats,'open_solder_window_samples':8,'scope':'Exported mesh geometry, not physical print fit or measured strength.'}
    (OUT/'usb-base/mesh-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Base mesh PASS:',m.extents.tolist(),';6 hole sections;6 seat/floor samples;8 open solder-window samples')
if __name__=='__main__':main()
