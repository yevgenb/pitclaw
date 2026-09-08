"""Apply the documented Adafruit 5807 direct-mount geometry; never route nets."""
import json
from pathlib import Path
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
MECH = ROOT / "mechanical/adafruit5807"
CFG = json.loads((MECH / "interface.json").read_text())

def vec(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))

def module_body():
    """Module faces +Y; its PCB is inset 1.643 mm for the recessed USB port."""
    width, length = CFG["source_board_outline_mm"]
    anchor = CFG["carrier_anchor_mm"]
    x1 = anchor["center_x"] - width / 2
    y2 = anchor["pcb_front_y"]
    return (round(x1, 4), round(y2-length, 4), round(x1+width, 4), round(y2, 4))

def holes():
    x1, y1, _, _ = module_body()
    return [(round(x1 + x, 4), round(y1 + y, 4))
            for x, y in CFG["source_mount_holes_from_rear_left_mm"]]

def usb_face():
    return (CFG["carrier_anchor_mm"]["center_x"],
            round(CFG["carrier_anchor_mm"]["pcb_front_y"] + CFG["usb_connector_face_overhang_mm"], 4))

def keepout_polygon():
    x1, y1, x2, y2 = module_body()
    m = CFG["keepout_margin_mm"]
    x1, y1, x2, y2 = max(0, x1-m), max(0, y1-m), min(60, x2+m), min(92, y2+m)
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def mounting_rectangles(margin=0):
    r = CFG["mount_courtyard_radius_mm"] + margin
    return [(x-r, y-r, x+r, y+r) for x, y in holes()]

def reserved_rectangles(margin=0):
    x1, y1, x2, y2 = module_body()
    m = CFG["keepout_margin_mm"] + margin
    return [(max(0, x1-m), max(0, y1-m), min(60.0, x2+m), min(92.0, y2+m))] + mounting_rectangles(margin)

def _line(board, a, b):
    shape = pcb.PCB_SHAPE(board)
    shape.SetShape(pcb.SHAPE_T_SEGMENT)
    shape.SetStart(vec(100+a[0], 50+a[1]))
    shape.SetEnd(vec(100+b[0], 50+b[1]))
    shape.SetWidth(pcb.FromMM(.15))
    shape.SetLayer(pcb.Dwgs_User)
    board.Add(shape)

def _note(board, text, x, y, size=.75):
    note = pcb.PCB_TEXT(board)
    note.SetText(text)
    note.SetPosition(vec(100+x, 50+y))
    note.SetTextSize(vec(size, size))
    note.SetTextThickness(pcb.FromMM(.12))
    note.SetLayer(pcb.Dwgs_User)
    board.Add(note)

def update_board(board):
    assert len(board.GetTracks()) == 0, "Refusing automatic placement moves after routing has begun"
    refs = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, (x, y, angle) in CFG["carrier_placement_changes"].items():
        refs[ref].SetOrientationDegrees(angle)
        refs[ref].SetPosition(vec(100+x, 50+y))

    for ref in ("H5", "H6"):
        if ref in refs:
            board.RemoveNative(refs[ref])
    for zone in list(board.Zones()):
        if zone.GetZoneName() == "ADAFRUIT_5807_NO_COPPER":
            board.RemoveNative(zone)

    io = pcb.PCB_IO_MGR.PluginFind(pcb.PCB_IO_MGR.KICAD_SEXP)
    for i, (x, y) in enumerate(holes(), 5):
        fp = pcb.FOOTPRINT(board)
        fp.SetReference("H" + str(i))
        fp.SetValue("ADAFRUIT 5807 M2 / 2.4 NPTH")
        fp.SetFPID(pcb.LIB_ID("PitClaw", "Adafruit5807_M2_Mount"))
        fp.SetAttributes(pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES | pcb.FP_BOARD_ONLY)
        fp.Reference().SetLayer(pcb.F_Fab)
        fp.Reference().SetTextSize(vec(.8, .8))
        fp.Reference().SetPosition(vec(0, -3.5))
        fp.Value().SetVisible(False)
        pad = pcb.PAD(fp)
        pad.SetNumber("")
        pad.SetAttribute(pcb.PAD_ATTRIB_NPTH)
        pad.SetShape(pcb.PAD_SHAPE_CIRCLE)
        pad.SetSize(vec(CFG["carrier_hole_diameter_mm"], CFG["carrier_hole_diameter_mm"]))
        pad.SetDrillSize(pad.GetSize())
        layers = pcb.LSET.AllCuMask()
        layers.AddLayer(pcb.F_Mask)
        layers.AddLayer(pcb.B_Mask)
        pad.SetLayerSet(layers)
        fp.Add(pad)
        for layer, radius in ((pcb.F_CrtYd, CFG["mount_courtyard_radius_mm"]), (pcb.B_CrtYd, CFG["mount_courtyard_radius_mm"]), (pcb.F_Fab, CFG["mount_hardware_max_diameter_mm"]/2)):
            circle = pcb.PCB_SHAPE(fp)
            circle.SetShape(pcb.SHAPE_T_CIRCLE)
            circle.SetCenter(vec(0, 0))
            circle.SetEnd(vec(radius, 0))
            circle.SetWidth(pcb.FromMM(.05))
            circle.SetLayer(layer)
            fp.Add(circle)
        io.FootprintSave(str(ROOT / "PitClaw.pretty"), fp)
        fp.SetPosition(vec(100+x, 50+y))
        board.Add(fp)

    x1, y1, x2, y2 = module_body()
    body = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    for i in range(4):
        _line(board, body[i], body[(i+1) % 4])
    center_x, face_y = usb_face()
    _line(board, (center_x-4.5, face_y), (center_x+4.5, face_y))
    _note(board, "ADAFRUIT 5807\nHUSB238 / 12V 3A", center_x, (y1+y2)/2)
    _note(board, f"USB FACE {face_y-92:+.3f} mm", center_x, 95.0)

    zone = pcb.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetZoneName("ADAFRUIT_5807_NO_COPPER")
    layer_set = pcb.LSET()
    layer_set.AddLayer(pcb.F_Cu)
    layer_set.AddLayer(pcb.B_Cu)
    zone.SetLayerSet(layer_set)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowCopperPour(True)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowFootprints(False)
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in keepout_polygon():
        outline.Append(pcb.FromMM(100+x), pcb.FromMM(50+y))
    board.Add(zone)

    for item in board.GetDrawings():
        if not isinstance(item, pcb.PCB_TEXT):
            continue
        if item.GetText() == "USB-C PD\n12V ONLY":
            item.SetPosition(vec(100+CFG["carrier_anchor_mm"]["center_x"], 148.0))
        if item.GetText() == "PIT CLAW B-DRAFT":
            item.SetLayer(pcb.Dwgs_User)
            item.SetPosition(vec(130, 151.0))
