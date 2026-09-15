#!/usr/bin/env python3
"""Build bounded fit coupons from the current R12 reference; never edit the release.

Run with the same Python environment as reference/verify_reference.py.
Only fit-test/ is written. Complete enclosure geometry is copied only for the
assembly checks; output STLs are cropped coupons, not a new enclosure release.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,subprocess,sys
import vertical_clearance

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'reference'
EXPECTED_BASE_SCAD='37b97045a014de0b7f250b26c06991e2e7b8c5c206489d3bf380c2b89a6706ca'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Scoped replacement did not match exactly once: '+old)
    return text.replace(old,new)
def protect():
    files=[p for p in BASE.rglob('*') if p.is_file()]
    files+=list((HERE.parent/'stl').glob('*.stl'))
    files+=list((HERE.parent/'native-stl').glob('*.stl'))
    files+=list(HERE.parent.glob('*.f3d'))
    return {str(p.relative_to(HERE.parent)):sha(p) for p in sorted(set(files))}

def generate_sources():
    if sha(BASE/'carrier-case.scad')!=EXPECTED_BASE_SCAD:
        raise ValueError('The released R12 source changed; review the scoped coupon changes first')
    folder=HERE/'sources';folder.mkdir(exist_ok=True)
    original=(BASE/'carrier-case.scad').read_text()
    control=original
    for old,new,count in [
        ('box_bounds(10,43,-52,-40.5,-.02,60)','box_bounds(10,43,-52,-22,-.02,60)',3),
        ('translate([-26.5,46.25,0])','translate([-26.5,37,0])',1),
        ('translate([-26.5,-46.25,case_height])','translate([-26.5,-37,case_height])',1),
    ]:
        if control.count(old)!=count:raise ValueError('Coupon crop replacement count changed')
        control=control.replace(old,new)
    candidate=control
    edits=[
        ('xz_prism([[32.7,3.8],[36.4,3.8],[36.4,5.9],[32.7,9.6]],-52.1,-43);',
         'xz_prism([[32.7,3.8],[36.3,3.8],[36.3,41.8+sqrt(2)*.25-36.3],[32.7,41.8+sqrt(2)*.25-32.7]],-52.1,-43);'),
        ('box_bounds(-33,33,-53,-42.5,0,27.3);','box_bounds(-33.1,33.1,-53,-42.5,0,27.4);'),
        ('box_bounds(31,33,-52,-42.5,2.48,9.5);','box_bounds(31,33.1,-52,-42.5,2.48,9.5);'),
        ('box_bounds(x-6.3,x+6.3,-50.85,-48.25,20.78,27.32);','box_bounds(x-6.3,x+6.3,-50.85,-48.25,20.78,27.42);'),
        ('translate([-23,13.65,52])','translate([-23,13.7,52])'),
        ('translate([0,0,.2999]) probe_fascia();','translate([0,0,.1999]) probe_fascia();'),
    ]
    for a,b in edits:candidate=replace_once(candidate,a,b)
    # This is the single lip-ring call. Only its OUTER radius changes; the
    # old inner radius1.0, dimensions, shoulder and retainer cuts stay identical.
    old='''                ring(lip_width,lip_length,
                         lip_width-2*locating_lip_wall,
                         lip_length-2*locating_lip_wall,
                         locating_lip_height+eps,2);'''
    new='''                difference() {
                    rounded_solid(lip_width,lip_length,locating_lip_height+eps,2.2);
                    translate([0,0,-eps])
                        rounded_solid(lip_width-2*locating_lip_wall,
                                      lip_length-2*locating_lip_wall,
                                      locating_lip_height+3*eps,1);
                }'''
    candidate=replace_once(candidate,old,new)
    marker='''            for(x=[-21,21])
                box_bounds(x-9.3,x+9.3,-52,-45.5,20.8,25);'''
    candidate=replace_once(candidate,marker,'''            // Only the floor extends rearward; the probe plate remains fixed.
            box_bounds(-33.1,33.1,-42.52,-42.2,0,2.5);
'''+marker)
    candidate=replace_once(candidate,'else if(part=="shell-closure-check") shell_closure_collision();',
        'else if(part=="shell-closure-check") shell_closure_collision();\nelse if(part=="shell-closure-with-fascia-check") shell_closure_with_fascia_collision();')
    candidate+='''\nmodule shell_closure_with_fascia_collision() {
    intersection() { top_bezel(); union() { bottom_shell(); probe_fascia(); } }
}
'''
    candidate=candidate.replace('// Approach the0.3mm upward stop within0.0001mm numerical margin.','// FIT TEST: approach the0.2mm upward stop within0.0001mm numerical margin.').replace('// At exactly0.3mm, the fascia top intentionally contacts seamZ27.6.','// At exactly0.2mm, the fascia top intentionally contacts seamZ27.6.')
    candidate=vertical_clearance.candidate(candidate)
    (folder/'candidate.scad').write_text('// FIT TEST ONLY. Not a revised enclosure release.\n'+candidate)
    (folder/'control.scad').write_text('// CURRENT R12 CONTROL. Only the coupon crop and print centering differ.\n'+control)
    (folder/'carrier-interface.scad').write_bytes((BASE/'carrier-interface.scad').read_bytes())
    verifier=(BASE/'verify_reference.py').read_text()
    verifier=verifier.replace('python3 enclosure/fusion-r12/reference/verify_reference.py','python3 enclosure/fusion-r12/fit-test/verify_fit_test.py')
    verifier=verifier.replace('Check the isolated r12 interior-mount-insert handedness reference and its installation scenarios.','Check the bounded fit-test candidate and its clamped comparison coupons.')
    verifier=verifier.replace('"enclosure/fusion-r12/reference/carrier-case.scad",','"enclosure/fusion-r12/fit-test/sources/candidate.scad",\n    "enclosure/fusion-r12/fit-test/sources/control.scad",')
    verifier=verifier.replace('"enclosure/fusion-r12/reference/carrier-interface.scad",','"enclosure/fusion-r12/fit-test/sources/carrier-interface.scad",')
    verifier=verifier.replace('str(Path(__file__).with_name("carrier-case.scad"))','str(Path(__file__).with_name("sources")/"candidate.scad")')
    start=verifier.index('EXPECTED_SIZE = {');end=verifier.index('\n\n\n@dataclass',start)
    verifier=verifier[:start]+'''EXPECTED_SIZE = {
    "candidate_bottom":[33,30,27.6],"candidate_top":[33,30,21.9],
    "candidate_fascia":[26,27.4,9.8],"control_bottom":[33,30,27.6],
    "control_top":[33,30,21.9],
}
MESH_NAMES = {
    "candidate_bottom":"bottom.stl","candidate_top":"top.stl",
    "candidate_fascia":"fascia.stl","control_bottom":"control-bottom.stl",
    "control_top":"control-top.stl",
}'''+verifier[end:]
    verifier=verifier.replace('"mount-screw-check", "mount-tool-check")]','"mount-screw-check", "mount-tool-check", "shell-closure-with-fascia-check")]')
    verifier=verifier.replace('check.part == "shell-closure-check" and target.is_file()','check.part in ("shell-closure-check","shell-closure-with-fascia-check") and target.is_file()')
    verifier=verifier.replace('"carrier-enclosure-fusion-r12-reference"','"bounded-clamped-fit-test"')
    verifier=verifier.replace('"scope": "Declared nominal geometry and explicit tolerance scenarios; no physical print or purchased-part fit test."','"scope": "FIT TEST ONLY: candidate full-assembly geometry and five cropped comparison meshes; released enclosure untouched."')
    verifier=vertical_clearance.verifier(verifier)
    (HERE/'verify_fit_test.py').write_text(verifier)
    return folder

def export_one(entry,folder):
    name,source,part=entry
    command=['arch','-x86_64','/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD','--export-format','binstl','-o',str(HERE/name),'-D',f'part="{part}"',str(folder/source)]
    result=subprocess.run(command,capture_output=True,text=True)
    (HERE/'logs').mkdir(exist_ok=True)
    (HERE/'logs'/(name+'.export.log')).write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(name+' export failed')
    print(name,'exported',flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources-only',action='store_true');parser.add_argument('--bottom-only',action='store_true');args=parser.parse_args()
    before=protect()
    keep_names=["top.stl","fascia.stl","control-bottom.stl","control-top.stl"]
    kept={n:sha(HERE/n) for n in keep_names} if args.bottom_only else {}
    folder=generate_sources()
    if not args.sources_only:
        entries=[('bottom.stl','candidate.scad','joint-coupon-bottom'),('top.stl','candidate.scad','joint-coupon-top'),('fascia.stl','candidate.scad','joint-coupon-fascia'),('control-bottom.stl','control.scad','joint-coupon-bottom'),('control-top.stl','control.scad','joint-coupon-top')]
        if args.bottom_only:entries=entries[:1]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda x:export_one(x,folder),entries))
        result=subprocess.run([sys.executable,str(HERE/'verify_fit_test.py'),'--jobs','3'])
        if result.returncode:raise RuntimeError('Candidate fit verification failed')
        measured=subprocess.run([sys.executable,str(HERE/'verify_running_clearance.py')])
        if measured.returncode:raise RuntimeError('Exported running-clearance measurement failed')
    if kept and kept!={n:sha(HERE/n) for n in keep_names}:raise RuntimeError("A retained fit-test STL changed")
    after=protect()
    if before!=after:raise RuntimeError('A protected release artifact changed during generation')
    record={'scope':'FIT TEST ONLY','released_artifacts_unchanged':True,'protected_sha256':after,
            'retained_fit_stl_sha256':kept,'bottom_only':args.bottom_only,
            'source_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()},
            'outputs_sha256':{p.name:sha(p) for p in HERE.glob('*.stl')}}
    (HERE/'generation-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Protected release unchanged.',flush=True)

if __name__=='__main__':main()
