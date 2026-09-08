# Existing Mini100 converter — superseded listing review, 2026-09-04

> Historical only. Rev B-T2F0-A5807-S3 replaces the Mini100 and its socket/header with a
> soldered TSR 2-2450N and removes F1–F4. None of the recommendations below
> describe the current CAD/BOM.

Selected by the user: Weewooday, Amazon ASIN **B08JZ5FVLC**. This identifies the
listing, not a controlled manufacturer part number or a verified batch revision.

## Seller evidence

The [listing and seller photographs](https://www.amazon.com/dp/B08JZ5FVLC/)
describe a **20 × 11 × 5 mm** board with **2.54 mm** solder-hole pitch.
Looking at the component side with the pad row on the left, its top-to-bottom
labels are **EN, IN+, GND, VO+**. The underside view reverses that orientation.
Photographs show adjustable output with a cut-ADJ / solder-5V fixed-output option.

The advertised 3 A maximum requires additional cooling; the seller reports a
12 V input / 1.5 A output test without it. This is not a guaranteed continuous
rating in our enclosure. Input claims conflict: 4.5–12 V versus 4.5–24 V.
The description claims short-circuit protection but warns against sustained
shorts; it lists no output overvoltage protection. EN is described as default-on.

## User measurement and implemented B-M1S1 interface

The user confirmed **2.54 mm hole pitch** and **1.5 mm from the hole-row centres
to the nearest short PCB edge**. These replace the previous pitch/edge guesses.
The row is provisionally centered across the seller's 11 mm board width, leaving
1.69 mm between either outer pad centre and the adjacent long edge. That centering
has not been measured. Body dimensions remain seller data, not a new user measurement.

Retain this converter as the **prototype candidate** for the 5 V WT32/MG90S rail.
Do not attribute the superseded Traco's ratings or capacitor limit to it. The
blower remains on the separate 12 V path; it is not a load on this converter.

Implemented carrier connection: a four-position 2.54 mm through-hole header/socket
interface, with the module parallel to the carrier, components outward, and an
insulating support under its free end still to be fit-tested. U2 purchases a
Sullins PPPC041LFBN-RC socket. A separate Amphenol 68000-104HLF male header solders
to the module underside. The new local footprint uses 1.02 mm carrier drills
from the socket drawing; these are not a claim about the module's hole diameter.
Provide positive retention for transport; do not rely on a cantilevered socket
or an adhesive pad alone. Keep conductive hardware and carrier copper clear of
the exposed underside pads. Preserve access to the voltage-setting pads before
final assembly and leave ventilation around the switching parts.

EN should remain unconnected for the proposed always-on use after confirming
the actual module's behavior. Do not tie it to 12 V. Check the physical labels
against the assigned KiCad numbers before insertion; the order is orientation-specific.

The remaining physical checks are row centering, module-hole fit, PCB thickness,
underside protrusions and header seating. Nominal module underside height is
about 11.05 mm (socket plus male-header insulator), with approximately 16.05 mm
total above the carrier using the seller's 5 mm module height. These are fit-test
estimates, not verified stack dimensions. No mounting holes are assumed or
to be drilled into the module. A short-wire interface remains a fallback if its
holes do not accept the chosen header.

## Bring-up and protection

1. With the carrier and loads disconnected, verify the trigger's actual 12 V
   output. Identify and check converter polarity from its own silkscreen.
2. Set the converter to 5 V while unloaded, power-cycle, and measure again before
   attaching WT32 or MG90S. Any fixed-output modification is done unpowered and
   only after confirming the actual board matches the seller's instructions.
3. Use a current-limited bench supply and dummy load first. Check regulation,
   startup, temperature and recovery at the intended load. Avoid sustained shorts.
4. Test WT32 boot/Wi-Fi/backlight together with representative loaded servo
   movement. Scope the 5 V rail at WT32 and at the servo, including PTC and harness
   voltage drop. Do not accept a no-load multimeter reading as a transient test.
5. Repeat in the intended stack/enclosure at the expected ambient temperature.
   Stop on overheating, voltage excursions or resets; do not solve failures by
   blindly increasing fuse ratings or capacitance.

**Keep F1–F4 unchanged pending testing.** An advertised short-circuit feature is
not enough to justify deleting F2; the available information does not establish
safe fault coordination. F3's provisional 0.5 A hold value still needs evaluation
with the MG90S. Neither a PTC nor the input TVS is output overvoltage protection.

## Artifact status

Native CAD, previews, selection.json, XLSX and CSV now describe **B-M1S1**. U2's
symbol and footprint have four pins; pin 4 EN has a no-connect marker. Pin 1 OUT
is at (10.21,74.5), pin 2 GND at (7.67,74.5), pin 3 IN at (5.13,74.5), and pin 4
EN at (2.59,74.5), all in mm from the carrier's top-left component-side corner.
The 20 × 11 mm body is x=0.9–11.9, y=56–76. A switching-body copper keepout spans
x=0.4–12.4, y=55.5–72.5, leaving the pad row accessible for routing. Support and
retention geometry is not yet released; do not ship a cantilevered module.

C3, C5, F1, R5 and D2 moved in B-M1 without changing values or nets. B-M1S1
removes Q3, R7 and R19 for direct passive-piezo drive; no fuses, PD-module
dimensions or mounting holes changed. See the verification reports. This remains
an unrouted engineering draft, not an order.

Connector sources: [Sullins socket drawing](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/937/Female_Headers.100_DS.pdf),
[Amphenol header](https://www.amphenol-cs.com/product/68000104hlf.html).
