#!/usr/bin/env python3
"""Export the checked native PCB and audit the exact JLCPCB upload archive.

Run with KiCad 9 Python; --cam-python needs gerbonara 1.6.3 and shapely 2.x.
The archive contains only seven Gerbers and separate plated/nonplated drills.
This script does not upload or order anything.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zipfile
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
NAME='pitclaw-carrier'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--cam-python',required=True)
parser.add_argument('--cli',default=CLI)
args=parser.parse_args()
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
review=out/'review';review.mkdir(exist_ok=True)
board_path=ROOT/(NAME+'.kicad_pcb')
board_sha=sha(board_path)
summary=json.loads((ROOT/'verification/summary.json').read_text())
assert summary['pcb_sha256']==board_sha,'Run check_draft.py on the current PCB first'
assert summary['erc_violations']==0 and summary['schematic_parity_issues']==0
assert summary['unconnected_items']==0 and not summary['drc_violations_by_type']
board=pcb.LoadBoard(str(board_path))
mm=pcb.ToMM
def cam(v): return [round(mm(v.x),6),round(-mm(v.y),6)]
holes=[];pads=[];vias=[]
for f in board.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() not in (pcb.PAD_ATTRIB_PTH,pcb.PAD_ATTRIB_NPTH):
            raise AssertionError('Review export logic for newly introduced SMD pads')
        x,y=cam(p.GetPosition());dx,dy=map(mm,(p.GetDrillSize().x,p.GetDrillSize().y))
        angle=math.radians(p.GetOrientationDegrees())
        ex,ey=((dx-dy)/2,0) if dx>=dy else (0,(dy-dx)/2)
        # KiCad's positive footprint rotation maps +X toward negative native Y.
        vx=ex*math.cos(angle)+ey*math.sin(angle)
        vy=ex*math.sin(angle)-ey*math.cos(angle)
        endpoints=sorted([[round(x-vx,6),round(y-vy,6)],[round(x+vx,6),round(y+vy,6)]])
        plated=p.GetAttribute()==pcb.PAD_ATTRIB_PTH
        holes.append({'ref':f.GetReference(),'pin':p.GetNumber(),'plated':plated,
                      'diameter_mm':round(min(dx,dy),6),'endpoints_mm':endpoints})
        if plated:
            pads.append({'id':f'{f.GetReference()}:{p.GetNumber()}',
                         'net':p.GetNetname(),'center_mm':[x,y]})
for t in board.GetTracks():
    if isinstance(t,pcb.PCB_VIA):
        xy=cam(t.GetPosition())
        holes.append({'ref':'via','pin':'','plated':True,
                      'diameter_mm':round(mm(t.GetDrillValue()),6),'endpoints_mm':[xy,xy]})
        vias.append({'net':t.GetNetname(),'center_mm':xy})
outline=[]
for g in board.GetDrawings():
    if g.GetLayer()==pcb.Edge_Cuts:
        assert isinstance(g,pcb.PCB_SHAPE) and g.GetShape()==pcb.SHAPE_T_SEGMENT
        outline.append(sorted([cam(g.GetStart()),cam(g.GetEnd())]))
reference={'pcb_sha256':board_sha,'board_size_mm':[60,92],
           'thickness_mm':round(mm(board.GetDesignSettings().GetBoardThickness()),6),
           'copper_layers':board.GetCopperLayerCount(),'outline_segments':sorted(outline),
           'holes':holes,'pads':pads,'vias':vias}
(review/'native-reference.json').write_text(json.dumps(reference,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='pitclaw-jlc-') as temp:
    stage=Path(temp)
    commands=[
        [args.cli,'pcb','export','gerbers','--layers',
         'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',
         '--subtract-soldermask','--disable-aperture-macros','--output',str(stage)+'/',str(board_path)],
        [args.cli,'pcb','export','drill','--format','excellon','--drill-origin','absolute',
         '--excellon-zeros-format','decimal','--excellon-oval-format','alternate',
         '--excellon-units','mm','--excellon-separate-th','--generate-map','--map-format','svg',
         '--output',str(stage)+'/',str(board_path)],
        [args.cli,'pcb','export','ipcd356','--output',str(review/(NAME+'.d356')),str(board_path)],
    ]
    logs=[]
    for command in commands:
        r=subprocess.run(command,check=True,text=True,capture_output=True)
        logs.append({'command':command,'stdout':r.stdout,'stderr':r.stderr})
    files=sorted(p for p in stage.iterdir() if p.suffix in ('.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gm1','.drl'))
    assert Counter(p.suffix for p in files)==Counter({'.gtl':1,'.gbl':1,'.gts':1,'.gbs':1,'.gto':1,'.gbo':1,'.gm1':1,'.drl':2})
    for p in stage.glob('*.svg'):(review/p.name).write_bytes(p.read_bytes())
    upload=out/'pitclaw-carrier-jlcpcb.zip'
    candidate=out/'pitclaw-carrier-jlcpcb.candidate.zip'
    candidate.unlink(missing_ok=True)
    with zipfile.ZipFile(candidate,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in files:archive.writestr(p.name,p.read_bytes())
    # Independently reopen the exact archive, not the KiCad files or staging folder.
    subprocess.run([args.cam_python,str(ROOT/'tools/audit_jlc_cam.py'),str(candidate),
                    str(review/'native-reference.json'),str(review)],check=True)
    assert sha(board_path)==board_sha,'PCB changed during export'
    candidate.replace(upload)
    file_hashes={p.name:sha(p) for p in files}
(review/'native-export-log.json').write_text(json.dumps(logs,indent=2)+'\n')
manifest={'status':'BARE-PCB PROTOTYPE FABRICATION PACKAGE; PHYSICAL QUALIFICATION PENDING',
          'pcb_sha256':board_sha,'schematic_sha256':sha(ROOT/(NAME+'.kicad_sch')),
          'project_rules_sha256':sha(ROOT/(NAME+'.kicad_pro')),
          'verification_summary_sha256':sha(ROOT/'verification/summary.json'),
          'archive':upload.name,'archive_sha256':sha(upload),'files_sha256':file_hashes,
          'board_mm':[60,92,1.6],'copper_layers':2,'copper_weight_oz':1,
          'kicad_version':subprocess.check_output([args.cli,'version'],text=True).strip(),
          'order_submitted':False,'assembly_service_package':False}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'archive':str(upload),'pcb_sha256':board_sha,'archive_sha256':sha(upload)},indent=2))
