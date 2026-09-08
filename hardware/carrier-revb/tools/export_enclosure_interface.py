#!/usr/bin/env python3
"""Export the actual placed carrier's mechanical interface for the enclosure.

Run with KiCad 9 Python after build_draft.py. Socket face offsets come from the
footprint drawings; seating heights and cable overmolds remain fit-test inputs.
"""
import json
import math
import hashlib
from pathlib import Path
import pcbnew as pcb
from adafruit5807_geometry import usb_face

ROOT = Path(__file__).resolve().parents[1]
board = pcb.LoadBoard(str(ROOT / "pitclaw-carrier.kicad_pcb"))
source_hashes={ext:hashlib.sha256((ROOT/f'pitclaw-carrier.kicad_{ext}').read_bytes()).hexdigest()
               for ext in ('pcb','pro')}
fps = {f.GetReference(): f for f in board.GetFootprints()}

def point(ref, local=(0, 0)):
    f = fps[ref]
    a = math.radians(f.GetOrientationDegrees())
    x, y = local
    return [round(pcb.ToMM(f.GetPosition().x) - 100 + x*math.cos(a) + y*math.sin(a), 4),
            round(pcb.ToMM(f.GetPosition().y) - 50 - x*math.sin(a) + y*math.cos(a), 4)]

mounts = [point(ref) for ref in ("H1", "H2", "H3", "H4")]
pd_mounts = [point(ref) for ref in ("H5", "H6")]
assert sorted(mounts) == sorted([[4.5,4.5],[55.5,4.5],[4.5,62.5],[55.5,62.5]])
for ref in ("H1", "H2", "H3", "H4"):
    assert abs(pcb.ToMM(next(iter(fps[ref].Pads())).GetDrillSize().x)-3.2) < 1e-6
probes = [point(ref, (3, 0)) for ref in ("J4", "J5", "J6")]
power = [point("J2", (3.56, -7.62)), point("J9", (-13.6, 0)), list(usb_face())]
assert all(abs(p[1]+3) < 1e-5 for p in probes), "Probe faces must face the short probe edge"
assert all(abs(p[1]-93.5) < 1e-5 for p in power[:2]), "RJ45 and barrel must stay flush"
assert abs(power[2][1]-91.5) < 1e-5, "USB-C must be recessed 2 mm behind the other sockets"

# Conservative round envelopes for solder/lead clearance, derived from actual
# placed THT pads rather than a solid PCB witness that hides underside pins.
underside_pads = []
for ref, f in sorted(fps.items()):
    for p in f.Pads():
        if ref.startswith("H") or p.GetAttribute() not in (pcb.PAD_ATTRIB_PTH, pcb.PAD_ATTRIB_NPTH):
            continue
        width, height = pcb.ToMM(p.GetSize().x), pcb.ToMM(p.GetSize().y)
        diameter = (max(width, height) if p.GetShape() in
                    (pcb.PAD_SHAPE_CIRCLE, pcb.PAD_SHAPE_OVAL)
                    else math.hypot(width, height))
        underside_pads.append([
            round(pcb.ToMM(p.GetPosition().x)-100, 4),
            round(pcb.ToMM(p.GetPosition().y)-50, 4),
            round(diameter+.4, 4),
        ])

relay_corners = [v for g in fps["K1"].GraphicalItems()
                 if isinstance(g, pcb.PCB_SHAPE) and g.GetLayer() == pcb.F_Fab
                 and g.GetShape() == pcb.SHAPE_T_SEGMENT
                 for v in (g.GetStart(), g.GetEnd())]
rx0, ry0 = min(pcb.ToMM(v.x)-100 for v in relay_corners), min(pcb.ToMM(v.y)-50 for v in relay_corners)
rx1, ry1 = max(pcb.ToMM(v.x)-100 for v in relay_corners), max(pcb.ToMM(v.y)-50 for v in relay_corners)
relay_box = [round(v, 4) for v in (rx0, ry0, rx1-rx0, ry1-ry0, 16.2)]

# Cover every other electrical component at its actual placed XY. A generic
# central block omitted U2, edge capacitors and headers. F.Fab bounds may include
# leads/stroke and are conservative; 16 mm is an assembly allowance, not a
# measured 3D supplier model. External connectors and K1 have dedicated models.
component_boxes=[]
for ref,f in sorted(fps.items()):
    if f.GetAttributes() & pcb.FP_BOARD_ONLY or ref in {'J2','J4','J5','J6','J9','K1'}:
        continue
    graphics=[g for g in f.GraphicalItems() if isinstance(g,pcb.PCB_SHAPE) and g.GetLayer()==pcb.F_Fab]
    assert graphics,('Missing component body envelope',ref)
    boxes=[g.GetBoundingBox() for g in graphics]
    x0=min(pcb.ToMM(b.GetX())-100 for b in boxes)
    y0=min(pcb.ToMM(b.GetY())-50 for b in boxes)
    x1=max(pcb.ToMM(b.GetRight())-100 for b in boxes)
    y1=max(pcb.ToMM(b.GetBottom())-50 for b in boxes)
    if ref=='U2':
        # Traco gives ±0.5 mm body tolerance; avoid counting line stroke twice.
        points=[v for g in graphics for v in (g.GetStart(),g.GetEnd())]
        x0=min(pcb.ToMM(v.x)-100 for v in points)-.5
        x1=max(pcb.ToMM(v.x)-100 for v in points)+.5
        y0=min(pcb.ToMM(v.y)-50 for v in points)-.5
        y1=max(pcb.ToMM(v.y)-50 for v in points)+.5
    component_boxes.append({'ref':ref,'xywh_height_mm':[round(v,4) for v in
        (x0,y0,x1-x0,y1-y0,6.5 if ref=='Q1' else 16)],
        'basis':'Placed F.Fab including leads/stroke; U2 includes body tolerance. Height is an assembly allowance; verify actual parts and harnesses.'})
assert len(component_boxes)==31

interface = {
    "revision": "carrier-enclosure-r7",
    "coordinate_system": "KiCad component-side view; board upper-left (0,0), mm",
    "board_mm": [60,92,1.6], "carrier_mounts_mm": mounts,
    "carrier_hole_mm": 3.2, "carrier_boss_diameter_mm": 9,
    "pd_mounts_mm": pd_mounts,
    "carrier_case_offset_y_mm": 4.5,
    "carrier_installation": {"initial_offset_y_mm": .5, "slide_mm": 4,
                             "lift_mm": .3, "max_solder_tail_mm": 3},
    "carrier_underside_pads_xy_d_mm": underside_pads,
    "carrier_relay_box_xywh_height_mm": relay_box,
    "component_envelopes": component_boxes,
    "component_envelopes_revision": "r7-complete-placed-coverage",
    "source_pcb_sha256": source_hashes['pcb'],
    "power_faces_mm": dict(zip(("RJ45", "BARREL", "USB_C"), power)),
    "power_face_setback_from_exterior_mm": {"RJ45": 0, "BARREL": 0, "USB_C": 2},
    "probe_faces_mm": dict(zip(("PIT", "MEAT1", "MEAT2"), probes)),
    "wt32_mounts_mm": [[4.305,6.52],[55.695,6.52],[4.305,81.66],[55.695,81.66]],
    "wt32_mount_type": "Rear-facing blind OEM plastic bosses; use internal retainer",
    "unmeasured": ["WT32 boss depth and glass outer envelope", "connector seating heights",
                   "actual plug overmolds", "carrier component and solder-lead heights"],
}
target = ROOT / "mechanical/enclosure-interface.json"
target.write_text(json.dumps(interface, indent=2)+"\n")
values = {
    "carrier_board_mm": interface["board_mm"], "carrier_mount_xy": mounts,
    "carrier_probe_x": [p[0] for p in probes], "carrier_power_x": [p[0] for p in power],
    "carrier_power_face_y": [p[1] for p in power], "carrier_probe_face_y": probes[0][1],
    "carrier_case_offset_y": interface["carrier_case_offset_y_mm"],
    "carrier_underside_pads": underside_pads,
    "carrier_relay_box": relay_box,
    "carrier_pd_mount_xy": pd_mounts,
    "carrier_component_boxes": [c['xywh_height_mm'] for c in component_boxes],
    "carrier_component_refs": [c['ref'] for c in component_boxes],
}
scad = ROOT.parents[1] / "enclosure/carrier-interface.scad"
scad.write_text("// Generated from carrier CAD by export_enclosure_interface.py. Do not hand-edit.\n"
                + "".join(f"{k} = {json.dumps(v)};\n" for k,v in values.items()))
print(json.dumps(interface, indent=2))
assert all(hashlib.sha256((ROOT/f'pitclaw-carrier.kicad_{ext}').read_bytes()).hexdigest()==digest
           for ext,digest in source_hashes.items()), 'Mechanical export changed native PCB/project'
