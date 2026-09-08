# Final electrical review — retained relay circuit

Reviewed 2026-09-06. K1 remains G5Q-1 DC12: USB-PD on NC, wall power on NO.
The user's no-fuse prototype choice is preserved. The fabrication review preserves the
schematic connections while correcting footprints and local routing.

**No confirmed schematic pin, polarity or source-selection error was found.**
The completed routing passes native ERC, DRC, connectivity and schematic parity.
The independent return-path review found a narrow J2 ground connection; that
connection was widened and the final saved copper was checked again. Physical
load and assembly qualification remains.

The review read the native schematic, exported KiCad netlist, component
selection and custom footprint definitions. It did not use the generator's
expected-pin-net file as proof of circuit correctness. The inspected netlist
contains 37 electrical components and 104 pin records, including intentionally
unconnected pins. Its normalized `(reference, pin, net)` SHA-256 is
`80ddba3ff031a202070c9084cdbf1d001501f4fd21a33c752aad2997ba2095a9`.

## Confirmed circuit behavior

| Block | Independent finding |
|---|---|
| Source selection | K1 pins 1/5 are the coil; 2 is COM, 3 NO and 4 NC. Native connections put pin 1 and NO on raw WALL_12V, pin 5 on GND, COM on +12V and NC on PD_12V. USB supplies the load with the coil off; wall supplies it with the coil on. |
| Barrel and flyback | J9 center/A is WALL_12V, sleeve/B is GND and switched sleeve/C is unused. D3's cathode is WALL_12V and anode is GND, opposing normal coil voltage. |
| Blower | Q1 is wired 1 gate, 2 drain/FAN_OUT, 3 source/+12V. Q2 is wired emitter to ground, base through R2, collector to Q1 gate. R1 pulls the gate to source; R3 pulls the base down. High GPIO12 turns the blower on; undriven GPIO leaves it off. D2 cathode FAN_OUT/anode GND is the correct high-side freewheel orientation. |
| Power and programming | C1/C3 positive terminals face their respective +12V/+5V rails. U2's native map is 1 VIN, 2 GND, 3 VOUT. JP1 separates carrier +5V from WT32 +5V; remove it before powering WT32 through programming USB. |
| Analog and GPIO | Probe sleeve is ground and both tip pins join the biased probe node. Each ADC channel has its own 1 kΩ/100 nF filter. AIN3 measures excitation; ADDR is grounded for 0x48. Firmware uses ±4.096 V gain, compatible with measuring the 3.3 V rail. EXT GPIO10/11/12/13/14 assignments agree with the WT32-SC01 Plus manual. |

Primary checks: [Omron G5Q](https://components.omron.com/eu-en/system/files/2026-04/datasheet_pdf/J155-E1.pdf),
[Tensility 54-00133](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf),
[Infineon IRF5305](https://www.infineon.com/part/IRF5305),
[onsemi 2N3904](https://www.onsemi.com/pdf/datasheet/2n3903-d.pdf),
[Same Sky MJ1-2503A](https://www.sameskydevices.com/product/resource/mj1-2503a.pdf),
[TI ADS1115](https://www.ti.com/lit/ds/symlink/ads1115.pdf), and the manufacturer's
[WT32-SC01 Plus V1.3 manual](https://github.com/janick/WT32-SqLn/blob/main/docs/WT32-SC01-Plus-V1.3-EN.pdf)
already available locally. The subsequent JLCPCB footprint review retrieved
[Traco's manufacturer datasheet through Mouser](https://www.mouser.com/datasheet/3/1230/1/tsr2n_datasheet.pdf)
and confirmed the pin map, 5 V / 2 A rating, 6.5–36 V input range and 820 µF
maximum capacitive load. That drawing also exposed the U2 drill/body defects
corrected for the fabrication package; see [the footprint review](jlc-footprint-review.md).

## Final routed evidence

The checked PCB SHA-256 is
`7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764`.
The schematic redraw preserves the 104-record pin-map hash above. The current
native checks report **0 ERC violations, 0 DRC violations, 0 unconnected items
and 0 schematic-parity differences**. All 37 electrical references agree with
the BOM and footprints. Eighteen actual jack/contact/source combinations keep
the two positive inputs isolated; this is a topology check, not a relay timing
or fault-current test.

The board contains **314 track segments and 16 vias**, with 1,589.925 mm total
track length. The measured power routing is:

| Net | Routed width and total length at that width |
|---|---|
| PD_12V | 2 mm: 21.580 mm |
| WALL_12V | 2 mm: 80.020 mm |
| +12V | 2 mm: 57.699 mm; 0.3 mm R1 bias branch: 62.071 mm |
| FAN_OUT | 1.2 mm: 81.637 mm |
| +5V | 1.2 mm: 153.167 mm |
| +5V_WT32 | 1.2 mm: 50.461 mm |

The 0.3 mm +12V branch supplies R1's gate bias, approximately 12 mA with the
blower enabled; it does not carry blower or converter load current. C2/C4 were
moved toward U2. The gate-drive components remain spread across the board, so
switching behavior and analog noise still need the intended-load bench test.

Saved GND fills cover 3,070.265 mm² on F.Cu (three regions) and 2,848.010 mm²
on B.Cu (four regions). Counting zones or airwires alone would have missed the
J2 return problem: its original B.Cu throat was approximately 0.6–0.7 mm wide,
and its F.Cu pad region was isolated. The fix moved the nearby servo signal and
added a 1.2 mm GND route from J2 pin 4 toward J9 ground. Its four segments total
20.418 mm and merge into the ground fill.

The order review corrected U2's offset body and enlarged its drills, then moved
its pin row to Y70.75 mm. The servo signal now detours outside the maximum
converter body using two additional signal vias. Two parallel Ø1.2/0.6 mm
GND stitches at (18,78.5) and (20,78.5) mm retain the broad return connection.
The original 2 mm front WALL_12V trunk remains. Its copper occupies a 1.54 mm
strip along the right edge of U2's maximum body envelope. This deliberately
retains the stronger ground return, and does not fully follow Traco's generic
avoid-under-converter trace guidance. Direct converter pin fanouts also remain;
bench noise/thermal testing is still required.

The checker retains an independent geometric test: union actual saved GND
fills, GND tracks and pad/via copper on each layer, then erode the polygons by
half the tested corridor width. A 0.01 mm width allowance avoids collapsing an
exactly nominal-width track to a zero-area line; a pad may meet a surviving
region within the erosion distance plus 0.05 mm. Power-section plated pads
and actual GND vias can join the layer graphs. ADC/DEBUG pads are excluded as
power-return layer bridges. Native KiCad geometry and a separate Shapely
inspection agreed on the original bottleneck; native geometry verifies the
final correction.

On the final board, **J1/J9/U2/C1/C3/D2 and J2 remain connected at the 2 mm
corridor check**, including necessary transitions between layers. The checker
requires 2 mm for the main power landings and at least 1.2 mm for J2's return.
This measures continuity through broad copper regions with short pad-entry
allowances. It does not certify PTH/via resistance, copper thickness, current
sharing, voltage drop, temperature or immunity to blower noise.

Four top mounting-washer keepouts also pass: tracks, vias, pads and pours are
excluded over Ø7.4 mm. Circular NPTH exemptions stay within 1.7 mm radius on
both top-washer and underside-boss rules. This fixes the previously exposed
corners of square exemptions while preserving the actual 3.2 mm mounting holes.

Reproducible measurements and per-net narrow sections are retained in
[summary.json](summary.json); the native reports and checker results are in
[README.md](README.md). The checker requires a routed board and zero native
unconnected items; it no longer accepts the old unrouted draft state.

## Physical load and assembly checks that remain

1. **J2 is rated 1.5 A per contact.** Pin 4 carries the combined blower and
   servo return. Validate their simultaneous current, startup waveform, cable
   voltage drop and contact heating against that rating; a 3 A input source
   does not establish compliance. This is a load-acceptance condition, not a
   confirmed overload without the actual loads.
   [Amphenol S6032C, page 2](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/s6032c_rjhse.pdf)
2. Confirm actual blower current and D2's 1 A freewheel duty/temperature, plus
   Q1 heating at the intended 100 Hz PWM. R1 dissipates approximately 0.144 W
   at 12 V with the blower continuously enabled, within its 0.25 W nominal
   rating subject to temperature derating.
3. Verify combined WT32/servo 5 V load and startup against U2's rating, and
   count downstream capacitance as well as C3's 470 µF against the recorded
   820 µF capacitive-load limit. Confirm the owned ADC module supplies local
   100 nF bypassing and SDA/SCL pull-ups to its 3.3 V supply.
4. Meter-check harness orientation, 5807's 12 V output, relay NC/NO states
   and all custom-footprint samples before powering the complete assembly.
   Test source changes and adapter brownout: D3 delays coil release, and the
   relay circuit does not promise uninterrupted power or brownout supervision.

These checks do not request extra fuses, a different selector or new enclosure
openings. No physical measurements were performed in this review.
