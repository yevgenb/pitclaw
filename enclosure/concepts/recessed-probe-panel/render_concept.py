"""Appearance alternative: a continuous case outline with one rounded port pocket.

Creates a separate Fusion concept document. Original CAD/STLs are preserved.
The ports remain7.5mm behind the overall exterior; they meet the pocket floor.
"""
import adsk.core as C
import adsk.fusion as F
import runpy,json,hashlib
from pathlib import Path

OUT=Path(__file__).resolve().parent
ENCLOSURE=Path(__file__).resolve().parents[2]


def run(_context):
    app=C.Application.get()
    source=ENCLOSURE/'fusion-r9/pitclaw-populated-r9.f3d'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    opt=app.importManager.createFusionArchiveImportOptions(str(source))
    doc=app.importManager.importToNewDocument(opt)
    doc.name='PitClaw rounded probe pocket - APPEARANCE CONCEPT'
    d=F.Design.cast(app.activeProduct);occ=list(d.rootComponent.occurrences)
    assert len(occ)==7
    for i,o in enumerate(occ):o.isLightBulbOn=i in [0,1,2,4,5,6]
    ns=runpy.run_path(str(ENCLOSURE/'fusion-r9/support/build_fusion_r8.py'))
    camera=runpy.run_path(str(ENCLOSURE/'concepts/stepped-probe-face/render_concept.py'))['camera']
    c=occ[0].component
    ns['rr'](c,'Concept integral probe pocket backing',(0,11.65),64,20,4,-52,10,ns['JOIN'],'XZ')
    profiles=[]
    for name,y,w,h,r in [('Outer rounded entry',-52.02,60,18,5.5),('Recess floor',-44.5,50,12,3)]:
        sk,flip=ns['sketch'](c,name,axis='XZ',z=y)
        ns['rounded'](sk,flip,0,11.65,w,h,r)
        profiles.append(sk)
    inp=c.features.loftFeatures.createInput(ns['CUT'])
    for sk in profiles:inp.loftSections.add(sk.profiles.item(0))
    inp.participantBodies=[c.bRepBodies.item(0)]
    f=c.features.loftFeatures.add(inp);f.name='Wide tapered probe pocket'
    for sk in profiles:sk.isLightBulbOn=False
    ns['circles'](c,'Small jack openings in recessed floor',[(-17,11.65),(0,11.65),(17,11.65)],4.6,-44.52,2.56,ns['CUT'],'XZ')
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    c.name='CONCEPT bottom - rounded probe pocket'
    c.attributes.add('PitClaw','release_status','Appearance only. Port faces remain7.5mm behind overall exterior. Cable boot clearance and assembly split not verified.')
    for sk in c.sketches:sk.isLightBulbOn=False
    for plane in c.constructionPlanes:plane.isLightBulbOn=False
    camera(app,(17,-20,16))
    assert app.activeViewport.saveAsImageFile(str(OUT/'rounded-probe-pocket.png'),1600,1200)
    camera(app,(9,-20,5))
    assert app.activeViewport.saveAsImageFile(str(OUT/'rounded-probe-detail.png'),1600,1100)
    camera(app,(20,0,2.245))
    assert app.activeViewport.saveAsImageFile(str(OUT/'side-profile.png'),1600,1000)
    camera(app,(9,-20,5))
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'rounded-probe-pocket-CONCEPT.f3d')))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    notes={'status':'APPEARANCE CONCEPT ONLY','source_f3d_sha256':digest,'source_unchanged':True,
           'overall_envelope_mm':[104,86,44.9],'outer_pocket_mm':[60,18],
           'pocket_floor_mm':[50,12],'depth_mm':7.5,
           'tradeoff':'Jacks are level with pocket floor but remain recessed7.5mm from the outermost case face.',
           'unchanged':'PCB/screen placement, top, retainer, case outline, power side.',
           'unverified':'Actual cable boots and insertion, assembly joint/path, print supports and mechanical stiffness.',
           'no_print_stl_exported':True}
    (OUT/'concept-notes.json').write_text(json.dumps(notes,indent=2)+'\n')
    print(json.dumps(notes))
