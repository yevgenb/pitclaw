"""Native Fusion r10: relieved probe pocket in a lid-captured sliding fascia.

Creates a new document from r9. Retains all populated-carrier references and
the physical PCB placement. Units below are mm; helpers convert to Fusion cm.
"""
import adsk.core as C
import adsk.fusion as F
import json,runpy,hashlib
from pathlib import Path

OUT=Path(__file__).resolve().parent
H=runpy.run_path(str(OUT/'support/geometry_helpers.py'))
JOIN,CUT,NEW=H['JOIN'],H['CUT'],H['NEW']
INTERSECT=F.FeatureOperations.IntersectFeatureOperation


def box(c,name,x0,x1,y0,y1,z0,z1,op):
    sk,f=H['sketch'](c,name)
    H['rounded'](sk,f,(x0+x1)/2,(y0+y1)/2,x1-x0,y1-y0,0)
    i=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
    i.startExtent=F.OffsetStartDefinition.create(H['val'](z0))
    i.setOneSideExtent(F.DistanceExtentDefinition.create(H['val'](z1-z0)),F.ExtentDirections.PositiveExtentDirection)
    if op in (CUT,INTERSECT):i.participantBodies=list(c.bRepBodies)
    feat=c.features.extrudeFeatures.add(i);feat.name=name;sk.isLightBulbOn=False
    return feat


def run(_context):
    app=C.Application.get()
    source=OUT.parent/'fusion-r9/pitclaw-populated-r9.f3d'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    doc.name='PitClaw enclosure r10 - reinforced probe insert'
    d=F.Design.cast(app.activeProduct)
    occ=list(d.rootComponent.occurrences);assert len(occ)==7
    for n,o in enumerate(occ):o.isLightBulbOn=n in [0,1,2,4,5,6]
    c=occ[0].component
    # The relieved lower entry is1mm lower; the inner opening and jack planes stay.
    H['rr'](c,'Probe recess backing',(0,11.65),64,20,4,-52,9.5,JOIN,'XZ')
    sections=[]
    for name,y,w,h,z,r in [('Outer lip with cable clearance',-52.02,60,19,11.15,5.5),
                         ('Probe pocket floor',-44.5,50,12,11.65,3)]:
        sk,f=H['sketch'](c,name,axis='XZ',z=y)
        H['rounded'](sk,f,0,z,w,h,r);sections.append(sk)
    i=c.features.loftFeatures.createInput(CUT)
    for sk in sections:i.loftSections.add(sk.profiles.item(0))
    i.participantBodies=[c.bRepBodies.item(0)]
    feat=c.features.loftFeatures.add(i);feat.name='Relieved rounded probe pocket'
    for sk in sections:sk.isLightBulbOn=False
    # Independent panel carries the complete lower lip; no fixed sill blocks it.
    panel_occ=d.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
    p=panel_occ.component;p.name='04 Sliding probe fascia'
    copied=c.bRepBodies.item(0).copyToComponent(panel_occ)
    assert copied and p.bRepBodies.count==1,'Fascia body copy failed'
    box(p,'Fascia boundary',-33,33,-53,-42.5,0,27.3,INTERSECT)
    box(c,'Open probe end for carrier installation',-33.3,33.3,-53,-42,-.02,27.62,CUT)
    for sign in (-1,1):
        def xs(a,b):return (a,b) if sign>0 else (-b,-a)
        x0,x1=xs(33.3,39)
        box(c,f'Open guide block {sign}',x0,x1,-52,-40.5,0,8,JOIN)
    # Trim the outer edges of the guides to the original corner outline.
    sk,f=H['sketch'](c,'Original rounded case perimeter')
    H['rounded'](sk,f,0,0,86,104,5)
    i=c.features.extrudeFeatures.createInput(sk.profiles.item(0),INTERSECT)
    i.setOneSideExtent(F.DistanceExtentDefinition.create(H['val'](27.6)),F.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[c.bRepBodies.item(0)]
    feat=c.features.extrudeFeatures.add(i);feat.name='Guide corner trim';sk.isLightBulbOn=False
    for sign in (-1,1):
        def xs(a,b):return (a,b) if sign>0 else (-b,-a)
        x0,x1=xs(32.7,36.3)
        box(c,f'Open-top guide channel {sign}',x0,x1,-52.1,-43,3.8,8.1,CUT)
        x0,x1=xs(31,33)
        box(p,f'Fascia side web {sign}',x0,x1,-52,-42.5,2.48,8,JOIN)
        x0,x1=xs(32.7,36)
        box(p,f'Sliding runner {sign}',x0,x1,-52,-43,3.8,5.8,JOIN)
        box(p,f'Guide entry cover {sign}',x0,x1,-52,-50.7,5.8,7.8,JOIN)
        x0,x1=xs(29,31.3)
        box(p,f'Keeper support web {sign}',x0,x1,-49.5,-45.5,18,25,JOIN)
    for x in (-21,21):
        box(p,f'Reinforced keeper block {x}',x-9.3,x+9.3,-52,-45.5,20.8,25,JOIN)
        # This MUST remain open all the way through the fascia's upper edge.
        box(p,f'Open keeper notch {x}',x-6.3,x+6.3,-50.85,-48.25,20.78,27.32,CUT)
    H['circles'](p,'Three probe clearance bores',[(-17,11.65),(0,11.65),(17,11.65)],5.6,-44.52,2.04,CUT,'XZ')
    for x in (-17,0,17):
        sections=[]
        for suffix,y,diam in [('inner',-43.1,5.6),('rear',-42.48,6.4)]:
            sk,f=H['sketch'](p,f'Probe{x} lead-in {suffix}',axis='XZ',z=y)
            sk.sketchCurves.sketchCircles.addByCenterRadius(H['point'](x,f*11.65),diam/20)
            sections.append(sk)
        i=p.features.loftFeatures.createInput(CUT)
        for sk in sections:i.loftSections.add(sk.profiles.item(0))
        i.participantBodies=[p.bRepBodies.item(0)]
        feat=p.features.loftFeatures.add(i);feat.name=f'Probe{x} rear lead-in'
        for sk in sections:sk.isLightBulbOn=False
    top=occ[1].component
    for x in (-21,21):
        box(top,f'Keeper root web {x}',x-6,x+6,-51.5,-48.5,27.6,29.6,JOIN)
        box(top,f'Wide fascia key {x}',x-6,x+6,-50.6,-48.5,23.4,28.6,JOIN)
        sections=[]
        for suffix,z,w,h in [('tip',23,11.2,1.3),('full section',23.4,12,2.1)]:
            sk,f=H['sketch'](top,f'Key {x} entry {suffix}',z=z)
            H['rounded'](sk,f,x,-49.55,w,h,0);sections.append(sk)
        i=top.features.loftFeatures.createInput(JOIN)
        for sk in sections:i.loftSections.add(sk.profiles.item(0))
        feat=top.features.loftFeatures.add(i);feat.name=f'Key {x} 0.4mm entry chamfer'
        for sk in sections:sk.isLightBulbOn=False
    c.name='01 Bottom shell - open probe guides'
    top.name='02 Top bezel - reinforced fascia keys'
    for part in (c,top,p):
        assert part.bRepBodies.count==1 and part.bRepBodies.item(0).isSolid
        part.bRepBodies.item(0).name=part.name
        for sk in part.sketches:sk.isLightBulbOn=False
        for plane in part.constructionPlanes:plane.isLightBulbOn=False
    H['color_body'](d,p.bRepBodies.item(0),'Case bottom slate',(72,91,106))
    p.attributes.add('PitClaw','assembly','Slide in from the probe end after the carrier is screwed down; top keys retain it. Remove top and fascia before sliding the PCB.')
    p.attributes.add('PitClaw','print_orientation','Outer face Y=-52 on the build plate. Print coordinates=(x,-z,y+52)mm.')
    assert d.activateRootComponent()
    H['camera'](app)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'pitclaw-enclosure-r10.f3d')))
    result={'document':doc.name,'source_f3d_sha256':digest,'source_unchanged':True,
            'printed_parts':['bottom','top','retainer','probe fascia'],
            'extra_screws':0,'extra_inserts':0,
            'fascia_holes_mm':5.6,'guide_running_clearance_mm':.3,
            'keeper_clearance_x_mm':.3,'keeper_clearance_y_mm':.25,'fascia_top_clearance_mm':.3,
            'key_width_mm':12,'key_thickness_mm':2.1,'key_entry_chamfer_mm':.4,
            'keeper_side_arm_mm':3,'keeper_rear_strap_mm':2.75,'keeper_height_mm':4.2,
            'retainer_to_key_clearance_mm':.5,
            'body_volumes_mm3':{part.name:part.bRepBodies.item(0).volume*1000 for part in (c,top,p)}}
    (OUT/'build-native.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
