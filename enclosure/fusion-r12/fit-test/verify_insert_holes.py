"""Measure heat-set pilots and unchanged screw passages in the exported coupons."""
from pathlib import Path
import hashlib
import json
import trimesh
from verify_running_clearance import crossings, near

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    locations = [
        ('bottom.stl', 'carrier insert pilot', -1, 0, [3, 5, 7], 4.2),
        ('bottom.stl', 'closure insert pilot', 11.5, 9, [23, 25, 27], 4.2),
        ('bottom.stl', 'accessory mount insert pilot', 9.5, 0, [3, 5, 7], 4.2),
        ('top.stl', 'retainer insert pilot', 9, 3, [8, 10, 12], 4.2),
        ('top.stl', 'closure screw passage', 11.5, -9, [10], 3.4),
        ('bottom.stl', 'external mounting screw passage', 9.5, 0, [1.5], 3.4),
        ('control-bottom.stl', 'control closure insert pilot', 11.5, 9, [25], 4.0),
        ('control-top.stl', 'control retainer insert pilot', 9, 3, [10], 4.0),
    ]
    files = sorted({row[0] for row in locations})
    before = {name: sha(HERE / name) for name in files}
    meshes = {name: trimesh.load(HERE / name, force='mesh') for name in files}
    report = {'status': 'RUNNING', 'scope': 'Diameters measured from actual print-oriented STL sections; no retention-force claim.',
              'sources_sha256': before, 'measurements': []}
    for name, label, x, y, zs, expected in locations:
        for z in zs:
            segments = trimesh.intersections.mesh_plane(meshes[name], [0, 0, 1], [0, 0, z])
            xs = crossings(segments, 1, y, 0)
            left = max(v for v in xs if v < x)
            right = min(v for v in xs if v > x)
            near(left, x - expected / 2)
            near(right, x + expected / 2)
            report['measurements'].append({'file': name, 'feature': label,
                'print_coordinates_mm': [x, y, z], 'diameter_mm': right - left,
                'expected_diameter_mm': expected})
    assert before == {name: sha(HERE / name) for name in files}
    report['status'] = 'PASS: 4.2mm candidate pilots, unchanged screw passages and controls'
    (HERE / 'insert-hole-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])
    print('Measured sections:', len(report['measurements']))


if __name__ == '__main__':
    main()
