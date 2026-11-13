"""Measure display contact from exported meshes, including the original-gap control."""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent
TOLERANCE = .005


def crossings(mesh, x, y):
    points, _, _ = mesh.ray.intersects_location([[x, y, 0]], [[0, 0, 1]])
    assert len(points) == 2, (x, y, points)
    return sorted(float(z) for z in points[:, 2])


def measure(top, retainer):
    ledges = [crossings(top, x, y)[0] for x, y in [(27, 0), (-27, 0), (0, 42), (0, -42)]]
    seats = []
    for x in (-35.5, 35.5):
        for y in (-40, 40):
            underside, seat = crossings(retainer, x + 3, y)
            stop = crossings(top, x + 3, y)[0]
            seats.append({'xy_mm': [x, y], 'retainer_back_z_mm': underside,
                          'retainer_front_z_mm': seat, 'stop_z_mm': stop,
                          'stop_to_retainer_gap_mm': stop - seat,
                          'glass_to_bezel_gap_mm': min(ledges) - (seat + 9.3)})
    return {'bezel_underside_samples_z_mm': ledges, 'anchors': seats}


def assert_contact(record):
    assert np.allclose(record['bezel_underside_samples_z_mm'], 43.7, atol=TOLERANCE)
    for p in record['anchors']:
        assert abs(p['stop_to_retainer_gap_mm']) < TOLERANCE, p
        assert abs(p['glass_to_bezel_gap_mm']) < TOLERANCE, p
        assert abs(p['retainer_back_z_mm'] - 31.9) < TOLERANCE, p


def main():
    source_paths = [OUT / 'native-stl' / f'carrier-{name}.stl' for name in ('top', 'retainer')]
    top, retainer = [trimesh.load(p, force='mesh') for p in source_paths]
    measured = measure(top, retainer)
    assert_contact(measured)
    # Deliberately restore the old display plane. The contact acceptance must
    # reject it even though it is collision-free, as the former checks allowed.
    old_top = top.copy()
    for plane in (34.4, 39.4):
        old_top.vertices[np.isclose(old_top.vertices[:, 2], plane, atol=.00001), 2] -= 1.8
    old_retainer = retainer.copy()
    old_retainer.apply_translation([0, 0, -1.8])
    old = measure(old_top, old_retainer)
    assert all(abs(p['stop_to_retainer_gap_mm']) < TOLERANCE for p in old['anchors'])
    assert all(abs(p['glass_to_bezel_gap_mm'] - 1.8) < TOLERANCE for p in old['anchors'])
    rejected = False
    try:
        assert_contact(old)
    except AssertionError:
        rejected = True
    assert rejected, 'Original-gap negative control was accepted'
    # Also measure the distributed print mesh after returning it to assembly.
    print_top = trimesh.load(OUT / 'stl/carrier-top.stl', force='mesh')
    print_top.vertices *= [1, -1, -1]
    print_top.vertices += [0, 0, 44.9]
    print_retainer = trimesh.load(OUT / 'stl/carrier-retainer.stl', force='mesh')
    print_retainer.apply_translation([0, 0, 31.9])
    print_record = measure(print_top, print_retainer)
    assert_contact(print_record)
    source_paths += [OUT / 'stl' / f'carrier-{name}.stl' for name in ('top', 'retainer')]
    shims=[]
    for thickness in (.1,.2):
        p=OUT/'stl'/f'display-shim-{thickness:.1f}.stl'
        mesh=trimesh.load(p,force='mesh')
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
        assert np.allclose(mesh.extents,[9,9,thickness],atol=.00001)
        assert len(mesh.ray.intersects_location([[0,0,1]],[[0,0,-1]])[0])==0
        assert np.allclose(crossings(mesh,3,0),[0,thickness],atol=.00001)
        shims.append({'file':p.name,'thickness_mm':thickness,'outer_diameter_mm':9,
                      'through_hole_mm':3.4,'copies_required':4})
        source_paths.append(p)
    fit_cases=[]
    for shim in (0,.1,.2,.3):
        effective_depth=9.3+shim
        gap=min(measured['bezel_underside_samples_z_mm'])-(measured['anchors'][0]['retainer_front_z_mm']-shim+effective_depth)
        assert abs(gap)<TOLERANCE
        fit_cases.append({'anchor_shim_mm':shim,'effective_module_depth_mm':round(effective_depth,6),
                          'glass_to_bezel_gap_mm':gap,'forward_movement_mm':round(1.8-shim,6)})
    result = {'status': 'PASS', 'native': measured, 'print': print_record,
              'shim_meshes':shims,'fit_range':fit_cases,
              'original_gap_negative_control_rejected': rejected,
              'original_gap_control_mm': 1.8, 'effective_mount_depth_range_mm': [9.3,9.6],
              'tolerance_mm': TOLERANCE,
              'sources_sha256': {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}
    (OUT / 'display-seat-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: four bezel edges and four retainer seats, native and print meshes; original-gap control rejected.')


if __name__ == '__main__':
    main()
