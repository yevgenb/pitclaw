"""Upgrade an open native r8 document to the populated, correctly handed r9 model.

The original r8 archive is preserved. Run through Fusion's Python API.
"""
import adsk.core as C
import adsk.fusion as F
import math,runpy
from pathlib import Path

OUT=Path(__file__).resolve().parent


def run(_context):
    app=C.Application.get();d=F.Design.cast(app.activeProduct)
    assert app.activeDocument.name=='PitClaw enclosure r8 - four-anchor retainer'
    assert d.rootComponent.occurrences.count==5
    c=d.rootComponent.occurrences.item(0).component
    original=c.bRepBodies.item(0)
    entities=C.ObjectCollection.create();entities.add(original)
    i=c.features.mirrorFeatures.createInput(entities,c.yZConstructionPlane);i.isCombine=False
    c.features.mirrorFeatures.add(i).name='Correct KiCad-to-case handedness across X'
    c.features.removeFeatures.add(original).name='Remove mirrored-layout predecessor'
    c.name='01 Bottom shell - r9 PCB alignment'
    c.bRepBodies.item(0).name='Bottom shell - corrected physical connector order'
    pop=d.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
    pop.component.name='REFERENCE - populated carrier (KiCad geometry)'
    opt=app.importManager.createSTEPImportOptions(str(OUT/'populated/carrier-native.step'))
    assert app.importManager.importToTarget(opt,pop.component)
    app.activeDocument.name='PitClaw enclosure r9 - populated carrier'
    runpy.run_path(str(OUT/'populate_custom.py'))['run'](_context)
    for o in pop.childOccurrences.item(0).childOccurrences:
        if 'CP_Radial' in o.component.name:o.isLightBulbOn=False
    m=C.Matrix3D.create();m.setToRotation(math.pi,C.Vector3D.create(0,0,1),C.Point3D.create(0,0,0))
    m.translation=C.Vector3D.create(0,.45,.75)
    pop.transform2=m
    # Fusion otherwise reverts uncaptured occurrence moves when features are added.
    d.snapshots.add().name='Locate actual PCB component side up from KiCad'
    d.rootComponent.occurrences.item(3).isLightBulbOn=False
