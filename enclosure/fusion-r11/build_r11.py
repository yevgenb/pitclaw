"""Add four interior M3 mounting inserts to a preserved R10 archive."""
import adsk.core as C
import adsk.fusion as F
import hashlib
import json
import runpy
from pathlib import Path

OUT = Path(__file__).resolve().parent
H = runpy.run_path(str(OUT / 'support/geometry_helpers.py'))
MOUNTS = [(x, y) for x in (-36, 36) for y in (-37, 37)]
SOURCE_SHA = '7b8a72a4156941832957eb7e3d6639795637ddd2f38485d4052f308b51262fd7'


def run(_context: str):
    app = C.Application.get()
    source = OUT.parent / 'fusion-r10/pitclaw-enclosure-r10.f3d'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    doc.name = 'PitClaw enclosure r11 - bottom mounting inserts'
    d = F.Design.cast(app.activeProduct)
    occ = list(d.rootComponent.occurrences)
    assert len(occ) == 8
    bottom = occ[0].component
    H['circles'](bottom, 'Four internal accessory mounting bosses', MOUNTS, 10, 2.5, 5, H['JOIN'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            H['rr'](bottom, f'Mount to wall and closure web {sx} {sy}',
                    (sx * 37.85, sy * 32.5), 5.7, 9, 0, 2.5, 5, H['JOIN'])
    H['circles'](bottom, 'Inside entry M3 insert pilots', MOUNTS, 4, 2.5, 5.02, H['CUT'])
    H['circles'](bottom, 'External M3 screw access', MOUNTS, 3.4, -.02, 2.54, H['CUT'])
    for sx in (-1, 1):
        H['rr'](bottom, f'Heat tool clearance over probe guide stop {sx}',
                (sx * 36.15, -41.75), 5.7, 2.5, 0, 7.5, .52, H['CUT'])
    bottom.name = '01 Bottom shell - hidden mounting inserts'
    assert bottom.bRepBodies.count == 1 and bottom.bRepBodies.item(0).isSolid
    bottom.bRepBodies.item(0).name = bottom.name
    bottom.attributes.add('PitClaw', 'mount_pattern', 'Four M3 at X=+/-36,Y=+/-37mm; 72x74mm pattern; Z0 is external bottom.')
    bottom.attributes.add('PitClaw', 'mount_screw_reach', '6.5–7mm beyond the mounting face, including bracket and washer stack in screw length selection.')
    bottom.attributes.add('PitClaw', 'mount_inserts', 'Install four M3Sx4 inserts from inside before electronics, flush with Z7.5 boss tops.')

    insert_occ = d.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
    inserts = insert_occ.component
    inserts.name = 'REFERENCE - optional bottom mounting inserts'
    H['circles'](inserts, 'Four short M3 insert envelopes', MOUNTS, 4.6, 3.5, 4, H['NEW'])
    H['circles'](inserts, 'Nominal thread minor bores - simplified', MOUNTS, 2.5, 3.48, 4.04, H['CUT'])
    assert inserts.bRepBodies.count == 4
    for body in inserts.bRepBodies:
        body.name = 'M3Sx4 mounting insert - simplified reference'
        H['color_body'](d, body, 'Mount insert brass reference', (185, 145, 53))
    inserts.attributes.add('PitClaw', 'scope', 'Simplified 4.6mm maximum OD, 4mm long heat-set envelopes; intentional overlap with 4mm pilot is not a collision.')
    for component in (bottom, inserts):
        for sk in component.sketches: sk.isLightBulbOn = False
        for plane in component.constructionPlanes: plane.isLightBulbOn = False
    assert d.activateRootComponent()
    for n, o in enumerate(d.rootComponent.occurrences):
        o.isLightBulbOn = n in (0, 1, 2, 4, 5, 6, 7, 8)
    if d.snapshots.hasPendingSnapshot:
        d.snapshots.add().name = 'Capture bottom mounting reference placement'
    H['camera'](app)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    report = {'document': doc.name, 'source_f3d_sha256': SOURCE_SHA,
              'source_unchanged': True, 'mount_centres_mm': MOUNTS,
              'mount_pitch_mm': [72, 74], 'mount_thread': 'M3',
              'additional_inserts': 4, 'total_case_inserts': 16,
              'boss_diameter_mm': 10, 'boss_top_z_mm': 7.5,
              'pilot_diameter_mm': 4, 'pilot_floor_z_mm': 2.5,
              'external_access_diameter_mm': 3.4,
              'front_guide_stop_cap_height_mm': 7.5,
              'insert_z_mm': [3.5, 7.5], 'recommended_screw_reach_mm': [6.5, 7],
              'reference_insert_diameter_mm': 4.6,
              'body_volume_mm3': bottom.bRepBodies.item(0).volume * 1000}
    (OUT / 'build-native.json').write_text(json.dumps(report, indent=2) + '\n')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT / 'pitclaw-enclosure-r11.f3d')))
    print(json.dumps(report))
