# Independent JLCPCB bare-board DFM review

Reviewed 2026-09-06 against the current [JLCPCB rigid PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/). Scope: actual routed carrier geometry, current project rules and relevant local footprints; two-layer FR-4, 1.6 mm board, 1 oz copper. The initial independent audit was read-only. The design task subsequently authorized the limited regulator-area routing repairs described below.

**Result: no remaining measured fabrication-geometry blocker on the reviewed board.** The initial slot-ratio and silkscreen issues were corrected by the main design task and independently rechecked. The fabrication archive must still be generated from this reviewed board and visually checked for correct copper/mask/silk layers, outline and plated/non-plated drill separation. This is a bare-board manufacturing review, not module-fit or operating-load validation.

Reviewed PCB SHA256: `7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764`.

Strict project SHA256: `814bd6b79383344938fb11cef374c5ab29d7d67091976e8c2353aa28831d35bf`.

## Findings corrected during review

- **J9 plated slots:** the original 0.80 × 1.50 mm slots had a 1.875:1 ratio. JLCPCB specifies slot length at least twice width. The three slots now measure **0.80 × 1.60 mm**, with minimum 0.45 mm annular ring. Local footprint drill definitions agree. Board-local coordinates (subtract KiCad X=100 mm, Y=50 mm) are pin 1 `(26.5,79.9)`, pin 2 `(26.5,85.8)`, pin 3 `(31.2,82.7)` mm.
- **Silkscreen:** original 0.80 mm text and 0.12 mm strokes were below the published printing guidance. All 41 visible footprint references now measure **1.00 mm high / 0.15 mm stroke**, and all 563 footprint silk primitives use 0.15 mm width. The project now requires 0.15 mm silk-to-pad clearance, 1.00 mm text height and 0.15 mm text stroke. Native DRC passes these rules.
- **U2 and J8 assembly holes:** the Traco footprint now represents the manufacturer's offset body and uses **Ø1.40 mm finished drills / Ø2.00 mm copper pads**, with 0.30 mm annular rings. U2 pin coordinates are `(17,70.75)`, `(19.54,70.75)` and `(22.08,70.75)` mm. J8's ten socket holes now use **Ø1.05 mm drills / Ø1.80 mm pads**, with 0.375 mm rings. The larger holes address actual lead/socket insertion rather than bare-board drilling limits.
- **Regulator-area routing:** the former thin ground route crossed corrected U2 pin 1 and was removed locally. A direct 2 mm front ground fanout and two parallel **Ø1.20/0.60 mm ground vias** at `(18,78.5)` and `(20,78.5)` reconnect the wide return pours. SERVO_SIG now detours around the left of U2, using two additional Ø0.80/0.40 mm transitions at `(23.4444,66.5)` and `(3,78)`. All servo track and via copper clears U2's maximum body. The full project check preserves the main 2 mm and J2 1.2 mm return corridors. No footprint/pad positions, circuit connections or mechanical keepouts changed during this local repair.

## Actual measurements

| Feature | Measured board | Result |
|---|---|---|
| Board outline | One closed 60 × 92 mm rectangle, four Edge.Cuts segments, 0.05 mm drawing stroke | Pass; no internal cutouts |
| Copper layers / thickness | Two / 1.60 mm | Standard rigid FR-4 geometry |
| Minimum track width | 0.30 mm; other routes 1.20 and 2.00 mm | Above 0.10 mm 1 oz manufacturing minimum |
| Minimum PTH annular ring | 0.30 mm, J4–J6 probe slots and U2 | Above 0.25 mm recommendation |
| RJ45 J2 pads | Ø1.50 mm copper / Ø0.89 mm drill; 0.305 mm ring | No thin-annulus issue remains |
| Probe slots J4–J6 | Nine 0.50 × 1.50 mm plated slots, 0.30 mm ring | At the supported two-layer minimum width; 3:1 ratio |
| Barrel slots J9 | Three 0.80 × 1.60 mm plated slots | Meets 2:1 ratio |
| Vias | Eleven Ø0.80/0.40 mm and five Ø1.20/0.60 mm pad/drill pairs | 0.20/0.30 mm rings; no microvias |
| Closest drill edges | U2 and Q1 adjacent holes: approximately 1.140 mm; J2 same-row holes: 1.142 mm | Above 0.45 mm PTH hole spacing |
| Closest foreign trace to via hole | Approximately 0.502 mm | Above 0.20 mm minimum |
| Closest foreign trace to component PTH hole | Approximately 0.621 mm, J2 pin 8 | Above 0.28 mm minimum |
| Closest foreign trace to NPTH | Approximately 0.584 mm, left J2 locating peg | Above 0.20 mm minimum |
| Mask expansion | Zero; pad and mask aperture 1:1 | Supported by current JLCPCB LDI process |
| Narrowest mask web | Approximately 0.313 mm, J2 pins 1/2 | Above 0.10 mm green and 0.13 mm black/white guidance |
| Copper-to-outline clearance | Current project requires 0.50 mm; native DRC passes | Above 0.20 mm routed-edge minimum |

The mask web calculation uses native KiCad pad polygons; drill/trace distances use native shape collision queries with 0.001 mm search resolution. Reported distances are rounded approximations. Vias are tented on both sides in the PCB settings; they are not specified as epoxy-filled or copper-capped. Mounting and locating holes are intentionally NPTH without copper annular pads.

## Regulator layout tradeoff

Traco's generic instruction to avoid routing traces under the converter is **not fully implemented**. The original low-impedance, 2 mm-wide WALL_12V front trace remains centered at X=26.5 mm. Its copper overlaps the maximum tolerated converter body over X=25.50…27.04 mm, Y=68.81…77.41 mm: a **1.54 mm-wide edge strip**. Against the nominal body the strip is 1.04 mm wide. Moving this feed to the back obstructed the alternative ground return and left a roughly 1.7 mm corridor between the R15 AIN2 pad and K1 NO pad. Retaining the original front route preserves the stronger return path with a bounded repair. The servo signal is outside the maximum body, while necessary direct VIN, VOUT and ground fanouts remain beneath the converter. This is a documented engineering tradeoff, not a claim of full compliance with the generic Traco layout note; loaded regulation and interference require prototype measurement.

## Verification and reproducibility

Final native KiCad checks against the restored strict project settings: **0 DRC violations, 0 unconnected items, 0 ERC violations and 0 schematic-parity issues**. The current [verification summary](summary.json), [DRC report](drc.json) and [ERC report](erc.json) match the PCB, schematic and project hashes. Final board: **314 tracks and 16 vias**. The independent native geometry measurement was repeated on this final PCB hash; its snapshot is `/tmp/pitclaw-jlc-measurements.json` and its retained measurement log is `work/jlc-release/final-dfm-measurements.log`.

The local custom footprints now carry the corrected hole geometry and 0.15 mm silk strokes. Any future update from original footprint libraries must retain these corrections and rerun the strict manufacturing checks before regenerating fabrication files. Saving a board loaded under a different basename was found to reset the live KiCad project to default rules; the release task restored the strict project and reran checks. The final project hash must match the verification summary before CAM export.
