"""Export and render the completed r9 model, leaving its populated PCB visible."""
import adsk.core as C
import adsk.fusion as F
import json,runpy,hashlib
from pathlib import Path

OUT=Path(__file__).resolve().parent


def run(_context):
    app=C.Application.get();d=F.Design.cast(app.activeProduct)
    assert app.activeDocument.name=='PitClaw enclosure r9 - populated carrier'
    occ=list(d.rootComponent.occurrences);assert len(occ)==7
    # Fusion may report export success without creating a file for a hidden part.
    for o in occ[:3]:o.isLightBulbOn=True
    camera=runpy.run_path(str(OUT/'support/build_fusion_r8.py'))['camera']
    (OUT/'native-stl').mkdir(exist_ok=True);(OUT/'step').mkdir(exist_ok=True)
    for o,part in zip(occ[:3],['bottom','top','retainer']):
        assert o.component.bRepBodies.count==1
        opt=d.exportManager.createSTLExportOptions(o.component,str(OUT/'native-stl'/f'carrier-{part}.stl'))
        opt.unitType=F.DistanceUnits.MillimeterDistanceUnits
        opt.isBinaryFormat=True;opt.meshRefinement=F.MeshRefinementSettings.MeshRefinementHigh
        opt.surfaceDeviation=.0005;opt.sendToPrintUtility=False
        assert d.exportManager.execute(opt)
        assert (OUT/'native-stl'/f'carrier-{part}.stl').is_file()
        assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(OUT/'step'/f'carrier-{part}.step'),o.component))
        assert (OUT/'step'/f'carrier-{part}.step').is_file()
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,1,2,4,5,6]
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-assembled.png'),1800,1400)
    original=[o.transform2.copy() for o in occ]
    for o,m,z in zip(occ,original,[0,8,4.5,0,6,3,3]):
        m=m.copy();tr=m.translation
        m.translation=C.Vector3D.create(tr.x,tr.y,tr.z+z);o.transform2=m
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-exploded.png'),1800,1600)
    for o,m in zip(occ,original):o.transform2=m
    for o,m in zip(occ,original):assert all(abs(a-b)<1e-9 for a,b in zip(o.transform2.asArray(),m.asArray()))
    if d.snapshots.hasPendingSnapshot:d.snapshots.add().name='Restore assembled component positions'
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,5,6]
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'pcb-in-bottom.png'),1800,1400)
    occ[0].isLightBulbOn=False;camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'pcb-populated.png'),1800,1400)
    occ[0].isLightBulbOn=True;camera(app)
    runpy.run_path(str(OUT/'check_native_r9.py'))['run'](_context)
    target=OUT/'pitclaw-populated-r9.f3d'
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(target)))
    print(json.dumps({'archive':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'root_components':len(occ),'view':'Populated board in open bottom; top/display hidden for inspection.'}))
