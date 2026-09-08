# JLCPCB mechanical order review

Reviewed 2026-09-06. Scope: bare carrier PCB fabrication and its tolerance relationship to the r6 enclosure. This does not qualify a populated product or certify the purchased modules, plugs, screws, printed plastic, or thermal performance.

**Disposition: the corrected board outline, holes and mounting arrangement support a small bare-PCB prototype order. J9’s slot-length item is resolved. The r6 enclosure remains a nominal fit prototype and does not have a complete worst-case tolerance budget.**

## Current evidence

- The actual PCB has two copper layers and nominal 1.6 mm thickness. Edge.Cuts contains four connected straight segments defining exactly 60 × 92 mm. The board has square external corners, no rounded-corner specification, and no internal routed cutouts. The enclosure's rectangular PCB witness matches this outline.
- H1–H4 are Ø3.2 mm NPTH at (4.5, 4.5), (55.5, 4.5), (4.5, 62.5), (55.5, 62.5): a 51 × 58 mm mounting pattern. H5/H6 are Ø2.4 mm NPTH at (36.753, 87.817) and (51.993, 87.817). The remaining mechanical holes are the two Ø3.25 mm RJ45 pegs and three Ø1.2 mm probe-jack pegs.
- Existing native verification reports zero DRC violations, zero unconnected items and zero schematic-parity issues. The three enclosure collision checks pass at nominal dimensions. The top, bottom and retainer meshes each remain one connected watertight solid. These results do not include fabrication or printer variation.
- All source hashes recorded in `enclosure/review/verification.json` match the files inspected. The PCB hash is `7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764`; case SCAD is `4f682c886fcae5e3fee92dca5948f43269c77ec7f5361b0e4be0aa3522276097`; generated interface SCAD is `dc19a718c7aa89431256124f31ea480d6a0e5973e2bcf92531672e36545f998b`. This review must be reconciled with any later CAD revision.

## Fabrication corrections verified

J9 pads 1–3 now have 0.8 × 1.6 mm plated oval drills, preserving their original centers and directions. This meets JLCPCB's 0.5 mm minimum plated-slot width and length-at-least-twice-width rule. The original Tensility pattern used 0.8 × 1.5 mm slots; extending only their length adds clearance. Probe slots remain 0.5 × 1.5 mm. [JLCPCB drilling capabilities](https://jlcpcb.com/capabilities/pcb-capabilities).

U2 now has Ø1.4 mm drills and Ø2.0 mm pads, corrected offset body geometry and anchor (17, 70.75) mm. J8 now has Ø1.05 mm drills. These values were read back independently from the final native PCB and agree with the companion footprint review. Native checks pass after the local routing repair.

The corrected U2 nominal body is X12.54–26.54, Y69.31–76.91 mm. Expanding it by 0.5 mm per edge keeps it clear of shell walls and closure columns. Independently reserving the full existing 16 mm fitted height at this actual location reaches Z25.1, below the top bezel's minimum Z25.6 and 3 mm below the display rear reserve. This conservative bound supplements the central SCAD component witness, which does not cover the full U2 body. The actual U2 pins are included in the regenerated underside sweep. See `enclosure/review/jlc-corrected-footprints.json` and the refreshed collision logs.

## Tolerance basis

Use ordinary CNC-routed individual boards for this case. JLCPCB lists ±0.2 mm regular routed dimensions, ±0.1 mm precision routing, ±0.4 mm V-scoring, ±10% thickness at 1.6 mm, and ±0.05 mm hole position. Its current through-hole diameter allowance is +0.13/−0.08 mm; its NPTH guide gives ±0.08 mm. These are fabrication capabilities, not measured results for this board. [Capability table](https://jlcpcb.com/capabilities/pcb-capabilities), [NPTH guide](https://jlcpcb.com/blog/npth-design-guide).

The following calculations apply those allowances to the current nominal model. Printer shrinkage, heat-set insert displacement, component seating, module-hole play and plug tolerances remain unmeasured. The published board-dimension tolerance alone is not a complete hole-to-outline datum specification.

| Interface | Current allowance | Consequence |
|---|---|---|
| Carrier blind edge channel | 60.4 mm wide, with 0.2 mm at each side; its end stops 0.2 mm beyond the nominal PCB power edge | A 0.2 mm outward edge deviation consumes the entire local clearance before print error or hole-to-edge registration. This is the main case-fit tolerance issue. It does not require changing the electrical PCB to order prototypes. Measure the delivered board and enlarge the hidden case channel if needed while preserving its exterior skin. |
| Channel height | Z7.2–9.7 mm; PCB underside seats at Z7.5; installation lift is 0.3 mm | At maximum 1.76 mm carrier thickness, the lifted PCB top is Z9.56, leaving 0.14 mm to the channel roof. Thickness variation alone fits; printed accuracy, bow and burrs still need checking. |
| Four M3 carrier mounts | Ø3.2 mm holes; Ø9 mm support bosses | A Ø3.12 mm minimum hole leaves only 0.06 mm radial space around an ideal Ø3 mm screw. Hole-position variation consumes most of that budget before insert placement error. The four fixed bosses are not a guaranteed production fit. Check an insert/mount coupon and do not force screws through a misaligned board. |
| M2 module mounts | Carrier holes Ø2.4 mm; purchased 5807 holes nominal Ø2.5 mm | A Ø2.32 mm carrier hole still clears an ideal Ø2 mm screw by 0.16 mm radially. However, the assembly is not a precision locating system: clearance at both boards can shift the USB face and hardware. Set the module against a fit fixture before tightening; its own manufacturing tolerance is not established by ordering this carrier from JLCPCB. |
| USB pocket and hidden reliefs | 20 × 10 mm exterior recess, 2 mm deep; 9.54 × 4.1 mm shell opening; 0.2 mm hidden PCB/head clearance | Nominal local floor skins are 0.943 mm at the PCB relief and 0.983 mm at the head relief. A +0.16 mm carrier thickness change alone consumes most of the hidden slot's 0.2 mm upward clearance, leaving 0.04 mm before module/spacer/print variation. Physical alignment and an actual cable fit are required. Do not present these thin regions as structurally tested. |
| RJ45 and barrel openings | Nominal faces flush; 0.3 mm profile clearance per side plus 0.3 mm installation travel | PCB thickness affects connector Z, while lead/peg tolerances and soldering affect face XY. Nominal flushness is not guaranteed by bare-board dimensional tolerance. Trial-seat connectors and plugs before committing to final plastic. |
| Initial carrier insertion | Lower at +0.5 mm Y, slide forward 4 mm, then lower 0.3 mm | Initial nominal end gaps are 1.0 mm at the probe noses and 1.5 mm at the power faces. This path is geometrically valid; the final fitted openings/channel are tighter than the initial lowering path. |
| Probe plug access | Ø10.5 mm openings; socket faces recessed 7.5 mm | Actual plug-body diameter, length and full seating remain a purchased-cable fit check. PCB milling tolerance does not establish plug reach. |

## Assembly limits retained

The underside CAD sweep uses all exported PTH pad/peg envelopes and a maximum 3 mm clipped solder-tail projection. M2 nut/washer/tip projection is limited to 3.3 mm below the carrier, with a Ø5 mm hardware envelope and 2 mm combined upper head/washer height. Inspect these dimensions on the assembled unit; a solder blob or substituted locking nut can invalidate the nominal path.

The final 16-via audit has 4.1144 mm minimum clearance to boss sweeps and 10.4632 mm to support sweeps. It assumes no protruding wire or solder mound on vias. Preserve the copper-free underside support patches and slide corridors. The relay's 16.2 mm seated envelope leaves 2.8 mm nominal reserve to the upper assembly; maximum carrier thickness alone reduces that to 2.64 mm, before unmeasured display, harness and printer variation.

For a small bare-board prototype run, the tight plastic interfaces are ordinary fit-development work. They prevent claiming a qualified enclosure or interchangeable assembled product. Keep the existing physical gates for the ADC module, actual WT32 rear envelope and mounting screws, cable seating, harness bends, and connector load testing. This review found no reason to add rounded PCB corners, change the 60 × 92 mm outline, or alter the mounting pattern merely to order the prototype boards.
