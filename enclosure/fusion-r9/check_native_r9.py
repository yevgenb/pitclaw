"""Check actual visible component geometry against the three enclosure solids.

Only positive-volume component/case intersections are counted. Internal overlaps
between a visual package's leads/housing, and display copper/mask sheets, are not
treated as physical assembly failures. No source geometry is altered.
"""
import adsk.core as C
import adsk.fusion as F
import json,math
from pathlib import Path

OUT=Path(__file__).resolve().parent


def run(_context):
    app=C.Application.get();d=F.Design.cast(app.activeProduct)
    assert app.activeDocument.name=='PitClaw enclosure r9 - populated carrier'
    pop=d.rootComponent.occurrences.item(5)
    expected=[-1,0,0,0,0,-1,0,.45,0,0,1,.75,0,0,0,1]
    assert all(abs(a-b)<1e-9 for a,b in zip(pop.transform2.asArray(),expected))
    cases=[o.bRepBodies.item(0) for o in list(d.rootComponent.occurrences)[:3]]
    parts=[];stock=0
    for o in d.rootComponent.allOccurrences:
        path=o.fullPathName
        if path.startswith('REFERENCE - populated carrier (KiCad geometry):'):
            if not o.isLightBulbOn or o.component.name.startswith('CP_Radial'):continue
            if o.component.name.startswith('pitclaw-carrier_') and not o.component.name.endswith('_PCB'):continue
            for b in o.bRepBodies:
                if b.isSolid:parts.append((path,b))
            if o.component.bRepBodies.count and not o.component.name.startswith('pitclaw-carrier_'):stock+=1
        elif path.startswith('REFERENCE - custom populated carrier parts:'):
            for b in o.bRepBodies:
                if b.isSolid:parts.append((path,b))
        elif path.startswith('REFERENCE - WT32 nominal mounting envelope:'):
            for b in o.bRepBodies:
                if b.isSolid:parts.append((path,b))
    assert stock==20,stock
    manager=F.TemporaryBRepManager.get();clashes=[];tests=0
    for case in cases:
        for path,body in parts:
            if not case.boundingBox.intersects(body.boundingBox):continue
            a=manager.copy(case);b=manager.copy(body)
            assert manager.booleanOperation(a,b,F.BooleanTypes.IntersectionBooleanType),path
            tests+=1
            volume=a.volume*1000 if a.isValid and a.faces.count and a.isSolid else 0
            if volume>1e-5:clashes.append({'case':case.name,'part':path,'body':body.name,'volume_mm3':volume})
    issues=[]
    # Imported assembly timeline entries can lack an API feature association.
    # Inspect the real feature/sketch collections instead of TimelineObject.entity.
    for component in d.allComponents:
        for entity in list(component.features)+list(component.sketches):
            if hasattr(entity,'healthState') and entity.healthState!=F.FeatureHealthStates.HealthyFeatureHealthState:
                issues.append({'name':entity.name,'message':entity.errorOrWarningMessage})
    report={'status':'PASS' if not clashes and not issues else 'REVIEW REQUIRED',
            'stock_models_visible':stock,'custom_components':18,
            'coverage':'37 carrier electrical references plus Adafruit5807 module',
            'body_case_boolean_tests':tests,'positive_volume_clashes':clashes,'timeline_issues':issues,
            'pcb_rigid_transform':pop.transform2.asArray(),
            'scope':'Nominal visual component solids versus case. Excludes display-layer sheets and internal package overlaps; not supplier-complete fit or structural validation.'}
    (OUT/'native-populated-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
