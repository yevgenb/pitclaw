"""Export the four printed r10 parts and illustrate the assembly sequence."""
import adsk.core as C
import adsk.fusion as F
import runpy,json,hashlib
from pathlib import Path

OUT=Path(__file__).resolve().parent


def camera(app,eye=(17,-20,16),target=(0,0,2.245),extent=None):
    cam=app.activeViewport.camera;cam.cameraType=C.CameraTypes.OrthographicCameraType
    cam.eye=C.Point3D.create(*eye);cam.target=C.Point3D.create(*target)
    cam.upVector=C.Vector3D.create(0,0,1);cam.isFitView=extent is None;cam.isSmoothTransition=False
    if extent is not None:cam.viewExtents=extent
    app.activeViewport.camera=cam;app.activeViewport.refresh()


def run(_context):
    app=C.Application.get();d=F.Design.cast(app.activeProduct)
    assert app.activeDocument.name=='PitClaw enclosure r10 - reinforced probe insert'
    assert d.activateRootComponent()
    occ=list(d.rootComponent.occurrences);assert len(occ)==8
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,1,2,4,5,6,7]
    (OUT/'native-stl').mkdir(exist_ok=True);(OUT/'step').mkdir(exist_ok=True)
    for index,name in [(0,'carrier-bottom'),(1,'carrier-top'),(2,'carrier-retainer'),(7,'probe-fascia')]:
        component=occ[index].component
        opt=d.exportManager.createSTLExportOptions(component,str(OUT/'native-stl'/f'{name}.stl'))
        opt.unitType=F.DistanceUnits.MillimeterDistanceUnits;opt.isBinaryFormat=True
        opt.meshRefinement=F.MeshRefinementSettings.MeshRefinementHigh;opt.surfaceDeviation=.0005;opt.sendToPrintUtility=False
        assert d.exportManager.execute(opt) and (OUT/'native-stl'/f'{name}.stl').is_file()
        assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(OUT/'step'/f'{name}.step'),component))
    camera(app,(9,-20,5))
    assert app.activeViewport.saveAsImageFile(str(OUT/'assembled-probe-face.png'),1600,1100)
    # Sequence1: installed carrier with the probe insert and upper assembly absent.
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,5,6]
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'assembly-1-carrier.png'),1600,1200)
    # Sequence2: panel is positioned on its straight insertion axis.
    original=[o.transform2.copy() for o in occ]
    occ[7].isLightBulbOn=True
    m=original[7].copy();m.translation=C.Vector3D.create(0,-1.4,0);occ[7].transform2=m
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'assembly-2-fascia.png'),1600,1200)
    occ[7].transform2=original[7]
    # Sequence3: the preassembled upper half closes vertically and inserts the keys.
    for i in (1,2,4):
        occ[i].isLightBulbOn=True;m=original[i].copy();m.translation=C.Vector3D.create(0,0,3)
        occ[i].transform2=m
    camera(app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'assembly-3-lid.png'),1600,1400)
    for o,m in zip(occ,original):o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add().name='Restore assembled r10 positions'
    for i,o in enumerate(occ):o.isLightBulbOn=i==7
    camera(app,(10,8,10),(0,-4.725,1.365))
    assert app.activeViewport.saveAsImageFile(str(OUT/'fascia-back.png'),1400,1000)
    for i,o in enumerate(occ):o.isLightBulbOn=i==1
    camera(app,(8,-14,-9),(0,0,3.4))
    assert app.activeViewport.saveAsImageFile(str(OUT/'bezel-keys.png'),1500,1100)
    # Enlarged interior view with the lid 6mm above its assembled position.
    occ[7].isLightBulbOn=True
    m=original[1].copy();m.translation=C.Vector3D.create(0,0,.6);occ[1].transform2=m
    camera(app,(4,2,-1),(2.1,-4.7,3.0),2.1)
    assert app.activeViewport.saveAsImageFile(str(OUT/'reinforced-joint-detail.png'),1500,1200)
    occ[1].transform2=original[1]
    if d.snapshots.hasPendingSnapshot:d.snapshots.add().name='Restore assembled position after joint detail'
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,1,2,4,5,6,7]
    camera(app,(9,-20,5))
    runpy.run_path(str(OUT/'check_native_r10.py'))['run'](_context)
    target=OUT/'pitclaw-enclosure-r10.f3d'
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(target)))
    print(json.dumps({'archive':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'printed_parts':4,'extra_fasteners':0,'overall_envelope_mm':[104,86,44.9]}))
