"""Build the PitClaw enclosure as native Fusion sketches and solid features.

Run inside Fusion's Python API. build('bottom'), build('top'), build('retainer').
Coordinates below are millimeters, converted to Fusion's internal centimeters.
Named Fusion parameters drive axial depths/datums. Sketch XY geometry is editable
in the named sketches; changing the Python dimensions requires rebuilding.
This is a fit prototype. No measured strength or physical fit is implied.
"""
import adsk.core as C
import adsk.fusion as F
import math
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DOC = 'PitClaw enclosure r8 - four-anchor retainer'
CLOSURE = [(x,y) for x in (-38,38) for y in (-28,28)]
ANCHORS = [(x,y) for x in (-35.5,35.5) for y in (-40,40)]
CARRIER = [(x,y) for x in (-25.5,25.5) for y in (-37,21)]
OEM = [(x,y) for x in (-25.695,25.695) for y in (-39.48,35.66)]
PD = [(6.753,46.317),(21.993,46.317)]
NEW, JOIN, CUT = F.FeatureOperations.NewBodyFeatureOperation, F.FeatureOperations.JoinFeatureOperation, F.FeatureOperations.CutFeatureOperation


def val(v):
    return C.ValueInput.createByString(v if isinstance(v,str) else f'{v:.9g} mm')


def setup():
    app=C.Application.get()
    assert app.activeDocument.name==DOC, 'Activate the dedicated PitClaw r8 document.'
    d=F.Design.cast(app.activeProduct)
    d.unitsManager.distanceDisplayUnits=F.DistanceUnits.MillimeterDistanceUnits
    values={'floor_t':'2.5 mm','carrier_standoff':'5 mm',
            'seam_z':'27.6 mm','case_h':'44.9 mm','retainer_t':'2.5 mm',
            'retainer_top':'32.6 mm','retainer_bottom':'retainer_top-retainer_t',
            'insert_pilot':'4 mm','insert_depth':'5 mm','lip_h':'2 mm'}
    for n,v in values.items():
        if not d.userParameters.itemByName(n):
            d.userParameters.add(n,val(v),'mm','PitClaw r8 nominal assembly datum; recheck fit after editing')
    return app,d


def component(d,name):
    assert not any(o.component.name==name for o in d.rootComponent.occurrences), 'Component already exists; do not duplicate.'
    occ=d.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
    occ.component.name=name
    return occ.component


def point(x,y):
    return C.Point3D.create(x/10,y/10,0)


def sketch(comp,name,axis='XY',z=None):
    plane=comp.xYConstructionPlane if axis=='XY' else comp.xZConstructionPlane
    if z is not None:
        i=comp.constructionPlanes.createInput()
        i.setByOffset(plane,val(z))
        plane=comp.constructionPlanes.add(i)
        plane.name=name+' plane'
        plane.isLightBulbOn=False
    sk=comp.sketches.add(plane)
    sk.name=name+' profile'
    # Fusion's XZ sketch has local +Y in global -Z and normal in global +Y.
    return sk, (-1 if axis=='XZ' else 1)


def rounded(sk,flip,x,y,w,h,r):
    def p(a,b): return point(a,flip*b)
    lines=sk.sketchCurves.sketchLines
    arcs=sk.sketchCurves.sketchArcs
    x0,x1=x-w/2,x+w/2; y0,y1=y-h/2,y+h/2
    if not r:
        lines.addTwoPointRectangle(p(x0,y0),p(x1,y1)); return
    pairs=[((x0+r,y0),(x1-r,y0)),((x1,y0+r),(x1,y1-r)),
           ((x1-r,y1),(x0+r,y1)),((x0,y1-r),(x0,y0+r))]
    for a,b in pairs: lines.addByTwoPoints(p(*a),p(*b))
    for center,start in [((x1-r,y0+r),(x1-r,y0)),((x1-r,y1-r),(x1,y1-r)),
                         ((x0+r,y1-r),(x0+r,y1)),((x0+r,y0+r),(x0,y0+r))]:
        arcs.addByCenterStartSweep(p(*center),p(*start),flip*math.pi/2)


def profiles(sk,ring=False):
    ps=[p for p in sk.profiles if not ring or p.profileLoops.count==2]
    assert ps, 'No closed profile in '+sk.name
    obj=C.ObjectCollection.create()
    for p in ps: obj.add(p)
    return obj


def extrude(comp,sk,name,start,length,operation,ring=False):
    i=comp.features.extrudeFeatures.createInput(profiles(sk,ring),operation)
    i.startExtent=F.OffsetStartDefinition.create(val(start))
    i.setOneSideExtent(F.DistanceExtentDefinition.create(val(length)),F.ExtentDirections.PositiveExtentDirection)
    if operation==CUT:
        i.participantBodies=[b for b in comp.bRepBodies]
    feat=comp.features.extrudeFeatures.add(i)
    feat.name=name
    sk.isLightBulbOn=False
    print('FEATURE',comp.name,name)
    return feat


def rr(comp,name,xy,w,h,r,start,length,op,axis='XY'):
    sk,f=sketch(comp,name,axis)
    rounded(sk,f,*xy,w,h,r)
    return extrude(comp,sk,name,start,length,op)


def ring(comp,name,outer,inner,r,start,length,op):
    sk,f=sketch(comp,name)
    rounded(sk,f,0,0,*outer,r)
    rounded(sk,f,0,0,*inner,max(r-1,.4))
    return extrude(comp,sk,name,start,length,op,True)


def circles(comp,name,points,diameter,start,length,op,axis='XY'):
    sk,f=sketch(comp,name,axis)
    diameter_mm=(F.Design.cast(C.Application.get().activeProduct).unitsManager.evaluateExpression(diameter,'mm')*10
                 if isinstance(diameter,str) else diameter)
    for x,y in points:
        circle=sk.sketchCurves.sketchCircles.addByCenterRadius(point(x,f*y),diameter_mm/20)
        if isinstance(diameter,str):
            dim=sk.sketchDimensions.addDiameterDimension(circle,point(x+diameter_mm/2+2,f*y+2))
            dim.parameter.expression=diameter
    return extrude(comp,sk,name,start,length,op)


def bottom(d):
    c=component(d,'01 Bottom shell')
    rr(c,'Outer shell',(0,0),86,104,5,0,'seam_z',NEW)
    rr(c,'Open cavity',(0,0),81,99,2.5,'floor_t','seam_z',CUT)
    circles(c,'Four carrier insert bosses',CARRIER,9,'floor_t','carrier_standoff',JOIN)
    circles(c,'Four case closure columns',CLOSURE,9,'floor_t','seam_z-floor_t',JOIN)
    rr(c,'USB recess internal backing',(14.5,15.7),20,10,2,48.5,1.02,JOIN,'XZ')
    circles(c,'Carrier insert pilots',CARRIER,'insert_pilot','floor_t','insert_depth+0.02 mm',CUT)
    circles(c,'Closure insert pilots',CLOSURE,'insert_pilot','seam_z-insert_depth','insert_depth+0.02 mm',CUT)
    circles(c,'Three probe access holes',[(-17,11.65),(0,11.65),(17,11.65)],10.5,-57,10,CUT,'XZ')
    rr(c,'RJ45 fitted opening',(-20.5,15.855),16.75,14.51,.2,47,10,CUT,'XZ')
    rr(c,'Barrel fitted opening',(-3.5,14.65),10,12.1,.2,47,10,CUT,'XZ')
    rr(c,'USB fitted shell aperture',(14.5,15.35),10.14,4.7,.4,47,10,CUT,'XZ')
    rr(c,'USB shallow external recess',(14.5,15.7),20,10,2,50,2.02,CUT,'XZ')
    rr(c,'Hidden carrier edge channel',(0,50.24),61,1.52,0,7,2.9,CUT)
    rr(c,'Hidden USB PCB edge clearance',(14.5,(48.48+49.057)/2),20.72,49.057-48.48,0,11.3,3.5,CUT)
    circles(c,'Hidden USB spacer and head clearances',PD,5.4,8.3,8.5,CUT)
    for x in (-28,26):
        rr(c,'Power edge support '+str(x),(x+1.5,49.85),3,1.3,0,'floor_t','carrier_standoff',JOIN)
    return c


def top(d):
    c=component(d,'02 Top bezel - four anchors')
    rr(c,'Top outer cup',(0,0),86,104,5,'seam_z','case_h-seam_z',NEW)
    rr(c,'Top inner cavity',(0,0),81,99,2.5,'seam_z-0.02 mm','case_h-3 mm-seam_z+0.02 mm',CUT)
    ring(c,'Locating lip connecting shoulder',(86,104),(78,96),5,'seam_z',1,JOIN)
    ring(c,'Locating lip',(80.4,98.4),(78,96),2,'seam_z-lip_h','lip_h+0.02 mm',JOIN)
    circles(c,'Lip relief around closure columns',CLOSURE,10,'seam_z-lip_h-0.02 mm','lip_h+0.02 mm',CUT)
    circles(c,'Four independent closure columns',CLOSURE,9,'seam_z','case_h-seam_z',JOIN)
    circles(c,'Four display retainer hard stops',ANCHORS,9,'retainer_top','case_h-retainer_top',JOIN)
    rr(c,'Display body and glass pocket',(0,0),61.2,93.2,1.5,'seam_z-0.02 mm',16.12,CUT)
    rr(c,'Active display window',(0,0),50.6,75.1,1,43.68,1.24,CUT)
    # A native loft creates the small front rim bevel. Circular corner arcs replace
    # the SCAD polygon approximation (its nonuniformly scaled radii differ <.01mm).
    s0,f=sketch(c,'Front window bevel start',z=44.4)
    rounded(s0,f,0,0,50.6,75.1,1)
    s1,f=sketch(c,'Front window bevel end',z=44.92)
    rounded(s1,f,0,0,51.359,75.851,1.01)
    i=c.features.loftFeatures.createInput(CUT)
    i.loftSections.add(s0.profiles.item(0)); i.loftSections.add(s1.profiles.item(0))
    i.participantBodies=[b for b in c.bRepBodies]
    feat=c.features.loftFeatures.add(i); feat.name='Front window comfort bevel'
    s0.isLightBulbOn=False; s1.isLightBulbOn=False
    circles(c,'Case screw clearance holes',CLOSURE,3.4,'seam_z-0.02 mm','case_h-seam_z+0.04 mm',CUT)
    circles(c,'Case screw head recesses',CLOSURE,6.4,'case_h-3.2 mm',3.22,CUT)
    circles(c,'Four retainer insert pilots',ANCHORS,'insert_pilot','retainer_top-0.02 mm','insert_depth+0.02 mm',CUT)
    rr(c,'Retainer insertion relief',(0,0),70.8,97,1,'seam_z-lip_h-0.02 mm','lip_h+1.04 mm',CUT)
    circles(c,'Four anchor pad insertion reliefs',ANCHORS,10,'seam_z-lip_h-0.02 mm','lip_h+1.04 mm',CUT)
    return c


def tab_hull(sk,x,y):
    # Analytic convex hull of the OEM Ø6.4 pad and Ø1.6 rail tie-in.
    a,b=sorted([(x,3.2),(-32 if x<0 else 32,.8)])
    xl,rl=a; xr,rr=b
    theta=math.acos((rl-rr)/(xr-xl))
    co,si=math.cos(theta),math.sin(theta)
    ul=(xl+rl*co,y+rl*si); ur=(xr+rr*co,y+rr*si)
    ll=(xl+rl*co,y-rl*si); lr=(xr+rr*co,y-rr*si)
    sk.sketchCurves.sketchLines.addByTwoPoints(point(*ul),point(*ur))
    sk.sketchCurves.sketchArcs.addByCenterStartSweep(point(xr,y),point(*ur),-2*theta)
    sk.sketchCurves.sketchLines.addByTwoPoints(point(*lr),point(*ll))
    sk.sketchCurves.sketchArcs.addByCenterStartSweep(point(xl,y),point(*ll),-(2*math.pi-2*theta))


def retainer(d):
    c=component(d,'03 WT32 retainer - four anchors')
    ring(c,'Thin perimeter frame',(70,96),(60.8,92.8),1,'retainer_bottom','retainer_t',NEW)
    sk,f=sketch(c,'Four OEM mounting pads and rail ties')
    for x,y in OEM: tab_hull(sk,x,y)
    extrude(c,sk,'Four OEM mounting pads and rail ties','retainer_bottom','retainer_t',JOIN)
    circles(c,'Four case anchor pads',ANCHORS,9,'retainer_bottom','retainer_t',JOIN)
    circles(c,'Closure column scallops',CLOSURE,10,'retainer_bottom-0.02 mm','retainer_t+0.04 mm',CUT)
    circles(c,'WT32 rear blind boss screw clearances',OEM,2.8,'retainer_bottom-0.02 mm','retainer_t+0.04 mm',CUT)
    circles(c,'Four M3 anchor screw clearances',ANCHORS,3.4,'retainer_bottom-0.02 mm','retainer_t+0.04 mm',CUT)
    return c


def build(stage):
    app,d=setup()
    c={'bottom':bottom,'top':top,'retainer':retainer}[stage](d)
    assert c.bRepBodies.count==1, f'{stage}: expected one solid, found {c.bRepBodies.count}'
    b=c.bRepBodies.item(0)
    assert b.isSolid
    b.name=c.name
    c.attributes.add('PitClaw','source','Native sketches/extrudes; r8 four-anchor design')
    for p in c.constructionPlanes: p.isLightBulbOn=False
    for s in c.sketches: s.isLightBulbOn=False
    app.activeViewport.fit()
    result={'stage':stage,'component':c.name,'body_count':c.bRepBodies.count,
            'volume_mm3':b.volume*1000,'timeline_count':d.timeline.count,
            'bounds_mm':[[v*10 for v in (p.x,p.y,p.z)] for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]}
    (OUT/f'build-{stage}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    export=d.exportManager.createFusionArchiveExportOptions(str(OUT/'pitclaw-enclosure-r8.f3d'))
    assert d.exportManager.execute(export)


def color_body(d,b,name,rgb):
    a=d.appearances.itemByName(name)
    if not a:
        source=C.Application.get().materialLibraries.itemByName('Fusion Appearance Library').appearances.itemByName('Plastic - Matte (Gray)')
        a=d.appearances.addByCopy(source,name)
        colors=[p for p in a.appearanceProperties if p.objectType=='adsk::core::ColorProperty']
        assert colors
        for p in colors: p.value=C.Color.create(*rgb,255)
    b.appearance=a


def references(d):
    c=component(d,'REFERENCE - bare carrier PCB only')
    rr(c,'Nominal carrier outline',(0,4.5),60,92,0,7.5,1.6,NEW)
    circles(c,'Carrier mounting holes',CARRIER,3.2,7.48,1.64,CUT)
    b=c.bRepBodies.item(0); b.name='Carrier PCB - placed components omitted'
    color_body(d,b,'Reference PCB green',(43,117,76))
    c.attributes.add('PitClaw','scope','Nominal board only; populated-carrier checks are in the independent reference report.')
    c=component(d,'REFERENCE - WT32 nominal mounting envelope')
    rr(c,'Display glass outline',(0,0),60,92,1.5,41.95,1.45,NEW)
    rr(c,'Active display area',(0,0),49.56,74.04,1,43.4,.03,NEW)
    ring(c,'Display frame envelope',(60,92),(53,82),1.5,38.6,3.35,NEW)
    rr(c,'Display rear PCB envelope',(0,0),48,70,0,32.6,1.6,NEW)
    circles(c,'Four rear mounting boss envelopes',OEM,5.8,32.6,6,NEW)
    for i,b in enumerate(c.bRepBodies):
        color_body(d,b,'Display active blue' if i==1 else 'Display frame charcoal',(30,92,123) if i==1 else (43,47,51))
    tool_bodies=C.ObjectCollection.create()
    for b in list(c.bRepBodies)[1:]: tool_bodies.add(b)
    ci=c.features.combineFeatures.createInput(c.bRepBodies.item(0),tool_bodies)
    ci.operation=JOIN; ci.isKeepToolBodies=False
    cf=c.features.combineFeatures.add(ci); cf.name='Unify overlapping reference envelopes'
    b=c.bRepBodies.item(0); b.name='WT32 nominal envelope - sample verification required'
    b.appearance=d.appearances.itemByName('Display frame charcoal')
    for face in b.faces:
        box=face.boundingBox
        if abs(box.minPoint.z-4.343)<.00001 and abs(box.maxPoint.z-4.343)<.00001:
            face.appearance=d.appearances.itemByName('Display active blue')
    c.attributes.add('PitClaw','scope','Nominal envelopes only; actual blind bosses, glass preload, rear parts and cables need measurement.')


def camera(app):
    cam=app.activeViewport.camera
    cam.cameraType=C.CameraTypes.OrthographicCameraType
    cam.eye=C.Point3D.create(-17,14,20)
    cam.target=C.Point3D.create(0,0,2.245)
    cam.upVector=C.Vector3D.create(0,0,1)
    cam.isFitView=True
    cam.isSmoothTransition=False
    app.activeViewport.camera=cam
    app.activeViewport.refresh()


def finish():
    app,d=setup()
    # Bind insert diameter dimensions when finishing an incrementally built model.
    for o in d.rootComponent.occurrences:
        for sk in o.component.sketches:
            if 'insert pilots profile' in sk.name and sk.sketchDimensions.count==0:
                for circle in sk.sketchCurves.sketchCircles:
                    p=circle.centerSketchPoint.geometry
                    dim=sk.sketchDimensions.addDiameterDimension(circle,C.Point3D.create(p.x+.4,p.y+.2,0))
                    dim.parameter.expression='insert_pilot'
    unused=d.userParameters.itemByName('wall_t')
    if unused: unused.deleteMe()
    colors=[('Case bottom slate',(72,91,106)),('Case top orange',(229,136,52)),('Retainer light gray',(175,187,192))]
    for o,(name,rgb) in zip(d.rootComponent.occurrences,colors):
        color_body(d,o.component.bRepBodies.item(0),name,rgb)
    references(d)
    for o in d.rootComponent.occurrences:
        for sk in o.component.sketches: sk.isLightBulbOn=False
    camera(app)
    print('Finished native model, references and appearances.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'pitclaw-enclosure-r8.f3d')))


def run(_context):
    app=C.Application.get()
    doc=app.documents.add(C.DocumentTypes.FusionDesignDocumentType)
    doc.name=DOC
    F.Design.cast(app.activeProduct).designType=F.DesignTypes.ParametricDesignType
    for stage in ('bottom','top','retainer'): build(stage)
    finish()
