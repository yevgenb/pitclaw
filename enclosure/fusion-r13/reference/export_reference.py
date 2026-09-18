#!/usr/bin/env python3
"""Export and verify the self-contained r13 reference and optional release coupons.

Requires OpenSCAD and Python with numpy/trimesh. Run from any directory:
  python export_reference.py --copy-coupons
No previous enclosure model or fit-test source is read.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,shutil,subprocess,sys

HERE=Path(__file__).resolve().parent
PARTS=[('bottom','carrier-bottom.stl'),('top','carrier-top.stl'),
       ('retainer','carrier-retainer.stl'),('fascia','probe-fascia.stl'),('usb-base','adafruit5807-base.stl'),
       ('joint-coupon-bottom','joint-coupon-bottom.stl'),
       ('joint-coupon-top','joint-coupon-top.stl'),
       ('joint-coupon-fascia','joint-coupon-fascia.stl'),
       ('fit-coupon','fit-coupon.stl'),('insert-coupon','insert-coupon.stl'),
       ('mount-coupon','mount-coupon.stl')]
COUPONS=[name for part,name in PARTS if 'coupon' in part]
INPUTS=['adafruit5807-base.scad','base-geometry.json','carrier-case.scad','carrier-interface.scad','verify_reference.py',
        'verify_running_clearance.py','geometry-contract.json']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def openscad():
    app=Path('/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD')
    if sys.platform=='darwin' and app.exists():return ['arch','-x86_64',str(app)]
    executable=shutil.which('openscad')
    if not executable:raise RuntimeError('OpenSCAD executable not found')
    return [executable]
def export(entry,command):
    part,name=entry
    args=command+['--export-format','binstl','-o',str(HERE/name),'-D',f'part="{part}"',str(HERE/'carrier-case.scad')]
    result=subprocess.run(args,capture_output=True,text=True)
    log=result.stdout+result.stderr
    (HERE/'logs'/f'{part}-export.log').write_text(log)
    if result.returncode or 'WARNING:' in log or 'ERROR:' in log:
        raise RuntimeError(name+' export failed or emitted diagnostics')
    print(name,'exported',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--copy-coupons',action='store_true')
    args=parser.parse_args()
    if args.jobs<1:parser.error('jobs must be positive')
    before={n:sha(HERE/n) for n in INPUTS}
    (HERE/'logs').mkdir(exist_ok=True)
    command=openscad()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda p:export(p,command),PARTS))
    for check in [['verify_reference.py','--jobs',str(args.jobs)],['verify_running_clearance.py']]:
        result=subprocess.run([sys.executable,str(HERE/check[0])]+check[1:])
        if result.returncode:raise RuntimeError(check[0]+' failed')
    if before!={n:sha(HERE/n) for n in INPUTS}:raise RuntimeError('An input changed during export/verification')
    report=json.loads((HERE/'fit-verification.json').read_text())
    report['geometry_contract']=json.loads((HERE/'geometry-contract.json').read_text())
    report['measured_clearances']=json.loads((HERE/'running-clearance-verification.json').read_text())
    (HERE/'fit-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    names=INPUTS+['README.md','export_reference.py','fit-verification.json','running-clearance-verification.json']+[name for _,name in PARTS]
    manifest={n:sha(HERE/n) for n in names}
    (HERE/'reference-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if args.copy_coupons:
        output=HERE.parent/'stl';output.mkdir(exist_ok=True)
        for name in COUPONS:shutil.copyfile(HERE/name,output/name)
    print('R13 reference complete:37 geometry checks,11 meshes, and measured full-part clearances.',flush=True)

if __name__=='__main__':main()
