"""Run inside the completed Fusion r8 document to validate, export and preview."""
import adsk.core as C
import adsk.fusion as F
import hashlib
import json
from pathlib import Path
import runpy

OUT=Path(__file__).resolve().parent


def run(_context):
    ns=runpy.run_path(str(OUT/'build_fusion.py'))
    app,d=ns['setup']()
    occurrences=list(d.rootComponent.occurrences)
    assert len(occurrences)==5
    assert all(o.component.bRepBodies.count==1 for o in occurrences)
    e=C.ObjectCollection.create()
    for o in occurrences:e.add(o)
    i=d.createInterferenceInput(e);i.areCoincidentFacesIncluded=False
    r=d.analyzeInterference(i)
    assert r.count==0, f'{r.count} native interference results'
    issues=[]
    for t in d.timeline:
        entity=t.entity
        if hasattr(entity,'healthState') and entity.healthState!=F.FeatureHealthStates.HealthyFeatureHealthState:
            issues.append({'name':entity.name,'message':entity.errorOrWarningMessage})
    assert not issues,issues
    (OUT/'native-stl').mkdir(exist_ok=True)
    (OUT/'step').mkdir(exist_ok=True)
    for o,part in zip(occurrences[:3],['bottom','top','retainer']):
        options=d.exportManager.createSTLExportOptions(o.component,str(OUT/'native-stl'/f'carrier-{part}.stl'))
        options.unitType=F.DistanceUnits.MillimeterDistanceUnits
        options.isBinaryFormat=True
        options.meshRefinement=F.MeshRefinementSettings.MeshRefinementHigh
        options.surfaceDeviation=.0005  # centimeters: 0.005 mm
        options.sendToPrintUtility=False
        assert d.exportManager.execute(options)
        options=d.exportManager.createSTEPExportOptions(str(OUT/'step'/f'carrier-{part}.step'),o.component)
        assert d.exportManager.execute(options)
    ns['camera'](app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-assembled.png'),1600,1200)
    original=[o.transform2.copy() for o in occurrences]
    for o,m,z in zip(occurrences,original,[0,7,2.5,1,4.5]):
        m=m.copy();m.translation=C.Vector3D.create(0,0,z);o.transform2=m
    ns['camera'](app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-exploded.png'),1600,1400)
    for o,m in zip(occurrences,original):o.transform2=m
    # A second native check verifies that all assembly positions were restored.
    e=C.ObjectCollection.create()
    for o in d.rootComponent.occurrences:e.add(o)
    i=d.createInterferenceInput(e);i.areCoincidentFacesIncluded=False
    assert d.analyzeInterference(i).count==0
    for o in occurrences[1:]:o.isLightBulbOn=False
    ns['camera'](app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-bottom.png'),1400,1100)
    for o in occurrences:o.isLightBulbOn=False
    occurrences[2].isLightBulbOn=True
    ns['camera'](app)
    assert app.activeViewport.saveAsImageFile(str(OUT/'fusion-retainer.png'),1400,1100)
    for o in occurrences:o.isLightBulbOn=True
    ns['camera'](app)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'pitclaw-enclosure-r8.f3d')))
    report={'status':'PASS: native CAD geometry; fit prototype', 'fusion_version':app.version,
            'native_interferences':0,'coincident_faces_excluded':True,'timeline_issues':issues,
            'timeline_entries':d.timeline.count,
            'insert_pilot_linked_dimensions':sum(1 for p in d.allParameters if p.expression=='insert_pilot'),
            'components':[],
            'material_status':'Print material remains undecided. Display appearances are illustrative; default physical material must not be used for mass or structural analysis.',
            'scope':'Three native enclosure solids and two labeled nominal electronics references. Populated-carrier swept checks are in the separate reference report; no physical or strength test.'}
    for o in occurrences:
        b=o.component.bRepBodies.item(0)
        report['components'].append({'name':o.component.name,'is_solid':b.isSolid,'volume_mm3':b.volume*1000,
            'faces':b.faces.count,'bounds_mm':[[p.x*10,p.y*10,p.z*10] for p in [b.boundingBox.minPoint,b.boundingBox.maxPoint]]})
    report['f3d_sha256']=hashlib.sha256((OUT/'pitclaw-enclosure-r8.f3d').read_bytes()).hexdigest()
    (OUT/'native-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
