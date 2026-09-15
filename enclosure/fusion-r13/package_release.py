"""Validate and package the reinforced r13 fit prototype; never edit hardware."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PROTECTED = {
    'hardware/carrier-revb/pitclaw-carrier.kicad_pcb': '7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764',
    'hardware/carrier-revb/pitclaw-carrier.kicad_pro': '814bd6b79383344938fb11cef374c5ab29d7d67091976e8c2353aa28831d35bf',
    'hardware/carrier-revb/fabrication/jlcpcb-2026-09-06/pitclaw-carrier-jlcpcb.zip': 'd75ea76ef0e9b0892459d3f8e0c6367630f1d467716bc774757389a562409497',
}
SIZES = {
    'carrier-bottom': [86, 104, 27.6], 'carrier-top': [86, 104, 21.9],
    'carrier-retainer': [80, 96, 2.5], 'probe-fascia': [72, 27.4, 9.8],
    'joint-coupon-bottom': [33, 30, 27.6], 'joint-coupon-top': [33, 30, 21.9],
    'joint-coupon-fascia': [26, 27.4, 9.8],
    'fit-coupon': [86, 22, 27.6], 'insert-coupon': [36, 16, 7.5],
    'mount-coupon': [16, 21, 10],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name, expected in PROTECTED.items():
        assert sha(ROOT / name) == expected, f'Protected file changed: {name}'
    native = json.loads((OUT / 'native-verification.json').read_text())
    comparison = json.loads((OUT / 'mesh-verification.json').read_text())
    reference = json.loads((OUT / 'reference/fit-verification.json').read_text())
    assert native['status'] == 'PASS' and comparison['status'] == 'PASS'
    assert reference['status'] == 'PASS: CAD GEOMETRY'
    for report_name in ('running-clearance-verification.json','insert-hole-verification.json'):
        measured=json.loads((OUT/report_name).read_text())
        assert measured['status'].startswith('PASS'),report_name
        for name,expected in measured['sources_sha256'].items():
            path=OUT/name if '/' in name else OUT/'native-stl'/(name+'.stl')
            assert sha(path)==expected,(report_name,name)
    for name, expected in json.loads((OUT / 'reference/reference-manifest.json').read_text()).items():
        assert sha(OUT / 'reference' / name) == expected, name

    meshes = {}
    for name, expected_size in SIZES.items():
        path = OUT / 'stl' / (name + '.stl')
        m = trimesh.load(path, force='mesh')
        assert m.is_watertight and m.is_winding_consistent and len(m.split()) == 1, name
        assert m.volume > 0 and abs(m.bounds[0, 2]) < .001, name
        assert np.allclose(m.extents, expected_size, atol=.005), (name, m.extents)
        meshes[name] = {'dimensions_mm': m.extents.tolist(), 'watertight': True,
                        'connected_solids': 1, 'volume_mm3': float(m.volume),
                        'sha256': sha(path)}
    for part, record in comparison['parts'].items():
        name = 'probe-fascia' if part == 'fascia' else 'carrier-' + part
        assert meshes[name]['sha256'] == record['print_stl_sha256']
        assert sha(OUT / 'native-stl' / (name + '.stl')) == record['native_source_sha256']
        assert sha(OUT / 'reference' / (name + '.stl')) == record['reference_sha256']
    for name in ['joint-coupon-bottom', 'joint-coupon-top', 'joint-coupon-fascia',
                 'fit-coupon', 'insert-coupon', 'mount-coupon']:
        assert meshes[name]['sha256'] == sha(OUT / 'reference' / (name + '.stl'))

    files = [OUT / p for p in [
        'README.md', 'mount-review.md', 'mount-interface.json', 'mount-pattern.dxf',
        'guide-review.md', 'guide-clearance.png', 'guide-clearance.svg',
        'pitclaw-enclosure-r13.f3d',
        'native-verification.json', 'mesh-verification.json', 'build-native.json',
        'reference/fit-verification.json',
        'running-clearance-verification.json', 'insert-hole-verification.json',
        'assembled-probe-face.png', 'assembly-1-carrier.png', 'assembly-2-fascia.png',
        'assembly-3-lid.png', 'fascia-back.png', 'bezel-keys.png', 'reinforced-joint-detail.png',
        'bottom-mounts-inside.png', 'bottom-mounts-outside.png', 'mount-pattern-top-view.png',
    ]]
    files += sorted((OUT / 'stl').glob('*.stl'))
    files += sorted((OUT / 'step').glob('*.step'))
    # Include the source and comparison meshes so the downloaded kit remains reviewable.
    files += sorted((OUT/'native-stl').glob('*.stl'))
    files += [p for p in sorted((OUT/'reference').iterdir()) if p.is_file()]
    files += sorted(OUT.glob('*.py'))
    files = sorted(set(files))
    assert len(list((OUT / 'stl').glob('*.stl'))) == 10
    assert len(list((OUT / 'step').glob('*.step'))) == 4
    assert all(p.is_file() and p.stat().st_size > 0 for p in files)
    manifest = {
        'revision': 'r13 fitted complete enclosure',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'CAD VERIFIED FIT PROTOTYPE; physical print validation pending',
        'geometry_checks': len(reference['geometry_checks']),
        'reference_meshes': len(reference['meshes']),
        'native_body_case_tests': native['body_case_boolean_tests'],
        'native_mesh_comparison': comparison['status'],
        'additional_mount_inserts': 4, 'total_case_inserts': 16,
        'mount_pitch_mm': [72, 74], 'mount_thread': 'M3',
        'guide_engagement_mm': 9, 'guide_side_clearance_mm': .3,
        'guide_roof_normal_clearance_mm': .4,
        'guide_lower_running_clearance_mm': .3, 'fascia_seam_gap_mm': .2,
        'insert_pilot_diameter_mm': 4.2, 'measured_insert_od_range_mm': [4,5],
        'protected_files_unchanged_sha256': PROTECTED,
        'print_meshes': meshes,
        'files_sha256': {str(p.relative_to(OUT)): sha(p) for p in files},
    }
    target_manifest = OUT / 'release-manifest.json'
    target_manifest.write_text(json.dumps(manifest, indent=2) + '\n')
    files.append(target_manifest)
    archive = OUT / 'pitclaw-enclosure-r13.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, str(p.relative_to(OUT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {str(p.relative_to(OUT)) for p in files}
        for p in files:
            assert hashlib.sha256(z.read(str(p.relative_to(OUT)))).hexdigest() == sha(p)
    print(json.dumps({'archive': str(archive), 'archive_sha256': sha(archive),
                      'size_bytes': archive.stat().st_size, 'packaged_files': len(files),
                      'print_meshes': len(meshes), 'protected_hardware_unchanged': True,
                      'status': 'PASS'}, indent=2))


if __name__ == '__main__':
    main()
