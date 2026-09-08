# Footprint audit for the first JLCPCB order

Reviewed 2026-09-06 against the native PCB, custom library footprints and the
manufacturer drawings below. This review made no CAD changes.

Reviewed PCB SHA256:
`7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764`.
The inspected PCB contains 314 tracks and 16 vias. Coordinates below use the
60 × 92 mm board frame, with KiCad's (100,50) mm drawing offset removed.
The final strict-rule pass restored project rules, refilled ground copper and
moved J9's reference text. A native comparison confirmed that the reviewed
U2/J8/J9 footprint geometry, all tracks and all vias remain unchanged. The matching
official verification summary reports zero ERC, DRC, schematic-parity and
unconnected-item findings.

## Ordering findings

**The confirmed U2 footprint defects are corrected.** The former Ø1.0 mm holes
did not accommodate the full published pin tolerance. Traco specifies 0.64 mm square
pins with ±0.1 mm pin tolerance: the maximum diagonal is
`sqrt(2) × 0.74 = 1.047 mm`, larger than the former nominal hole. Its body was
also incorrectly centered on the pin row. With pins 1–3 running along +X, the
nominal body is X −4.46…9.54 mm, Y −1.44…6.16 mm relative to pin 1.

The sealed PCB and local footprint now use Ø1.4 mm holes with 2.0 mm pads and
the corrected body. U2's pin-1 anchor is (17,70.75) mm; its nominal body occupies
X12.54…26.54 / Y69.31…76.91 mm. The courtyard is
X11.79…27.29 / Y68.56…77.66 mm, including the ±0.5 mm body tolerance and
additional clearance. The position is 0.75 mm north of the former anchor to
accommodate the corrected body near J2. These dimensions and orientation agree
with KiCad 9's exact `Converter_DCDC_TRACO_TSR2-24xxN_TSR2-24xxxN_THT`
footprint. Pins remain 1=VIN, 2=GND, 3=VOUT with 2.54 mm pitch.
[Traco's current manufacturer datasheet, page 4](https://www.mouser.com/datasheet/3/1230/1/tsr2n_datasheet.pdf)

**U2's under-body routing is an explicit layout tradeoff.** Traco advises
avoiding PCB traces beneath the converter. The unrelated servo route has been
moved outside the conservatively expanded body rectangle
X12.04…27.04 / Y68.81…77.41 mm; the closest servo track copper is 0.76 mm away.
No ADC, probe or I²C signal route crosses this rectangle. Direct converter
supply/ground fanouts remain, as does the 2.0 mm F.Cu WALL_12V trunk centered
at X26.5 mm. That trunk overlaps the maximum body by a 1.54 mm edge strip,
X25.5…27.04 / Y68.81…77.41 mm. It was deliberately retained to preserve the
broad ground return; this does **not** fully follow Traco's routing guidance.
This is a prototype layout limitation, not a demonstrated mechanical fit
failure. Two Ø1.2/0.6 mm GND vias at (18,78.5) and (20,78.5) mm lie outside
the maximum body. These statements come from an independent read of the sealed
PCB's actual track geometry, including track width.

**J9's CAM issue has been corrected in the inspected native PCB.** Tensility
specifies 0.8 × 1.5 mm slots; the board now extends their long dimension to
1.6 mm to meet JLCPCB's slot aspect-ratio requirement. Slot direction and all
three centers remain correct. [Tensility drawing, page 1](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf),
[JLCPCB drilling capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)

**J8's owned module is still an unqualified fit assumption.** The carrier's
socket is a defined Sullins part, and its 2.54 mm pitch / 22.86 mm end-to-end pin
span is correct. Sullins recommends Ø1.02 mm holes; all ten holes in the sealed
PCB and local footprint now use Ø1.05 mm, exceeding that nominal recommendation.
[Sullins manufacturer drawing, page 2](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/937/Female_Headers.100_DS.pdf)

The module above that socket has no identified manufacturer or controlled
mechanical drawing. The user-linked Components101 page provides a generic
module model and pin labels, but does not establish the owned board's exact
header-to-edge offsets or assembled insertion height. Its linked chip datasheet
does not define those module dimensions. A matching nominal outline cannot
establish that two anonymous blue modules are mechanically identical.
[User-identified module reference](https://components101.com/modules/ads1115-module-with-programmable-gain-amplifier)

No confirmed footprint defect remains in the sealed PCB. With the final
strict-rule DRC passing, and subject to the separate archived-CAM checks,
this supports a **small bare-PCB prototype order**. It does not establish guaranteed drop-in fit of the
owned ADC module. If avoiding a possible board respin is essential, confirm
the module's 22.86 mm first-to-last pin span, pin order, header-to-edge offsets
and fully seated height before ordering. Electrical bring-up measurements are
separate from these dimensions that can affect PCB placement.

## Other custom footprints

| Footprint | Independent result |
|---|---|
| J2, RJHSE5080 | Matches the manufacturer's component-side PCB pattern: eight Ø0.89 mm plated holes, two Ø3.25 mm nonplated pegs 12.7 mm apart, 2.032 mm same-row pitch, 1.016 mm stagger and 1.78 mm row separation. Pin order and 7.62 mm pin-1-to-front offset agree. No discovered footprint defect. |
| J4–J6, MJ1-2503A | Three 0.5 × 1.5 mm plated slots, their orientations, 3.6 mm side-pin separation, 6/8.1 mm longitudinal positions and Ø1.2 mm locating hole agree with the recommended top-view pattern. Pin 1 is sleeve; pins 2/3 are tip. |
| K1, G5Q-1 | Correct five-pin SPDT pattern, mirrored from the manufacturer's bottom view to top-side placement. Ø1.3 mm drills, 7.62 mm row separation, 10.16/15.24/17.78 mm contact positions and 20.3 × 10.3 mm maximum body agree. |
| Q1, IRF5305 | 2.54 mm G/D/S row and Ø1.4 mm holes accommodate the maximum 1.01 × 0.61 mm narrow lead section. The 6 mm body-to-pad offset keeps the specified bend beyond the widened lead section. Lead forming, insulated support beneath the live tab and final tail length remain assembly operations to verify on the first part. |
| C2/C4/C10–C12, TDK FG28 | Ø0.9 mm holes clear the published Ø0.60 mm maximum leads. Nominal 5 mm pitch matches; forming the flexible radial leads to that pitch is normal assembly. The custom body reserve uses the published 4 × 2.5 mm plan dimensions. |
| BZ1, TDK PS1240P02BT | Custom footprint retains the specified 5 mm pitch, Ø1.0 mm holes for the nominal Ø0.6 mm leads, and Ø12.2 mm body reserve. No newly identified discrepancy. |
| H1–H4 and H5/H6 | Native Ø3.2 mm carrier mounts and Ø2.4 mm module mounts match the mechanical contract. Finished-hole/printed-insert alignment and enclosure clearances are addressed in the separate mechanical review. |

Drawing sources: [Amphenol RJHSE-X080 Rev A](https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/rjhsex080.pdf),
[CUI/Same Sky MJ1-2503A, page 2](https://xonstorage.z8.web.core.windows.net/pdf/cuiinc_mj12503a_nocat_xonlink.pdf),
[Omron G5Q](https://components.omron.com/eu-en/system/files/2026-04/datasheet_pdf/J155-E1.pdf),
[Infineon IRF5305](https://www.infineon.com/part/IRF5305),
[TDK FG28 exact part](https://product.tdk.com/en/search/capacitor/ceramic/lead-mlcc/info?part_no=FG28X7R1H104KNT06),
and [TDK PS1240P02BT](https://product.tdk.com/en/search/sw_piezo/sw_piezo/piezo-buzzer/info?part_no=PS1240P02BT).

This is a footprint/manufacturing-readiness audit. It does not repeat the
separate electrical load review or certify the enclosure's printed fit.
