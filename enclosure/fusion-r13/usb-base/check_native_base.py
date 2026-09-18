"""Check USB-base seating, stops, screws, module descent and declared solder envelopes."""
import adsk.core as C, adsk.fusion as F
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent

def run(_context: str):
    app=C.Application.get();d=F.Design.cast(app.activeProduct);root=d.rootComponent
    assert root.occurrences.count==10
    base=root.occurrences.item(9).bRepBodies.item(0)
    mod=next(o for o in root.allOccurrences if o.name.startswith('MOD1 -'))
    board=next(b for b in mod.bRepBodies if b.name=='Adafruit5807 PCB')
    manager=F.TemporaryBRepManager.get()
    def overlap(a,b,dx=0,dy=0,dz=0):
        a=manager.copy(a);b=manager.copy(b)
        if dx or dy or dz:
            m=C.Matrix3D.create();m.translation=C.Vector3D.create(dx/10,dy/10,dz/10);assert manager.transform(a,m)
        if not a.boundingBox.intersects(b.boundingBox):return 0
        assert manager.booleanOperation(a,b,F.BooleanTypes.IntersectionBooleanType)
        return a.volume*1000 if a.faces.count and a.isSolid else 0
    def cylinder(u,v,dia,zlo,zhi):
        x,y=-4.34-u,25.362+v
        return manager.createCylinderOrCone(C.Point3D.create(x/10,y/10,zlo/10),dia/20,C.Point3D.create(x/10,y/10,zhi/10),dia/20)
    def box(u,v,w,h,zlo,zhi):
        bounds=C.OrientedBoundingBox3D.create(C.Point3D.create((-4.34-u)/10,(25.362+v)/10,(zlo+zhi)/20),C.Vector3D.create(1,0,0),C.Vector3D.create(0,1,0),w/10,h/10,(zhi-zlo)/10)
        return manager.createBox(bounds)
    fits={}
    for name,offset,blocked in [('nominal',(0,0,0),False),('seat_negative_control',(0,0,-.05),True),('rear_clearance',(0,-.2999,0),False),('rear_stop',(0,-.4,0),True),('left_clearance',(-.2999,0,0),False),('right_clearance',(.2999,0,0),False),('left_guide',(-.4,0,0),True),('right_guide',(.4,0,0),True)]:
        v=overlap(board,base,*offset);assert (v>1e-5) if blocked else (v<1e-5),(name,v)
        fits[name]={'offset_xyz_mm':offset,'intersection_mm3':v,'expected_contact':blocked}
    descent=[]
    for dz in [5,2,1,.5,.1,0]:
        v=sum(overlap(b,base,dz=dz) for b in mod.bRepBodies)
        assert v<1e-5,(dz,v)
        descent.append({'z_offset_mm':dz,'clash_mm3':v})
    solder=[]
    # Nominal pad outline plus0.3mm radial solder allowance; keep tails <=2.5mm.
    for u in (2.54,5.08,7.62,12.7,15.24,17.78):
        v=overlap(cylinder(u,2.54,1.6764+.6,9.6,12.1),base);assert v<1e-5
        solder.append({'kind':'header solder','uv_mm':[u,2.54],'diameter_mm':2.2764,'clash_mm3':v})
    for u in (8.36,11.86):
        v=overlap(cylinder(u,4.572,2.1844+.6,9.6,12.1),base);assert v<1e-5
        solder.append({'kind':'output solder','uv_mm':[u,4.572],'diameter_mm':2.7844,'clash_mm3':v})
    for u in (5.84,14.48):
        for v0 in (17.858,22.038):
            v=overlap(box(u,v0,1.6,2.6,9.6,12.1),base);assert v<1e-5,(u,v0,v)
            solder.append({'kind':'USB shell stake solder','uv_mm':[u,v0],'xy_mm':[1.6,2.6],'clash_mm3':v})
    for u in (7.27,13.05):
        v=overlap(cylinder(u,18.358,1.25,9.6,12.1),base);assert v<1e-5
        solder.append({'kind':'USB locating peg allowance','uv_mm':[u,18.358],'diameter_mm':1.25,'clash_mm3':v})
    screws=[]
    for u in (2.413,17.653):
        v=overlap(cylinder(u,20.955,2.0,9.09,13.31),base);assert v<1e-5
        screws.append({'eagle_u_mm':u,'nominal_M2_shaft_clash_mm3':v})
    result={'status':'PASS','seat_and_stop_checks':fits,'module_descent_checks':descent,'solder_and_peg_envelope_checks':solder,'screw_checks':screws,'seat_height_mm':3.0,'solder_tail_limit_below_module_mm':2.5,'tail_to_carrier_gap_mm':.5,'scope':'Geometric envelopes, not measured solder, clamp force, temperature or retention rating. M2 clamps carry extraction; curved front guides do not stop travel before the case pocket.'}
    (OUT/'native-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('USB base PASS:',len(fits),'seating/stop controls,',len(descent),'module descent poses,',len(solder),'solder/peg envelopes,',len(screws),'M2 shafts')
