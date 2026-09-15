"""Package the current verified fit-test coupons without changing the full release."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((HERE / 'fit-verification.json').read_text())
    generation = json.loads((HERE / 'generation-manifest.json').read_text())
    assert report['status'].startswith('PASS')
    assert generation['released_artifacts_unchanged']
    for name, digest in generation['protected_sha256'].items():
        assert sha(HERE.parent / name) == digest, name
    for record in report['meshes'].values():
        assert record['result'] == 'PASS'
        assert sha(HERE / record['file']) == record['sha256'], record['file']
    for name, digest in generation['source_sha256'].items():
        assert sha(HERE / 'sources' / name) == digest, name
    files = ['README.md', 'closure-post.png', 'guide-clearance.png',
             'guide-clearance.svg', 'bottom.stl', 'top.stl', 'fascia.stl',
             'control-bottom.stl', 'control-top.stl', 'fit-parameters.json',
             'fit-verification.json', 'generation-manifest.json']
    for name in ['running-clearance-verification.json', 'insert-hole-verification.json']:
        section_report = HERE / name
        if section_report.exists():
            assert json.loads(section_report.read_text())['status'].startswith('PASS')
            files.append(section_report.name)
    manifest = {
        'scope': 'Fit-test coupons only; released R12 enclosure unchanged',
        'geometry_checks': len(report['geometry_checks']),
        'mesh_checks': len(report['meshes']),
        'files_sha256': {name: sha(HERE / name) for name in files},
    }
    (HERE / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files.append('package-manifest.json')
    target = HERE / 'joint-fit-test.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in files:
            z.write(HERE / name, name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(files)
        for name in files:
            assert z.read(name) == (HERE / name).read_bytes(), name
    print(json.dumps({'archive': str(target), 'sha256': sha(target),
                      'geometry_checks': manifest['geometry_checks'],
                      'mesh_checks': manifest['mesh_checks'], 'status': 'PASS'}, indent=2))


if __name__ == '__main__':
    main()
