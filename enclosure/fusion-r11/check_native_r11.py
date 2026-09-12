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
    assert app.activeDocument.name=='PitClaw enclosure r11 - bottom mounting inserts'
    pop=d.rootComponent.occurrences.item(5)
    expected=[-1,0,0,0,0,-1,0,.45,0,0,1,.75,0,0,0,1]
    assert all(abs(a-b)<1e-9 for a,b in zip(pop.transform2.asArray(),expected))
    case_occ=[d.rootComponent.occurrences.item(i) for i in (0,1,2,7)]
    cases=[o.bRepBodies.item(0) for o in case_occ]
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
    def overlap(a,b,dx=0,dy=0,dz=0):
        first=manager.copy(a);second=manager.copy(b)
        if dx or dy or dz:
            m=C.Matrix3D.create();m.translation=C.Vector3D.create(dx/10,dy/10,dz/10)
            assert manager.transform(first,m)
        if not first.boundingBox.intersects(second.boundingBox):return 0
        assert manager.booleanOperation(first,second,F.BooleanTypes.IntersectionBooleanType)
        return first.volume*1000 if first.faces.count and first.isSolid else 0
    for n,a in enumerate(cases):
        for b in cases[n+1:]:
            v=overlap(a,b)
            if v>1e-5:clashes.append({'case':a.name,'part':b.name,'volume_mm3':v})
    for case in cases:
        for path,body in parts:
            if not case.boundingBox.intersects(body.boundingBox):continue
            a=manager.copy(case);b=manager.copy(body)
            assert manager.booleanOperation(a,b,F.BooleanTypes.IntersectionBooleanType),path
            tests+=1
            volume=a.volume*1000 if a.faces.count and a.isSolid else 0
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
    fascia=cases[3];bottom=cases[0];top=cases[1]
    report['retention_tests']={
        'outward_0_5mm_blocked_by_lid_volume_mm3':overlap(fascia,top,dy=-.5),
        'inward_0_5mm_blocked_by_bottom_stop_volume_mm3':overlap(fascia,bottom,dy=.5),
        'upward_1mm_blocked_by_closed_lid_volume_mm3':overlap(fascia,top,dz=1)}
    assert all(v>1e-5 for v in report['retention_tests'].values()),report['retention_tests']
    report['allowed_fascia_lift_0_2999mm_clash_volume_mm3']=overlap(fascia,top,dz=.2999)
    assert report['allowed_fascia_lift_0_2999mm_clash_volume_mm3']<1e-5
    path=[]
    for dy in [-12,-9,-6,-3,-1,-.5,-.25,0]:
        v=overlap(fascia,bottom,dy=dy)
        for _,body in parts:v+=overlap(fascia,body,dy=dy)
        path.append({'fascia_offset_y_mm':dy,'case_component_clash_volume_mm3':v})
    report['native_fascia_path_spot_checks']=path
    assert max(v['case_component_clash_volume_mm3'] for v in path)<1e-5,path
    inserts=list(d.rootComponent.occurrences.item(8).bRepBodies)
    assert len(inserts)==4
    mount_tests=[]
    for x in (-36,36):
        for y in (-37,37):
            shaft=manager.createCylinderOrCone(C.Point3D.create(x/10,y/10,-.01),.16,
                C.Point3D.create(x/10,y/10,.75),.16)
            tool=manager.createCylinderOrCone(C.Point3D.create(x/10,y/10,.75001),.4,
                C.Point3D.create(x/10,y/10,3.5),.4)
            shaft_clash=overlap(shaft,bottom)
            for _,body in parts:shaft_clash+=overlap(shaft,body)
            tool_clash=overlap(tool,bottom)
            assert shaft_clash<1e-5 and tool_clash<1e-5,(x,y,shaft_clash,tool_clash)
            mount_tests.append({'centre_mm':[x,y],'screw_shaft_diameter_mm':3.2,
                'screw_shaft_z_mm':[-.1,7.5],'screw_clearance_clash_mm3':shaft_clash,
                'working_tool_diameter_mm':8,'working_tool_z_mm':[7.5001,35],
                'tool_vs_empty_bottom_clash_mm3':tool_clash})
    floor=manager.copy(bottom)
    slab=manager.createBox(C.OrientedBoundingBox3D.create(C.Point3D.create(0,0,.125),
        C.Vector3D.create(1,0,0),C.Vector3D.create(0,1,0),20,20,.25))
    assert manager.booleanOperation(floor,slab,F.BooleanTypes.IntersectionBooleanType)
    capture=[]
    for insert in inserts:
        v=sum(overlap(insert,b) for _,b in parts)+sum(overlap(insert,b) for b in cases[1:])
        nominal=overlap(insert,floor)
        displaced=overlap(insert,floor,dz=-1.5)
        assert v<1e-5 and nominal<1e-5 and displaced>1e-5,(v,nominal,displaced)
        capture.append({'insert_vs_electronics_and_other_shells_clash_mm3':v,
            'nominal_insert_floor_clash_mm3':nominal,
            'insert_displaced_outward_1_5mm_blocked_by_floor_mm3':displaced})
    report['mounting_hardware_checks']=mount_tests
    report['insert_secondary_capture_checks']=capture
    report['mount_check_scope']='The insert/pilot press-fit and screw/thread overlap are intentional. Tool access assumes the empty bottom before electronics and a straight 8mm working envelope. Floor capture is secondary after insert movement; no pull-out or load rating.'
    assert not clashes and not issues,report
    (OUT/'native-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
