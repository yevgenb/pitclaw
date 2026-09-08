# Actual routed verification

**Routed engineering prototype; physical qualification remains.**

- Logical schematic checks: 104 pin/net pairs agree with the design description.
- PCB: 37 electrical footprints agree with those logical net assignments.
- J8: 10-pin socket for the user-linked blue module; physical fit not yet verified.
- U2: Traco TSR 2-2450N fixed 5 V / 2 A SIP-3; pinout, body envelope and coordinates checked independently.
- Q1: horizontal TO-220 body, G/D/S lead row, 1.4 mm drills and F.Cu live-tab keepout checked. 6.5 mm fitted envelope includes 1 mm insulating support; forming and thermal sample checks remain.
- K1 automatically selects wall power when energized, USB-PD otherwise. JP2 is removed. Eighteen jack/relay/source cases checked for source shorts and simultaneous input paths. Transfer timing, inrush and brownout require physical validation.
- Simplification: D1, C5, C7, C13, R17 and R18 are absent by assertion, along with the previously removed F1-F4/Q3/R7/R19.
- Protection: use only protected/current-limited regulated 12 V sources rated no more than 3 A; there is no onboard or branch-selective overcurrent protection.
- ADC module release gate: confirm local supply bypassing and SDA/SCL pull-ups to VDD before assembly.
- BZ1: direct GPIO14 drive through R6 330 ohm; Q3, R7 and R19 are absent by assertion. Test 4 kHz audibility in the enclosure.
- Adafruit 5807 HUSB238: official 20.32 x 23.495 mm PCB outline and two-hole pattern applied.
- 5807 mounting: 2.4 mm NPTH holes at [(36.753, 87.817), (51.993, 87.817)]; USB-C face is 0.500 mm inside the carrier power edge.
- 5807 mounting: F.Cu/B.Cu track/via/pour keepout present; no electrical-component or carrier-hole courtyard intersects the reserved region.
- Native KiCad ERC: 0 violations. This does not verify module hardware or performance.
- Native PCB/schematic parity: 0 issues. BOM manufacturer and DigiKey identifiers agree for 37 references.
- Native KiCad DRC: 0 reported violations plus 0 unconnected items.
- Copper routing: 314 track/arc segments, 16 vias, 1589.925 mm total segment length.
- Native DRC requires zero unconnected items. Planned power-trunk widths are present; narrower pad escapes and low-current branches are reported individually in summary.json for review.
- Four F.Cu top-washer keepouts cover Ø7.4 mm; circular NPTH exemptions stay within 1.7 mm radius. Underside boss exemptions are checked against the same limit.
- J2: 1.5 A/contact. Pin 4 carries combined blower and servo return; validate actual load, cable drop and contact heating.
- Four 3.2 mm NPTH M3 carrier mounts, 51 x 58 mm pattern; independently fastened to the bottom. WT32 mounts separately to the top via its retainer.

| Power net | Tracks | Total length, mm | Width: length, mm |
|---|---:|---:|---|
| PD_12V | 5 | 21.580 | 2: 21.580 |
| WALL_12V | 17 | 80.020 | 2: 80.020 |
| +12V | 16 | 119.770 | 0.3: 62.071, 2: 57.699 |
| FAN_OUT | 16 | 81.637 | 1.2: 81.637 |
| +5V | 37 | 153.167 | 1.2: 153.167 |
| +5V_WT32 | 5 | 50.461 | 1.2: 50.461 |

Ground zones are measured from actual saved fills:

- GND_FRONT / F.Cu: 3 filled regions, 3070.265 mm².
- GND_BACK / B.Cu: 4 filled regions, 2848.010 mm².
- Ground geometry: J1/J9/U2/C1/C3/D2 remain connected through regions surviving the 2 mm corridor check, joining layers at power-section PTH pads or GND vias. J2's combined blower/servo return also reaches that network at 1.2 mm corridor width. ADC/DEBUG pads are excluded as power-return layer bridges. A 0.01 mm width allowance avoids collapsing exactly nominal-width tracks to zero-area lines; short pad landings are allowed within the erosion distance + 0.05 mm. This checks geometry, not copper temperature, current sharing, PTH/via resistance or voltage drop.

PCB SHA-256: `7d648c85aaa1fabd4f39074680c3daeb83a75353a57960b03cd88eaad8274764`.

Normalized native schematic pin-map SHA-256: `80ddba3ff031a202070c9084cdbf1d001501f4fd21a33c752aad2997ba2095a9`.

Reports are retained without exclusions. Resolve actual violations and all README
release gates before ordering. No electrical load, temperature, antenna, or physical
fit test has been performed.
