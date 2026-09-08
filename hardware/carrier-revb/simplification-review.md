# Simplification review — updated in Rev B-T2F0-A5807-S4

The carrier now contains only parts that serve a distinct electrical or
mechanical function. The requested simplifications are implemented in schematic,
PCB source, BOM and checks.

## DigiKey one-board cost change

| Change | Previous | S4 | Saving |
|---|---:|---:|---:|
| FQP27P06 -> IRF5305PBF | $3.99 | $2.53 | $1.46 |
| CPT-1255C-090 -> PS1240P02BT | $1.50 | $0.67 | $0.83 |
| 1N5819-TP -> SB140 | $0.31 | $0.23 | $0.08 |
| Precision R10-R12 plus R5 -> one common 1% line | $1.99 | $0.40 | $1.59 |
| Six Vishay 100 nF positions -> five TDK positions | $1.70 | $1.25 | $0.45 |
| C3 + C5 -> one 470 uF C3 | $0.55 | $0.52 | $0.03 |
| Remove D1 and C7 | $0.66 | $0.00 | $0.66 |
| Add 12 V wall-adapter inlet | $0.00 | $0.90 | -$0.90 |
| Automatic source relay K1 and coil diode D3 | $0.00 | $2.03 | -$2.03 |
| **Total BOM change** | **$31.38** | **$29.21** | **$2.17** |

Retained prices are the 2026-09-05 DigiKey US snapshot; K1 is from 2026-09-06.
See `bom/selection.json`. The S4 design has 37 populated electrical footprints versus 38 populated plus two DNP
footprints previously. A cheaper RECOM R-78K5.0-2.0 converter was reviewed but
not selected: its approximately $0.96 saving did not justify a taller or wider
right-angle mechanical envelope and a new placement risk in this stack.

| Change | Result |
|---|---|
| Mini100 module/socket/header | Replaced by one TSR 2-2450N THT converter. |
| F1 input PTC | Removed; K1 selects one protected/current-limited 12 V source at a time. |
| F2 WT32 PTC | Removed; +5 V reaches JP1 directly. |
| F3 servo PTC | Removed; +5 V reaches RJ45 pin 3 directly. |
| F4 blower PTC | Removed; Q1 drain reaches RJ45 pin 5 directly. |
| Q3/R7/R19 buzzer stage | Removed; GPIO14 drives passive BZ1 through R6. |
| Separate 3.3 V regulator | Not fitted; low-current ADC rail comes from WT32 DEBUG. |
| Source ORing diode | Not fitted; K1 selects PD by default and powered wall input automatically. J9's sleeve NC contact is unused. |
| D1 12 V TVS | Removed; HUSB238 output OVP acts first for the fixed 12 V request. |
| C3 + C5 bulk capacitors | Consolidated into one 470 uF C3. |
| ADC bypass and I2C pull-ups | Carrier C7/C13/R17/R18 removed; verify these functions on the owned module. |
| Q1 | FQP27P06 replaced by lower-cost IRF5305PBF with the same G-D-S pin order. |
| D2 | 1N5819-TP replaced by lower-cost SB140 with the same rating/package class. |
| BZ1 | Same Sky part replaced by lower-cost TDK PS1240P02BT passive piezo. |
| Probe bias | Common 10 k, 1% resistors replace 0.1% parts; calibrate each channel. |

Parts retained and why:

- Q1/Q2/R1/R2/R3 are the high-side 12 V blower switch and 3.3 V logic interface.
- D2 clamps blower inductive kick; it is not redundant overcurrent protection.
- C1/C2 and C3/C4 provide local rail decoupling for cable, converter, WT32 and
  MG90S load transients.
- R4/R5 establish a defined, protected servo control signal.
- Probe bias/filter components and AIN3 excitation measurement support accurate
  NTC readings in a noisy motor environment.
- JP1 prevents unverified back-powering when WT32 USB is connected.

The resulting fuse-free design depends on protected/current-limited regulated
12 V sources rated no more than 3 A and on test-verified wiring, trace widths,
connector loading and thermal performance. K1 avoids opening the case to change
sources and prevents normal parallel contribution from both sources. Verify relay
transfer/restart, inrush and brownout with the actual loads. J9's sleeve switch
must not be used as a positive-source selector. This is a deliberate prototype tradeoff, not an assertion that
the loads are independently protected.
