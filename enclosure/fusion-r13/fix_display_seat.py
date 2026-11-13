"""Apply the direct-contact display seat correction to the original r13 Fusion archive.

Run once in Fusion on the supplied r13 archive. All dimensions are in mm.
The fitted outer shell and bezel pocket stay fixed; shorten only the four
retainer stops by 1.8mm, shifting the display/retainer towards the glass ledge.
"""
import adsk.core as C
import adsk.fusion as F
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def run(_context: str):
    app = C.Application.get()
    d = F.Design.cast(app.activeProduct)
    root = d.rootComponent
    assert root.occurrences.count == 10
    assert abs(d.userParameters.itemByName('case_h').value * 10 - 44.9) < 1e-7
    assert d.rootComponent.occurrences.item(1).component.name.startswith('02 Top bezel')
    unchanged = {i: root.occurrences.item(i).component.bRepBodies.item(0).volume for i in (0, 7, 9)}
    original_retainer_volume = root.occurrences.item(2).component.bRepBodies.item(0).volume
    for name, expression, description in (
        ('bezel_contact_z', '43.7 mm', 'Fixed underside of the bezel, on the inactive glass border'),
        ('screen_mount_depth', '9.3 mm', 'Effective bench-fit depth, inferred from1.8mm gap; use9.3..9.6 with0..0.3mm anchor shims'),
        ('retainer_stop_z', '34.4 mm', 'Fixed shell stop: original32.6 plus1.8mm correction'),
        ('screen_interface_t', '0 mm', 'Direct glass contact; no assumed soft strip or open air gap'),
        ('screen_front_z', 'bezel_contact_z - screen_interface_t', 'Screen front follows the bezel contact face'),
    ):
        p = d.userParameters.itemByName(name)
        if p:
            p.expression = expression
            p.comment = description
        else:
            d.userParameters.add(name, C.ValueInput.createByString(expression), 'mm', description)
    d.userParameters.itemByName('retainer_top').expression = 'screen_front_z - screen_mount_depth'
    top = root.occurrences.item(1).component
    display = root.occurrences.item(4).component
    changes = [
        (top, 'Four display retainer hard stops', 'ProfileOffset', 'retainer_stop_z'),
        (top, 'Four display retainer hard stops', 'AlongDistance', 'case_h - retainer_stop_z'),
        (top, 'Four retainer insert pilots', 'ProfileOffset', 'retainer_stop_z - 0.02 mm'),
        (top, 'Display body and glass pocket', 'AlongDistance', 'bezel_contact_z - seam_z + 0.02 mm'),
        (top, 'Active display window', 'ProfileOffset', 'bezel_contact_z - 0.02 mm'),
        (top, 'Active display window', 'AlongDistance', 'case_h - bezel_contact_z + 0.04 mm'),
        (display, 'Display glass outline', 'ProfileOffset', 'screen_front_z - 1.45 mm'),
        (display, 'Active display area', 'ProfileOffset', 'screen_front_z'),
        (display, 'Display frame envelope', 'ProfileOffset', 'screen_front_z - 4.8 mm'),
        (display, 'Display rear PCB envelope', 'ProfileOffset', 'screen_front_z - screen_mount_depth'),
        (display, 'Four rear mounting boss envelopes', 'ProfileOffset', 'retainer_top'),
        (display, 'Four rear mounting boss envelopes', 'AlongDistance', 'screen_mount_depth - 4.8 mm'),
    ]
    for component, feature, role, expression in changes:
        matches = [p for p in component.modelParameters if p.createdBy and p.createdBy.name == feature and p.role == role]
        assert len(matches) == 1, (feature, role)
        matches[0].expression = expression
    assert d.computeAll()
    for i, volume in unchanged.items():
        assert abs(root.occurrences.item(i).component.bRepBodies.item(0).volume - volume) < 1e-9
    assert abs(root.occurrences.item(2).component.bRepBodies.item(0).volume - original_retainer_volume) < 1e-9
    top.name = '02 Top bezel - direct glass seat and 4.2mm pilots'
    app.activeDocument.name = 'PitClaw enclosure r13 - direct glass seat with USB base'
    report = {
        'status': 'APPLIED; run export_r13.py and all release checks',
        'reported_original_gap_range_mm': [1.5,1.8], 'nominal_gap_mm': 0,
        'bezel_underside_z_mm': 43.7, 'glass_front_z_mm': 43.7,
        'retainer_front_z_mm': 34.4, 'retainer_back_z_mm': 31.9,
        'maximum_retainer_movement_toward_bezel_mm': 1.8, 'anchor_shim_range_mm': [0,.3], 'outer_glass_recess_mm': 1.2,
        'effective_mount_depth_range_mm': [9.3,9.6], 'depth_basis': 'Inferred from reported gap and original11.1mm stack; not a supplier measurement',
        'reprint': ['carrier-top.stl'],
        'unchanged_print_geometry': ['carrier-bottom.stl', 'carrier-retainer.stl', 'probe-fascia.stl', 'adafruit5807-base.stl'],
        'physical_fit': 'First fit required; start with0.3mm shims at all anchors and reduce evenly until glass contacts without force. Do not tighten across an anchor support gap.'
    }
    (OUT / 'display-seat-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
