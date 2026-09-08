# Carrier routing — S4 relay prototype

The editable PCB is `pitclaw-carrier.kicad_pcb`. Keep its matching schematic,
project rules and local footprint libraries together. K1 retains USB-PD on NC,
wall power on NO and common ground. No electrical components were added by
the routing pass.

## Copper and placement

The board remains 60 × 92 mm, two layers, 1.6 mm FR-4, with a nominal 35 µm
(1 oz) external copper build assumption. This is a prototype layout, not a
measured temperature-rise or fabrication qualification.

| Path | Routing intent |
|---|---|
| PD_12V, WALL_12V and main +12V | 2.0 mm trunks; short pad escapes may neck down |
| +5V and WT32 +5V | 1.2 mm trunks; short pad escapes may neck down |
| FAN_OUT | 1.2 mm trunk |
| GPIO, probes, ADC and relay gate-bias branch | 0.3 mm minimum |
| Ground | Filled front and back copper, solid pad connections |
| Clearance | 0.3 mm copper spacing, 0.5 mm copper-to-edge minimum |
| Through vias | Minimum 0.8 mm diameter / 0.4 mm drill; power class 1.2 / 0.6 mm |

The narrow +12V branch feeds only R1's gate pull-up, about 12 mA with the
blower on; it is not the blower or regulator supply trunk. Ground pads use
solid connections for return width; they will need sufficient soldering heat.
See `verification/summary.json` for the actual width/length distributions and
track/via counts, including any short router neckdowns.

C2 moved to (15, 65) mm and C4 to (30.5, 70) mm, rotated 270°, to shorten the
regulator's bypass connections. All connector faces, mounting holes, Q1,
relay and module locations remain aligned with the r6 enclosure.

The final review widened J2's shared ground escape to 1.2 mm and moved the
adjacent servo signal through a via at (9, 80.6) mm. This removes the short
0.6–0.7 mm ground throat found after routing; the filled-ground review verifies
its connection to the broader power-return copper.

The JLCPCB review corrected U2's offset body and Ø1.4 mm lead drills, moving
its pin row to (17,70.75) mm. SERVO_SIG now takes a local left-side detour
outside the maximum converter body through two additional signal vias. Two
parallel Ø1.2/0.6 mm GND stitches at (18,78.5) and (20,78.5) mm preserve
the 2 mm main-return check. The original front WALL_12V trunk remains under a
1.54 mm edge strip of the maximum U2 body; keeping it there preserves the broad
back-layer return. This is a documented exception to Traco's under-body trace
guidance, not a claim of complete compliance. The final board has 314 tracks
and 16 vias.

Both copper layers preserve the Adafruit module reservation. The top avoids
Q1's live tab and the M3 washers; the bottom avoids the insert bosses and their
installation sweep, plus the two enclosure support ledges. Circular NPTH
exemptions in the mounting keepouts prevent square-corner copper pockets under
metal hardware. Component references and power labels are on front silkscreen.

## Verification and limits

`tools/check_draft.py` runs fresh native ERC, PCB DRC and schematic parity,
requires all nets connected, and checks source-selection topology, actual pin
assignments, BOM identifiers and mechanical reservations. The independent
review also examines the filled-ground geometry around the power returns; see
`verification/final-electrical-review.md` for its method and limits.

The wide traces do not increase connector or component ratings. J2 pin 4
carries the combined blower/servo return and is rated 1.5 A. Check the actual
blower's freewheel load against D2, the total WT32/servo load against U2's 2 A
rating, and temperature in the enclosure. Physical module fit, harness polarity,
source transfer and load testing remain as listed in the carrier README.

## Editing and reproduction

Schematic updates use `tools/build_draft.py --schematic-only`; this is also the
default and preserves the routed PCB. The explicit unrouted-board rebuild mode
refuses a board containing routed copper. For layout edits, open the native
KiCad PCB, refill zones and rerun verification. Do not replace it with an old
placement preview or an intermediate routing session.

Routing was performed locally with KiCad 9.0.6 and Freerouting 2.1.0, followed
by manual rule/keepout corrections, ground filling, cleanup and native KiCad
checks. Intermediate DSN/SES files are retained under `work/pcb-route` at the
repository root. They are investigation checkpoints, not the final PCB source.

The native layer exporter is `work/render_routed_previews.py` within this
carrier directory. Final SVG/PNG copper and assembly views are under
`previews/routed`; the back view is mirrored as viewed from the solder side.
