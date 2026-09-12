"""Validate native Fusion r10 exports against the independent assembly reference.

Requires numpy, trimesh, scipy, rtree. Checks real meshes, not pictures.
Surface checks sample all vertices, face centers and 5000 seeded surface points
in each direction. This is a sampled comparison, not a mathematical Hausdorff bound.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh

OUT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_record(m):
    return {'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),
            'connected_solids':len(m.split()),'volume_mm3':float(m.volume),
            'bounds_mm':m.bounds.tolist(),'triangles':len(m.faces)}


def distances(source,target):
    samples,_=trimesh.sample.sample_surface(source,5000,seed=8)
    points=np.vstack((source.vertices,source.triangles_center,samples))
    ds=[]
    for start in range(0,len(points),500):
        _,d,_=trimesh.proximity.closest_point(target,points[start:start+500])
        ds.extend(d)
    return {'samples':len(points),'max_mm':float(np.max(ds)),'p99_mm':float(np.quantile(ds,.99))}


def main():
    result={'scope':'Native Fusion mesh integrity and sampled comparison with independently checked four-anchor OpenSCAD reference.',
            'surface_allowance_mm':.03,'allowance_reason':'Analytic CAD arcs versus SCAD faceting and 0.02mm Boolean construction overlaps.',
            'parts':{}}
    (OUT/'stl').mkdir(exist_ok=True)
    for part in ('bottom','top','retainer','fascia'):
        filename='probe-fascia.stl' if part=='fascia' else f'carrier-{part}.stl'
        path=OUT/'native-stl'/filename
        native=trimesh.load(path,force='mesh')
        if part=='top':
            native.vertices*=np.array([1,-1,-1])
            native.vertices+=np.array([0,0,44.9])
        elif part=='retainer':
            native.vertices-=np.array([0,0,30.1])
        elif part=='fascia':
            old=native.vertices.copy()
            native.vertices=np.column_stack((old[:,0],-old[:,2],old[:,1]+52))
        ref_path=OUT/'reference'/filename
        ref=trimesh.load(ref_path,force='mesh')
        record=mesh_record(native)
        record['native_source_sha256']=sha(path)
        record['reference_sha256']=sha(ref_path)
        assert record['watertight'] and record['winding_consistent'] and record['connected_solids']==1
        assert record['volume_mm3']>0
        assert np.allclose(native.bounds,ref.bounds,atol=.005), (part,native.bounds,ref.bounds)
        record['native_to_reference']=distances(native,ref)
        record['reference_to_native']=distances(ref,native)
        record['relative_volume_difference']=float((native.volume-ref.volume)/ref.volume)
        record['surface_comparison_pass']=max(record['native_to_reference']['max_mm'],record['reference_to_native']['max_mm'])<=.03
        print(part,record['native_to_reference'],record['reference_to_native'],flush=True)
        target=OUT/'stl'/filename
        native.export(target)
        record['print_stl_sha256']=sha(target)
        result['parts'][part]=record
    result['status']='PASS' if all(p['surface_comparison_pass'] for p in result['parts'].values()) else 'FAIL: investigate geometry difference'
    (OUT/'mesh-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['status']=='PASS'
    print('PASS: all native meshes and surface comparisons.')


if __name__=='__main__':
    main()
