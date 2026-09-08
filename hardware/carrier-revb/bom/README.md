# DigiKey prototype BOM — Rev B-T2F0-A5807-S4

The current BOM matches the fuse-free native CAD revision. U2 is the through-hole
**Traco Power TSR 2-2450N**, DigiKey **1951-TSR2-2450N-ND**, fixed 5 V / 2 A.
The Adafruit 5807 is included as a purchased, screw-mounted module. The Mini100,
its socket/header and F1–F4 are not purchased or fitted. J9 is the Tensility
54-00133 wall-adapter inlet. K1 automatically selects wall power when available,
and USB-PD otherwise. D3 is its coil flyback diode. JP2 and its shunt are removed;
J9's sleeve switch remains unused.

Retained DigiKey US public prices are from 2026-09-05; K1 was checked 2026-09-06. The simplified
one-carrier order subtotal is **$29.21** before shipping, tax or tariff:

| Scope | Subtotal |
|---|---:|
| Carrier parts plus Adafruit 5807 | $28.25 |
| Harness mates/contacts and JP1 shunt | $0.96 |
| Total | **$29.21** |

The workbook chooses price-break quantities when buying extra is cheaper.
Refresh price and stock before checkout; this snapshot is not a quote.

## Files

- `selection.json`: source of exact MPNs, DigiKey SKUs, price tiers, stock
  snapshots, descriptions and assembly cautions.
- `pitclaw-carrier-digikey-bom.xlsx`: editable order, detailed parts and unpriced
  assembly requirements.
- `pitclaw-carrier-digikey-import.csv`: initial 27-line DigiKey import file.

The CSV does not recalculate if workbook quantities are edited.

## Deliberate omissions and substitutions

- **F1–F4:** removed from schematic, PCB and BOM at the user's direction. Use
  only protected/current-limited regulated 12 V sources rated no more than 3 A.
  There is no onboard or branch-selective overcurrent protection.
- **Mini100:** replaced by the soldered TSR 2-2450N; no module socket or support
  is required.
- **Source selector:** K1 is G5Q-1 DC12 (Z221-ND), with an SB140 D3 across
  its raw-wall-powered coil. NC selects PD, NO selects wall, COM feeds +12V.
  NC is rated 3 A/30 VDC and NO 5 A/30 VDC; the coil draws approximately 0.4 W.
  Do not substitute the SPST G5Q-1A. Automatic transfer may restart the controller.
  The relay and D3 replace the JP2 header/shunt, adding $1.59 to S3.
- **Q3/R7/R19:** removed; BZ1 uses direct GPIO14 drive through R6.
- **D1:** removed because the Adafruit 5807/HUSB238 output OVP acts before the
  former P6KE18A's minimum breakdown for a 12 V request.
- **C5:** folded into one 470 uF C3. **C7/C13/R17/R18:** removed; confirm the
  owned ADS1115 module provides local bypassing and SDA/SCL pull-ups to VDD.
- **Q1:** IRF5305PBF replaces FQP27P06. **BZ1:** TDK PS1240P02BT replaces the
  Same Sky piezo. **D2:** SB140 replaces 1N5819-TP.
- **R10-R12:** common 10 k, 1% resistors replace 0.1% parts. Calibrate each probe
  channel; the calculated worst-case bias contribution is about 0.23–0.45 °C
  across 25–150 °C for a B≈3950 probe.

Converter short-circuit protection is not a precise 2 A branch limiter. The
datasheet's typical current-limit value for this model is 360% of rated load,
so actual wiring and loads still need bench testing.

## Not included in the subtotal

WT32-SC01 Plus, owned ADS1115, bare PCB, 5807 fasteners/support,
optional regulated 12 V / 3 A wall adapter, WT32-end harness connectors, wire,
crimp tooling, probes,
HeaterMeter blower/MG90S assembly, shipping, taxes and tariffs are excluded.

This is a purchasing aid for a routed engineering prototype, not authorization to
order the PCB.
