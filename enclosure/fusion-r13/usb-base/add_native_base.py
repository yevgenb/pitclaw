"""Add the printed USB base to an imported R13 Fusion archive without modifying case solids.

Run once in Fusion on the four-part enclosure (nine root occurrences). The saved
archive contains the resulting editable feature history. Coordinates in mm.
"""
import adsk.core as C, adsk.fusion as F
import math,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
W,L,R=20.32,23.495,2.54
CX,CY,Z0=-14.5,25.362+23.495/2,9.1
NEW,JOIN,CUT=F.FeatureOperations.NewBodyFeatureOperation,F.FeatureOperations.JoinFeatureOperation,F.FeatureOperations.CutFeatureOperation

def val(v):return C.ValueInput.createByString(f'{v:.10g} mm')
def p(x,y):return C.Point3D.create(x/10,y/10,0)
def profile(sk,cx,cy,w,h,r=0):
    x0,x1=cx-w/2,cx+w/2;y0,y1=cy-h/2,cy+h/2
    lines=sk.sketchCurves.sketchLines
    if not r:lines.addTwoPointRectangle(p(x0,y0),p(x1,y1));return
    for a,b in [((x0+r,y0),(x1-r,y0)),((x1,y0+r),(x1,y1-r)),((x1-r,y1),(x0+r,y1)),((x0,y1-r),(x0,y0+r))]:lines.addByTwoPoints(p(*a),p(*b))
    for center,start in [((x1-r,y0+r),(x1-r,y0)),((x1-r,y1-r),(x1,y1-r)),((x0+r,y1-r),(x0+r,y1)),((x0+r,y0+r),(x0,y0+r))]:sk.sketchCurves.sketchArcs.addByCenterStartSweep(p(*center),p(*start),math.pi/2)
def extrude(c,sk,name,z0,z1,op,ring=False,participants=None):
    ps=C.ObjectCollection.create()
    for pr in sk.profiles:
        if not ring or pr.profileLoops.count==2:ps.add(pr)
    assert ps.count
    i=c.features.extrudeFeatures.createInput(ps,op)
    i.startExtent=F.OffsetStartDefinition.create(val(z0))
    i.setOneSideExtent(F.DistanceExtentDefinition.create(val(z1-z0)),F.ExtentDirections.PositiveExtentDirection)
    if participants is not None:i.participantBodies=participants
    elif op==CUT:i.participantBodies=list(c.bRepBodies)
    f=c.features.extrudeFeatures.add(i);f.name=name;sk.isLightBulbOn=False;return f

def rounded(c,name,w,h,r,z0,z1,op):
    sk=c.sketches.add(c.xYConstructionPlane);sk.name=name+' profile';profile(sk,CX,CY,w,h,r)
    return extrude(c,sk,name,z0,z1,op)
def rect(c,name,u0,u1,v0,v1,z0,z1,op,r=0,participants=None):
    sk=c.sketches.add(c.xYConstructionPlane);sk.name=name+' profile'
    profile(sk,-4.34-(u0+u1)/2,25.362+(v0+v1)/2,u1-u0,v1-v0,r)
    return extrude(c,sk,name,Z0+z0,Z0+z1,op,participants=participants)
def join_all(c,name):
    assert c.bRepBodies.count>1
    bodies=C.ObjectCollection.create()
    for b in list(c.bRepBodies)[1:]:bodies.add(b)
    i=c.features.combineFeatures.createInput(c.bRepBodies.item(0),bodies);i.operation=JOIN;i.isKeepToolBodies=False
    f=c.features.combineFeatures.add(i);f.name=name
    assert c.bRepBodies.count==1

def annulus(c,name,inner_offset,z0,z1,y_start=6.2):
    sk=c.sketches.add(c.xYConstructionPlane);sk.name=name+' profile'
    profile(sk,CX,CY,W+3,L+3,R+1.5)
    profile(sk,CX,CY,W+2*inner_offset,L+2*inner_offset,R+inner_offset)
    f=extrude(c,sk,name,Z0+z0,Z0+z1,NEW,ring=True)
    rect(c,name+' ends clear',-5,26,y_start,22.8,-1,6,F.FeatureOperations.IntersectFeatureOperation,participants=list(f.bodies))
    join_all(c,name+' join')

def run(_context: str):
    app=C.Application.get();d=F.Design.cast(app.activeProduct);root=d.rootComponent
    assert app.activeDocument.name.startswith('PitClaw enclosure r13')
    assert root.occurrences.count==9,'The base is already present, or this is not the baseline R13 assembly.'
    case_before={i:root.occurrences.item(i).component.bRepBodies.item(0).volume for i in (0,1,2,7)}
    pcb_matrix=root.occurrences.item(5).transform2.asArray()
    occ=root.occurrences.addNewComponent(C.Matrix3D.create());c=occ.component;c.name='05 Adafruit5807 printed base - 3mm seat'
    rounded(c,'Insulating floor',W,L,R,Z0,Z0+.8,NEW)
    f=rounded(c,'Rear bearing blank',W,L,R,Z0,Z0+3,NEW)
    rect(c,'Rear edge bearing strip',-1,W+1,0,1.1,-1,5,F.FeatureOperations.IntersectFeatureOperation,participants=list(f.bodies));join_all(c,'Rear bearing to floor')
    annulus(c,'Side and front bearing frame',-1.5,0,3,.9)
    annulus(c,'Side and curved front locating lips',.3,3,4.2)
    sk=c.sketches.add(c.xYConstructionPlane);sk.name='M2 compression pads profile'
    for u in (2.413,17.653):sk.sketchCurves.sketchCircles.addByCenterRadius(p(-4.34-u,25.362+20.955),.25)
    extrude(c,sk,'Two 3mm M2 compression pads',Z0,Z0+3,JOIN)
    for a,b in ((6.2,7.8),(12.9,14.5)):
        rect(c,f'Rear stop support {a}',a,b,-1.5,1.1,0,3,JOIN)
        rect(c,f'Rear stop {a}',a,b,-1.5,-.3,3,4.2,JOIN)
    rect(c,'Output solder and wire relief',.8,19.52,1.3,6.3,-.01,4.3,CUT,r=.3)
    for a,b in ((4.84,7.995),(12.325,15.48)):
        rect(c,f'USB solder and peg relief {a}',a,b,16.3,24,-.01,4.3,CUT,r=.3)
    sk=c.sketches.add(c.xYConstructionPlane);sk.name='M2 screw clearance profile'
    for u in (2.413,17.653):sk.sketchCurves.sketchCircles.addByCenterRadius(p(-4.34-u,25.362+20.955),.12)
    extrude(c,sk,'M2 through holes diameter2.4',Z0-.01,Z0+4.3,CUT)
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    c.bRepBodies.item(0).name='Adafruit5807 printed base spacer'
    # Improve only the reference module to the published R2.54 outline.
    mod=next(o.component for o in root.allOccurrences if o.name.startswith('MOD1 -'))
    board=next(b for b in mod.bRepBodies if b.name=='Adafruit5807 PCB')
    sk=mod.sketches.add(mod.xYConstructionPlane);sk.name='Published PCB corner trim profile'
    for sx in (-1,1):
        for sy in (-1,1):
            q=lambda x,y:p(CX+sx*x,CY+sy*y)
            hx,hy=W/2,L/2
            sk.sketchCurves.sketchArcs.addByCenterStartSweep(q(hx-R,hy-R),q(hx,hy-R),sx*sy*math.pi/2)
            sk.sketchCurves.sketchLines.addByTwoPoints(q(hx-R,hy),q(hx,hy))
            sk.sketchCurves.sketchLines.addByTwoPoints(q(hx,hy),q(hx,hy-R))
    extrude(mod,sk,'Published module PCB corner radius2.54',12.09,13.71,CUT,participants=[board])
    old=[b for b in mod.bRepBodies if b.name.startswith('3mm nylon spacer')]
    assert len(old)==2
    for b in old:mod.features.removeFeatures.add(b).name='Replaced nylon spacer with printed base'
    for i,v in case_before.items():assert abs(root.occurrences.item(i).component.bRepBodies.item(0).volume-v)<1e-12
    assert all(abs(a-b)<1e-12 for a,b in zip(pcb_matrix,root.occurrences.item(5).transform2.asArray()))
    c.attributes.add('PitClaw','part','Printable replacement for both nylon spacers and rear adhesive support; seat3mm, lips1.2mm above seat, PCB edge clearance0.3mm')
    assert d.activateRootComponent()
    for sk in c.sketches:sk.isLightBulbOn=False
    report={'seat_height_mm':3,'overall_height_mm':4.2,'floor_thickness_mm':.8,'wall_mm':1.2,'board_edge_clearance_mm':.3,'screw_clearance_mm':2.4,'board_corner_radius_mm':2.54,'base_volume_mm3':c.bRepBodies.item(0).volume*1000,'case_solids_unchanged':True,'pcb_transform_unchanged':True,'assembly_translation_from_print_mm':[-14.5,25.362,9.1]}
    (OUT/'usb-base/build-native.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
