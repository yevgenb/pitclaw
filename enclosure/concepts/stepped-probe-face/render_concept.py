"""Appearance study only: a stepped probe face under the existing screen.

Creates a separate Fusion document from the r9 archive. Does not modify r9 or
export printable STLs. The future split fascia / assembly joint is unresolved.
"""
import adsk.core as C
import adsk.fusion as F
import runpy,json,math,hashlib
from pathlib import Path

OUT=Path(__file__).resolve().parent
ENCLOSURE=Path(__file__).resolve().parents[2]


def camera(app,eye):
    cam=app.activeViewport.camera
    cam.cameraType=C.CameraTypes.OrthographicCameraType
    cam.eye=C.Point3D.create(*eye)
    cam.target=C.Point3D.create(0,0,2.245)
    cam.upVector=C.Vector3D.create(0,0,1)
    cam.isFitView=True;cam.isSmoothTransition=False
    app.activeViewport.camera=cam;app.activeViewport.refresh()


def run(_context):
    app=C.Application.get()
    source=ENCLOSURE/'fusion-r9/pitclaw-populated-r9.f3d'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    opt=app.importManager.createFusionArchiveImportOptions(str(source))
    doc=app.importManager.importToNewDocument(opt)
    doc.name='PitClaw stepped probe face - APPEARANCE CONCEPT'
    d=F.Design.cast(app.activeProduct)
    occ=list(d.rootComponent.occurrences);assert len(occ)==7
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,1,2,4,5,6]
    camera(app,(17,-20,16))
    assert app.activeViewport.saveAsImageFile(str(OUT/'before-probe-face.png'),1600,1200)
    ns=runpy.run_path(str(ENCLOSURE/'fusion-r9/support/build_fusion_r8.py'))
    c=occ[0].component
    assert c.bRepBodies.count==1

    def yz_prism(name,points,start_x,length,operation):
        sk=c.sketches.add(c.yZConstructionPlane);sk.name=name+' profile'
        # Transform model coordinates into the plane rather than guessing the
        # local YZ sketch axes. The extrusion normal is measured independently.
        p=[sk.modelToSketchSpace(C.Point3D.create(0,y/10,z/10)) for y,z in points]
        for a,b in zip(p,p[1:]+p[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(a,b)
        origin=sk.sketchToModelSpace(C.Point3D.create(0,0,0))
        zaxis=sk.sketchToModelSpace(C.Point3D.create(0,0,1))
        normal_sign=1 if zaxis.x-origin.x>0 else -1
        ext=c.features.extrudeFeatures.createInput(sk.profiles.item(0),operation)
        ext.startExtent=F.OffsetStartDefinition.create(ns['val'](start_x*normal_sign))
        direction=F.ExtentDirections.PositiveExtentDirection if normal_sign>0 else F.ExtentDirections.NegativeExtentDirection
        ext.setOneSideExtent(F.DistanceExtentDefinition.create(ns['val'](length)),direction)
        if operation==ns['CUT']:ext.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.extrudeFeatures.add(ext);f.name=name;sk.isLightBulbOn=False
        return f

    yz_prism('Remove deep lower probe-side overhang',
             [(-60,-1),(-44.5,-1),(-44.5,18.9),(-52,26.4),(-60,26.4)],-50,100,ns['CUT'])
    ns['rr'](c,'Concept flush lower probe wall',(0,-43.25),86,2.5,0,2.48,16.42,ns['JOIN'])
    inner=2.5*math.sqrt(2)
    yz_prism('Sloped shoulder below screen housing',
             [(-44.5,18.9),(-52,26.4),(-52+inner,26.4),(-44.5+inner,18.9)],
             -43,86,ns['JOIN'])
    # Preserve the original upper corner silhouette; the new roof may not extend
    # beyond the reviewed case's rounded outer perimeter.
    sk,f=ns['sketch'](c,'Keep existing outer rounded silhouette')
    ns['rounded'](sk,f,0,0,86,104,5)
    ext=c.features.extrudeFeatures.createInput(sk.profiles.item(0),F.FeatureOperations.IntersectFeatureOperation)
    ext.setOneSideExtent(F.DistanceExtentDefinition.create(ns['val'](27.6)),F.ExtentDirections.PositiveExtentDirection)
    ext.participantBodies=[c.bRepBodies.item(0)]
    feat=c.features.extrudeFeatures.add(ext);feat.name='Trim concept to original outer silhouette';sk.isLightBulbOn=False
    ns['circles'](c,'Concept close-fitting probe openings',[(-17,11.65),(0,11.65),(17,11.65)],
                  4.6,-44.52,2.56,ns['CUT'],'XZ')
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    c.name='CONCEPT bottom - assembly joint not yet designed'
    c.bRepBodies.item(0).name='Stepped probe-face appearance only'
    c.attributes.add('PitClaw','release_status','APPEARANCE CONCEPT ONLY. Split fascia and installation path need design. Do not print as a released enclosure.')
    for sk in c.sketches:sk.isLightBulbOn=False
    camera(app,(17,-20,16))
    assert app.activeViewport.saveAsImageFile(str(OUT/'stepped-probe-face.png'),1600,1200)
    camera(app,(20,0,2.245))
    assert app.activeViewport.saveAsImageFile(str(OUT/'stepped-side-profile.png'),1600,1000)
    camera(app,(9,-20,5))
    assert app.activeViewport.saveAsImageFile(str(OUT/'stepped-probe-detail.png'),1600,1100)
    camera(app,(17,-20,16))
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'stepped-probe-face-CONCEPT.f3d')))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    report={'status':'APPEARANCE CONCEPT ONLY','source_f3d_sha256':before,
            'source_unchanged':True,'new_face_y_mm':-44.5,'original_face_y_mm':-52,
            'face_inset_mm':7.5,'slope_start_z_mm':18.9,'slope_end_z_mm':26.4,
            'overall_envelope_mm':[104,86,44.9],
            'unchanged':'PCB and its placement, WT32 and its placement, four-anchor retainer, upper housing and power-side geometry.',
            'not_verified':'New fascia split/joint, installation/removal path, cable boots, print supports and structural strength.',
            'no_print_stl_exported':True}
    (OUT/'concept-notes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
