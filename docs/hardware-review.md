# Hardware review — Rev B-T2F0-A5807-S4

The carrier is a **routed prototype** with a
[JLCPCB fabrication package](../hardware/carrier-revb/fabrication/jlcpcb-2026-09-06/README.md).
The order review corrected U2's undersized holes and misplaced body outline,
extended J9's slots to the fabricator's minimum aspect ratio, aligned J8's holes
with its socket drawing, and corrected manufacturing legend rules. Physical
module/enclosure fit and load qualification remain.
The [final electrical review](../hardware/carrier-revb/verification/final-electrical-review.md)
records the retained relay circuit and independent pin/polarity checks.
Three subagents reviewed electrical design, physical interfaces and firmware.
Findings were challenged against the actual KiCad netlist, manufacturer drawings
and production firmware before applying the small corrections below.

## Confirmed defects and corrections

| Priority | Defect | Correction |
|---|---|---|
| P1 | S2 put USB-PD on J9’s normally closed sleeve contact, shorting PD to ground with an empty jack. | Leave J9 pin 3 unused. K1 selects one positive source at a time, automatically giving powered wall input priority. |
| P1 | Probe conversion inverted the pull-up divider, treated ADC full scale as the excitation voltage, and never detected an open probe at 3.3 V. | Measure AIN3 each scan; use `R = 10000 * raw / (raw_supply - raw)` and a 98% rail-relative open threshold. Invalid reference readings invalidate the probes. |
| P1 | Losing the pit probe retained the old PID output and could keep the blower running. | Stop the fan and close the damper on invalid pit data. Resume only after a fresh valid PID computation. |
| P2 | The 25 kHz power PWM default was poorly suited to the passive MOSFET gate pull-up and uncharacterized two-wire blower. | Start at 100 Hz and a 100% kick-start; confirm startup, duty range and temperature on the actual blower. |
| P2 | The draft checker could return success with ERC/DRC violations and reuse stale reports. | Regenerate native reports, fail on actual violations and parity errors, and check all 18 jack/relay/source cases for source shorts and simultaneous input paths. |
| P2 | Final routing put a narrow return beside the servo signal at J2 pin 4. | Move the servo approach between layers and widen the shared ground escape to 1.2 mm; recheck filled-ground paths. |
| P2 | Mounting courtyards alone did not prohibit copper under metal washers. | Add top-washer copper keepouts and round the NPTH exemptions; preserve underside boss/sweep exclusions. |
| P2 | Existing controller enclosure instructions appeared applicable to the new carrier. | Mark the 50 × 70 mm perfboard case and controller STLs incompatible with the Rev B mounting and connector layout. |
| P2 | The first carrier case used an unsupported 8 mm WT32 rear mounting datum. | Use the Plus V1.3 drawing's 10.8 mm datum. The revised 44.9 mm case also lowers the carrier onto 5 mm posts and mounts Q1 flat. |

J9’s [manufacturer drawing](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf)
shows A as the isolated center contact and B–C as the sleeve switch. The original
S2 1–3 assumption was also embedded in the verification script; clean ERC could
not establish the physical contact behavior. **Do not power S2 as drawn.**

The revised [wiring](wiring.md) and [carrier project](../hardware/carrier-revb/README.md)
use common ground with separate PD_12V and WALL_12V positive nets. K1 is a
G5Q-1 DC12 changeover relay: NC selects PD; a coil powered by raw WALL_12V selects
wall power through NO. D3 clamps the coil. JP2 is removed, so ordinary source
changes do not require opening the enclosure. An unpowered barrel plug does
not disable PD. The captured BOM is $29.21 before extras, $1.59 above S3.

The [Omron drawing and ratings](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf)
specify NC 3 A/30 VDC, NO 5 A/30 VDC and a 0.4 W coil. Its transfer contact
opens before changing sources; switching can restart the controller. The flyback
diode slows release. This is a prototype source selector, with contact inrush,
brownout behavior and loaded transfer still requiring bench checks.

## Rebuttal decisions

- Keep the fixed TSR 2-2450N converter, common ground, high-side blower switch,
  flyback diode and direct passive-piezo drive. Their topology is consistent.
- Reject switching the PD negative return: external USB/PC grounds can bypass
  the disconnected return. No verified suitable switched-center jack was found.
- S4 used K1 to keep the sources exclusive. The subsequent
  [relay-free input review](../hardware/carrier-revb/power-input-review.md)
  compares a dual Schottky package and a low-loss electronic selector by cost,
  assembly and blower-voltage loss. The final user decision retains K1, with USB-PD on NC and wall on NO.
- Use the SPDT G5Q-1, not G5Q-1A: the latter has no normally closed contact.
  Account for the SPDT coil’s 0.4 W and NC contact’s lower 3 A rating.
- Keep the existing fuse-removal decision. Use protected/current-limited regulated
  12 V sources rated no more than 3 A; this carrier has no branch protection.
- Keep the ADS1115 module’s own bypassing and pull-ups as an assembly requirement.
  Extra carrier parts are not justified without evidence that those functions are missing.
- Do not treat a successful embedded compilation as working display hardware.
  The legacy TFT_eSPI SPI pins overlap carrier GPIO13/14. WT32’s actual parallel
  data bus spans two GPIO banks and its FT6336U touch uses I2C. Fixing pin flags
  alone does not fix the backend. See [firmware bring-up](../firmware/hardware-bringup.md).

The 100 Hz PWM default is a prototype starting point, supported by the
[Analog Devices two-wire fan discussion](https://www.analog.com/en/resources/technical-articles/fanspeed-regulators.html).
The exact fan still determines useful frequency, startup duration and duty range.

## Remaining physical work

1. Fit-check the purchased RJ45, probe jacks, barrel jack, converter, ADC socket
   and Adafruit 5807 mounting stack. Verify jack/cable electrical numbering.
2. Verify the owned ADC module’s local bypassing and SDA/SCL pull-ups to VDD.
   Measure DEBUG-derived 3.3 V with the display and Wi-Fi active.
3. Fit-check the new [landscape enclosure](../enclosure/carrier-case.md), including
   WT32 antenna/rear components, blind-boss screw engagement and real plug bodies.
   The carrier now has an independent 51 × 58 mm M3 pattern; the WT32's
   51.39 × 75.14 mm pattern is on its internal retainer. Legacy controller STLs
   remain incompatible.
4. Complete the WT32 display/touch backend before testing with carrier loads.
5. Measure WT32 plus MG90S startup and loaded currents, 5 V droop, shared RJ45
   ground loading, blower startup/PWM and Q1/U2 temperatures. Begin servo travel
   with the linkage disconnected and conservative mechanical endpoints.
6. Validate the routed power copper against measured current and temperature.
   J2 pin 4 carries combined blower and servo return and is rated 1.5 A.
7. Rerun ERC/DRC/parity after routing, inspect Gerbers and PTH/NPTH drill output,
   and complete a representative multi-hour bench soak before cooker use.

## Bring-up checks

With sources disconnected, check J9 pins 2–3 are continuous only when empty and
pin 3 has no PCB connection elsewhere. Verify K1 coil pins 1/5, COM 2, NO 3 and
NC 4. With sources disconnected, check COM–NC continuity and diode polarity;
then exercise PD only, wall only, both, and an unpowered barrel plug with a
current-limited setup. Test interruption/restart, coil release and adapter
brownout before connecting the blower and servo.
Configure MOD1 for 12 V / 3 A and meter-check polarity before connecting loads.

Check U2’s 5 V output with a load before fitting JP1. Include all downstream
capacitance when checking its stated 820 uF capacitive-load limit. Its internal
current limiting protects the converter; it is not a precise 2 A branch fuse.
Remove JP1 before using the WT32’s own USB port.

Use known resistors on all three probe channels before temperature calibration.
Disconnect and short the pit channel during fan kick-start and each control mode:
the blower must stop and the damper close. Reconnection must wait for fresh control
data. Test fan and servo separately, then together; target 4.75–5.25 V on the 5 V
rail under the measured worst-case load.

See [generated verification](../hardware/carrier-revb/verification/README.md) for
actual CAD checks. Passing logical checks does not establish physical fit,
thermal performance or fabrication readiness.
