# JLCPCB bare-board prototype package

**Final review: PASS for a small bare-PCB prototype order, 2026-09-06.**
The final native ERC, DRC, schematic parity and unconnected counts are all zero.
Independent inspection of the exact archive finds no copper opens or shorts
across 31 nets, and all 120 plated holes/slots plus 11 nonplated holes match.
Both Gerber faces were rendered and visually inspected. Physical qualification
and the fabricator's own upload/CAM acceptance remain as described below.

Upload **`pitclaw-carrier-jlcpcb.zip`**. It contains the two copper layers,
two solder-mask layers, two legend layers, one closed board profile and
separate plated/nonplated Excellon drill files. The 12 plated slots are encoded
as G85 slots. The archive is for manual through-hole assembly; it is not a
JLCPCB assembly-service package. Drill maps, previews and review documents are
outside the upload archive.

## Order settings

| Setting | Value |
|---|---|
| Service | Bare PCB, single board; no assembly or stencil |
| Quantity | 5 suggested for the first prototype run |
| Dimensions | 60 × 92 mm |
| Material / layers | FR-4 / 2 copper layers |
| Board thickness | 1.6 mm |
| Outer copper | 1 oz |
| Solder mask / legend | Green / white |
| Surface finish | Lead-free HASL |
| Outline process | Ordinary CNC routing, individual boards |
| Via treatment | Ordinary tented vias; no filling, capping or special plugging |
| Special features | No impedance control, castellations, edge plating or V-scoring |

Green mask, 1 oz and these drill/slot sizes were checked against
[JLCPCB's published capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/)
on 2026-09-06. Standard board tolerances still apply. If the upload viewer
does not detect **2 layers, 60 × 92 mm, 120 plated holes/slots and 11 nonplated
holes**, investigate the discrepancy before checkout. Hole counts include vias;
some viewers display vias and slots separately. Factory CAM acceptance and the
live quote have not been obtained, and no order has been submitted.

## Verification evidence

- [Release manifest](manifest.json): SHA-256 of source PCB, schematic, project
  rules, successful native verification, every CAM file and the final ZIP.
- [Independent CAM audit](review/cam-audit.json): reopens the exact ZIP with
  Gerbonara, checks every drill's plating, diameter, location and slot direction,
  confirms the closed outline and compares Gerber copper connectivity to the
  native pad nets using independent vector geometry.
- [Top Gerber preview](review/gerber-top.svg) and
  [bottom Gerber preview](review/gerber-bottom.svg), with the bottom viewed from
  the solder side. These are rendered from the manufacturing archive.
- [Native checks](../../verification/README.md),
  [DFM review](../../verification/jlc-dfm-review.md),
  [footprint review](../../verification/jlc-footprint-review.md), and
  [enclosure review](../../verification/jlc-mechanical-review.md).

The CAM audit allows only Excellon's 0.001 mm coordinate quantization. Its arc
approximation is at most 0.002 mm. It checks connectivity separately from native
KiCad DRC and does not replace the fabricator's CAM process. Gerbonara reports
KiCad's accepted G90 statement position and the intentionally absent paste
layers; these do not change the parsed geometry.

## Changes made by the order review

- Corrected U2's offset body/courtyard and increased its drills from Ø1.0 to
  Ø1.4 mm, with Ø2.0 mm pads, to fit the tolerated Traco square pins. Moved U2
  0.75 mm toward the probe end to retain connector clearance.
- Enlarged J8 socket drills to Ø1.05 mm, meeting the socket drawing's Ø1.02 mm
  recommendation.
- Extended J9's 0.8 mm-wide plated slots from 1.5 to 1.6 mm to meet JLCPCB's
  minimum 2:1 slot aspect ratio. Pin centers and slot directions are unchanged.
- Increased visible legend height/stroke to 1.0/0.15 mm, cleared overlapping
  labels and enforced manufacturing clearances in the native project rules.
- Moved SERVO_SIG outside the converter body and added two parallel power-size
  ground stitches. The original front wall-power trunk retains a 1.54 mm overlap
  along the maximum converter body edge to preserve the broad ground return;
  this is a documented exception to Traco's generic under-body routing guidance.
  Both ground layers were refilled. The schematic, relay selection and BOM part
  identities are unchanged.

## Prototype limits

This package supports a **small bare-PCB prototype order**, followed by assembly
and fit development. The exact owned ADS1115 module's header offsets and seated
height are not backed by a controlled drawing or physical measurement. Its
fit remains a possible first-board respin risk. The printed enclosure also
needs first-fit work at the tight carrier channel, inserts and USB relief.

Before powered use, verify harness polarity, the 5807's 12 V configuration,
module bypassing/pull-ups, relay transfer and the actual loads. J2's shared
blower/servo return is limited to 1.5 A; U2 supplies at most 2 A on 5 V. Check
blower freewheel current and temperatures in the case. These are assembly/load
qualification steps; no physical testing was performed by this review.

## Re-export after an edit

Run `tools/check_draft.py` with KiCad 9 Python, then `tools/export_jlc.py` with
`--output` set to a new release directory and `--cam-python` pointing to Python
with Gerbonara 1.6.3 and Shapely 2.x. The checker refuses weakened manufacturing rules, and the exporter requires
PCB, schematic and project-rule hashes to match the successful native report. Reconcile footprint and enclosure
reviews after geometry changes; a successful export alone does not repeat
those engineering reviews. Do not substitute an intermediate file from `work/`.
