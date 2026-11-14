"""Package freshly built firmware and the checked-in r13 archive; no CAD edits.

Run after the firmware/tests pass. The output directory must not already exist.
This checks artifact integrity, not physical hardware qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'enclosure/fusion-r13'
BOM = ROOT / 'hardware/carrier-revb/bom'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=ROOT,
                   check=True, stdout=subprocess.DEVNULL)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                     text=True).strip()
    config = (ROOT / 'firmware/src/config.h').read_text()
    version = re.search(r'#define FIRMWARE_VERSION\s+"([^"]+)"', config).group(1)
    ui = re.search(r'#define WEB_UI_BUILD\s+"([^"]+)"', config).group(1)
    firmware = ROOT / 'firmware/.pio/build/wt32_sc01_plus/firmware.bin'
    binary = firmware.read_bytes()
    if binary[:1] != b'\xe9' or version.encode() not in binary:
        raise ValueError('Firmware is not an ESP image with the source firmware version')

    archive = CASE / 'pitclaw-enclosure-r13.zip'
    manifest = json.loads((CASE / 'release-manifest.json').read_text())
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Enclosure ZIP failed its CRC check')
        if bundle.read('release-manifest.json') != (CASE / 'release-manifest.json').read_bytes():
            raise ValueError('Enclosure archive manifest is stale')
        for name, expected in manifest['files_sha256'].items():
            if digest(bundle.read(name)) != expected or digest((CASE / name).read_bytes()) != expected:
                raise ValueError(f'Enclosure file differs from its manifest: {name}')

    assets = [firmware, archive, BOM / 'pitclaw-carrier-digikey-bom.xlsx',
              BOM / 'pitclaw-carrier-digikey-import.csv']
    for source in assets:
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError(f'Missing or empty release asset: {source}')
    args.output.mkdir(parents=True, exist_ok=False)
    for source in assets:
        shutil.copyfile(source, args.output / source.name)

    base = f'https://github.com/yevgenb/pitclaw/blob/{commit}'
    (args.output / 'BUILD-GUIDE.md').write_text(
        '# Pit Claw prototype build instructions\n\n'
        f'Source commit: `{commit}`. Firmware: `{version}`; web UI: `{ui}`.\n\n'
        f'Start with the [builder\'s guide]({base}/docs/build-guide.md), then use\n'
        f'the [wiring]({base}/docs/wiring.md), '
        f'[BOM notes]({base}/hardware/carrier-revb/bom/README.md) and\n'
        f'[enclosure assembly guide]({base}/enclosure/fusion-r13/README.md).\n\n'
        'The firmware.bin asset is for OTA on a compatible installation. For a\n'
        'first USB installation, follow the PlatformIO instructions in the guide.\n'
        'Do not upload a filesystem image; the web UI is embedded in firmware.\n'
        'Finish the cook before updating. Restart resets runtime temperatures.\n\n'
        'Physical fit, cold-start overshoot and carrier load/thermal checks remain.\n'
        f'[Licensing remains unresolved]({base}/README.md#license).\n'
    )
    records = {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
               for p in sorted(args.output.iterdir())}
    (args.output / 'release-manifest.json').write_text(json.dumps({
        'status': 'prototype; physical qualification incomplete',
        'source_commit': commit, 'firmware_version': version, 'web_ui_build': ui,
        'enclosure': 'Fusion r13', 'carrier': 'Rev B-T2F0-A5807-S4',
        'license_status': 'unresolved; no new license granted', 'assets': records,
    }, indent=2) + '\n')
    checksums = ''.join(f'{digest(p.read_bytes())}  {p.name}\n'
                        for p in sorted(args.output.iterdir()))
    (args.output / 'SHA256SUMS').write_text(checksums)
    # Verify the bytes being released, including copied files and generated notes.
    for line in checksums.splitlines():
        expected, name = line.split('  ', 1)
        if digest((args.output / name).read_bytes()) != expected:
            raise ValueError(f'Packaged checksum mismatch: {name}')
    for source in assets:
        if digest(source.read_bytes()) != digest((args.output / source.name).read_bytes()):
            raise ValueError(f'Copy mismatch: {source.name}')
    print(f'PASS: {len(list(args.output.iterdir()))} assets; source {commit}; firmware {version}')


if __name__ == '__main__':
    main()
