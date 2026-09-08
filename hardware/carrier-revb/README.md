# Rev B-T2F0-A5807-S4 carrier PCB — routed prototype

The KiCad project contains the reviewed relay circuit and two-layer copper routing.
See [current native verification](verification/README.md), the
[schematic preview](previews/schematic/pitclaw-carrier.svg), and
[PCB previews](previews/routed/). The
[JLCPCB package](fabrication/jlcpcb-2026-09-06/README.md) targets a small bare-board
prototype order and includes exact-archive Gerber/drill checks. Physical module
and enclosure fit, load and thermal qualification remain. No order is submitted.

This revision replaces the socketed Mini100 with a soldered, through-hole
**Traco Power TSR 2-2450N** fixed 5 V / 2 A converter and removes **F1, F2, F3
and F4**. J9 provides a 5.5 × 2.1 mm center-positive wall-adapter inlet.
K1 automatically selects wall power when its 12 V coil is energized, and USB-C
PD otherwise. JP2 is removed, so changing supplies does not require opening the
case. J9 switches its sleeve, so its pin 3/C is deliberately unused. The 12 V
input, WT32 5 V feed, MG90S 5 V feed and switched blower output have no series
fuses. Use only protected/current-limited regulated 12 V sources rated no more
than 3 A; the carrier has no onboard or branch-selective overcurrent protection.

The S1 simplification also removes D1, C5, C7, C13, R17 and R18. Q3, R7 and R19
remain removed. GPIO14 drives the passive piezo through R6 (330 ohm). The owned
ADS1115 module must provide its own local supply bypassing and SDA/SCL pull-ups.

## Board architecture

- Candidate carrier: 60 × 92 mm, two layers, through-hole parts except the
  preassembled Adafruit 5807 and ADS1115 modules.
- Four 3.2 mm carrier clearance holes form an independent 51 × 58 mm M3
  pattern: (4.5, 4.5), (55.5, 4.5), (4.5, 62.5), (55.5, 62.5) mm.
  M3 screws attach the carrier to heat-set inserts in the bottom shell. Reserve
  7 mm diameter for top screw/washer hardware and 9 mm for underside insert
  bosses. The WT32 mounts separately in the top assembly.
- All external connectors occupy the two short ends for landscape use. J2,
  J9 face Y = 93.5 mm; MOD1 USB-C is set back to Y = 91.5 mm for the exterior
  recess. J4–J6 face the opposite end
  at Y = -3 mm. Two isolated underside supports at X = 2–5 and 56–59 mm,
  Y = 90.7–92 mm support the power end; matching B.Cu keepouts exclude copper,
  soldered pads and vias from their contact patches. The M3 underside reservations
  also cover the 4 mm installation slide; the whole carrier sits 4.5 mm toward
  the power end in the enclosure.
- MOD1: Adafruit 5807 HUSB238 USB-C PD breakout, 20.32 × 23.495 mm. Its two
  documented 2.5 mm holes mount over 2.4 mm H5/H6 carrier holes.
- U2: TSR 2-2450N, 14 × 7.6 × 10.2 mm SIP-3, pin 1 VIN, pin 2 GND, pin 3 VOUT.
  The pin row is offset within the body. The order review corrected that offset,
  adopted Ø1.4 mm holes / Ø2.0 mm pads for its tolerated square pins and moved
  the converter 0.75 mm toward the probe end.
- J8: socket for the owned blue 10-pin ADS1115 board. Its header pitch and body
  offsets still require a physical fit check. Confirm local bypassing and measure
  continuity from SDA/SCL to VDD through the module pull-ups before assembly.
- J2: unmagnetized 8P8C connector for the HeaterMeter blower/servo cable. It is
  **not Ethernet** and must never be connected to network equipment.
- J4–J6: three PCB-mounted Same Sky MJ1-2503A 2.5 mm probe jacks.
- J9: Tensility 54-00133, 5.5 × 2.1 mm center-positive switched DC jack,
  right-angle THT. Pin 1/A feeds WALL_12V, pin 2/B is GND and pin 3/C is unused.
- K1: G5Q-1 DC12 SPDT relay. NC = PD_12V, NO = WALL_12V, COM = +12V.
  The raw wall input powers its coil; D3 (SB140) is the coil flyback diode.
  NC is rated 3 A / 30 VDC and NO 5 A / 30 VDC. The 12 V coil uses 0.4 W.
- J1/J7/J3: carrier-side JST-XH harness headers to the 5807 and WT32. J1 and J7
  use the same housing but carry different voltages; label and route them
  separately.

## Power and connector mapping

```text
Adafruit 5807 V+ -> J1 -> PD_12V ----> K1 NC
12 V wall adapter center -> J9 pin 1 -> WALL_12V -> K1 NO + coil
K1 COM -> +12V -> U2 VIN and Q1 source
K1 coil return -> GND; D3 cathode WALL_12V, anode GND
wall adapter sleeve -> J9 pin 2 -> GND; J9 pin 3 is unused
U2 pin 3 -> +5V ----> JP1 -> WT32 EXT pin 1
                     +-----------------------> RJ45 pin 3 (MG90S +5 V)
WT32 DEBUG 3.3 V ---> J7 -> ADS1115/probe excitation only

Q1 drain -> FAN_OUT --------------------------> RJ45 pin 5
common GND -----------------------------------> RJ45 pin 4
GPIO13 -> R4 ---------------------------------> RJ45 pin 6 (servo signal)
```

RJ45 pins 1, 2, 7 and 8 are unused. Its contacts are rated 1.5 A each; pin 4
carries the combined blower and servo return. Keep the combined load within
that contact rating and verify startup and contact heating.
[Amphenol contact specification](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/s6032c_rjhse.pdf). JP1 is power-source isolation, not a fuse;
remove its shunt before powering/programming the WT32 through its own USB port.

K1 selects one input at a time. Both sources may be connected; powered wall input
has priority, while an unpowered barrel plug leaves USB-PD selected. No jumper
change is required. The break-before-make transfer may restart the controller;
D3 slows coil release. This circuit does not supervise wall-voltage quality.
Verify inrush, supply brownout and loaded switching before use.

The jack’s NC contact joins pins 2/B and 3/C, not 1/A and 3/C. S2 would short
PD to ground with J9 empty. S3 used an internal manual selector; S4 removes that
usability problem with K1. After the [price and complexity comparison](power-input-review.md),
the final decision on 2026-09-06 retains the relay: USB-PD on NC and wall on NO,
with low contact loss and straightforward through-hole assembly.
See the [G5Q contact and coil ratings](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf).

The ADC is intentionally powered from the WT32 DEBUG 3.3 V rail, so there is no
carrier 3.3 V LDO. Keep motor currents off that harness and verify the loaded
rail before relying on it.

## Retained functional circuitry

The fuses and carrier TVS are gone, but the following functional parts remain:

- The Adafruit 5807/HUSB238 power path handles USB-PD negotiation and output
  overvoltage shutdown. The former P6KE18A began breaking down above 17.1 V,
  later than the HUSB238's 1.2× requested-voltage OVP for a 12 V request, so D1
  did not add useful first-response protection in this prototype.
- D2 is the SB140 blower flyback clamp and is required for the inductive load.
- Start two-wire blower power PWM at 100 Hz with a 100% kick-start; confirm the
  actual blower starts reliably and Q1 stays cool before tuning frequency/duty.
- Q1/Q2 form the 12 V high-side blower switch and level translation from the
  WT32's 3.3 V GPIO.
- C1/C2 and C3/C4 are input/output decoupling. One 470 uF C3 replaces the former
  220 uF C3 plus 100 uF C5 while remaining below U2's stated 820 uF maximum,
  before downstream capacitance is counted.
- Q1 is now the lower-cost IRF5305PBF with the same TO-220 gate/drain/source pin
  order; BZ1 is the lower-cost TDK PS1240P02BT passive piezo.
- R5 and R10-R12 use one common 10 k, 1% part. At B≈3950, a 1% bias-resistor
  error is roughly 0.23 °C at 25 °C, 0.35 °C at 100 °C and 0.45 °C at 150 °C;
  calibrate each probe channel.

The TSR 2-2450N has internal current limiting, continuous short-circuit
protection and automatic recovery, but its specified typical 5 V-model current
limit is 360% of its 2 A rated output. Treat that as converter self-protection,
not precise protection for the MG90S, blower, cable, connector or PCB traces.

## Reduced enclosure stack

Mechanical revision r3 reduces the enclosure to 44.9 mm by lowering the carrier
onto 5 mm posts and mounting Q1 flat. Q1 uses the custom
`IRF5305_TO220_Horizontal_TabDown` footprint with 1.4 mm lead drills and an F.Cu
keepout beneath its live drain tab and formed leads. Maintain a 1 mm cured
insulating support and secure the body with side adhesive fillets for transport;
there is no tab bolt. Form the leads before soldering while supporting them
near the package. The 6.5 mm fitted-height allowance still requires a sample
and thermal check. Exact electrical parts and nets are unchanged.

The 16 mm overall carrier component allowance also covers the 14 mm C1,
socketed ADC and mated JST-XH wiring. Verify complete assemblies, including wire
turns, fit that allowance. K1 alone reserves 16.2 mm including its molded feet;
the enclosure checks its local clearance separately without increasing case depth. See the [revised case stack](../../enclosure/carrier-case.md).

Q1 dimensions use [Infineon's current datasheet](https://www.infineon.com/dgdl/Infineon-IRF5305-DataSheet-v01_01-EN.pdf?fileId=5546d462533600a4015355e370101993)
(Rev 2.1, 2026-07-24): maximum 10.67 × 16.51 × 4.83 mm body.
The 6 mm body-to-pad-row offset allows the bend beyond the widened lead area.
Follow [Infineon's assembly guidance](https://www.infineon.com/assets/row/public/packages/73/package_download/infineon-board-assembly-recommendations-to-package-en.pdf)
and verify the formed sample before soldering.

## Adafruit 5807 mount and stack

The active mount is documented in [mechanical/adafruit5807](mechanical/adafruit5807/README.md).
The module occupies X = 34.34–54.66 mm and Y = 66.862–90.357 mm, with H5/H6 at
(36.753, 87.817) and (51.993, 87.817) mm. Its PCB front edge is 1.643 mm inside the carrier
power edge. The USB-C face remains 1.143 mm beyond the module PCB, placing it
at carrier Y = 91.5 mm: **0.5 mm inside the carrier edge**.

Use two provisional M2 × 10 screws, four washers no larger than Ø5 mm, two 3 mm nylon spacers
and nuts under the carrier. Add one adhesive insulating support beneath the
module's rear/free edge and maintain clearance to the WT32. The
[current enclosure fit prototype](../../enclosure/carrier-case.md) provides
flush RJ45/barrel openings and a 2 mm-deep outside USB pocket. The USB face
is level with the pocket floor, inside a fitted 9.54 × 4.1 mm opening.
The cable housing sits in the 20 × 10 mm exterior pocket. Internal backing
has blind PCB/head clearances, with at least 0.943 mm of plastic locally;
there are no exterior board/hardware cutouts. The main carrier-edge channel
remains. Solid plastic separates the three ports. Verify full insertion and the carrier's slide-in assembly with
the actual cables and populated PCB before final printing.

The board-mount holes and module body have an F.Cu/B.Cu keepout with no current
component-courtyard collisions. Connect V+/GND to J1 with a short secured
20-22 AWG pair; the wires must not carry USB insertion force.

## Design files

- `pitclaw-carrier.kicad_pro`, `.kicad_sch`, `.kicad_pcb`: editable KiCad 9
  project.
- `tools/build_draft.py`: schematic generator; defaults to preserving routed PCB copper.
- `tools/export_enclosure_interface.py`: exports actual carrier mount and socket
  coordinates to `mechanical/enclosure-interface.json` and the enclosure's
  generated `carrier-interface.scad`.
- [Current enclosure fit prototype](../../enclosure/carrier-case.md): bottom
  carrier mounts, top display mounting, connector openings and fit-test gates.
- `verification/`: native ERC/DRC plus independent pin/net, BOM and mechanical
  checks.
- `previews/pitclaw-carrier-schematic.pdf` and `.png`: full schematic, with enlarged section PNGs alongside.
- `previews/schematic/`: native schematic SVG.
- `previews/routed/`: native copper-layer and assembly previews.
- `bom/selection.json`: exact part selection and captured DigiKey pricing.
- `bom/pitclaw-carrier-digikey-bom.xlsx`: editable priced BOM.

The routed PCB is authoritative for copper. Keep it alongside the project rules,
custom footprints and schematic. Power trunks use wider copper than signal
traces; see [routing notes](routing.md) for widths, returns and reproduction.

## Reproduce the checks

Use KiCad 9's Python interpreter with `pcbnew` available. From this directory:

```sh
python3 tools/build_draft.py --schematic-only
python3 tools/export_enclosure_interface.py
python3 tools/check_draft.py
```

The schematic-only mode preserves PCB copper and project rules. Explicit
`--rebuild-unrouted-pcb` refuses an existing routed board. The checker exports
fresh ERC, DRC and schematic parity reports and requires zero unconnected items.
It also checks the physical pin maps, source-selection states, BOM and mechanical
reservations. `PITCLAW_KICAD_CLI` and `PITCLAW_KICAD_SHARE` override the default
macOS KiCad paths. Regenerating geometry requires refreshing enclosure verification.

## Prototype assembly and qualification

The fabrication package records the native and exported-file order checks.
The following physical checks remain for assembly and use. In particular, the
exact owned ADC module's header offsets and seated height remain a possible
first-board respin risk; measuring them before ordering reduces that risk.

1. Configure the Adafruit 5807 for 12 V / 3 A and confirm voltage/polarity with a meter before connecting J1.
2. Fit-check J9 against the Tensility drawing and sample. With all power removed,
   confirm continuity from pins 2–3 only when no barrel plug is inserted. Confirm
   pin 3 is otherwise unconnected. Verify K1 selects PD when de-energized and wall
   power when energized, including an unpowered barrel plug and both sources. Use a
   regulated center-positive 12 V adapter rated no more than 3 A.
3. Confirm the owned ADS1115 has local bypassing and SDA/SCL pull-ups to VDD.
4. Fit-check U2, J2, J4–J6, the ADS1115 socket/support, 5807 mounting stack and USB cable overmold.
5. Measure the WT32 plus MG90S 5 V startup/current transients and the actual
   blower current. Verify the shared RJ45 ground contact under combined load.
6. Confirm antenna, enclosure, screw, rear-component, barrel-plug and USB clearances
   using the [current enclosure fit prototype](../../enclosure/carrier-case.md).
   It has not passed physical fit testing. Earlier perfboard enclosure SCAD/STLs
   remain legacy designs and do not fit this carrier.
7. Validate the routed power paths against measured current, voltage drop and
   enclosed temperature. Confirm the combined fan/servo return stays within
   J2's 1.5 A/contact rating and D2 is suitable for the measured freewheel load.
8. After any CAD edit, rerun ERC, DRC, parity and drawing checks, then inspect
   regenerated Gerbers and plated/nonplated drills. Use the verified release ZIP
   rather than an intermediate routing or export file.
9. Bring up from a current-limited bench supply with loads disconnected, then
   test the blower and servo separately and together.

## Key sources

- [TSR 2-2450N product page](https://www.digikey.com/en/products/detail/traco-power/TSR-2-2450N/25903121)
- [Tensility 54-00133 product page](https://www.tensility.com/products/54-00133)
- [Tensility 54-00133 drawing](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf)
- [Adafruit 5807 product page](https://www.adafruit.com/product/5807)
- [Adafruit HUSB238 guide](https://learn.adafruit.com/adafruit-husb238-usb-type-c-power-delivery-breakout)
- [Hynetek HUSB238 product page](https://en.hynetek.com/2421.html)
- [Infineon IRF5305 product page](https://www.infineon.com/part/IRF5305)
- [TDK PS1240P02BT product page](https://product.tdk.com/en/search/sw_piezo/sw_piezo/piezo-buzzer/info?part_no=PS1240P02BT)
- [Traco TSR 2N series datasheet](https://www.tracopower.com/tsr2n-datasheet)
- [User-identified ADS1115 module](https://components101.com/modules/ads1115-module-with-programmable-gain-amplifier)
- [WT32-SC01 Plus V1.3 manual](https://github.com/janick/WT32-SqLn/blob/main/docs/WT32-SC01-Plus-V1.3-EN.pdf)
- [Same Sky MJ1-2503A drawing](https://www.sameskydevices.com/product/resource/mj1-2503a.pdf)
- [Amphenol RJHSE-x080 drawing](https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/rjhsex080.pdf)
- [HeaterMeter blower/servo wiring](https://github.com/CapnBry/HeaterMeter/wiki/Blower-and-Servo-Wiring)

No parts have been ordered and no manufacturing files have been submitted.
