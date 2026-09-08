# Rev B-T2F0-A5807-S4 carrier wiring

This net list matches the fuse-free KiCad engineering draft in
[`hardware/carrier-revb`](../hardware/carrier-revb/README.md). The PCB has two-layer routing;
the [JLCPCB package](../hardware/carrier-revb/fabrication/jlcpcb-2026-09-06/README.md)
targets a small bare-board prototype run. Physical fit and load qualification remain.

## External connectors

- J2: HeaterMeter-compatible unmagnetized RJ45/8P8C output. **Not Ethernet.**
- MOD1: Adafruit 5807 USB-C PD power inlet, mounted through H5/H6 and connected
  to J1 with a short 20-22 AWG red/black pair.
- J9: Tensility 54-00133 5.5 × 2.1 mm center-positive 12 V inlet.
- K1: automatic wall-priority changeover relay inside the enclosure; JP2 is removed.
- J4/J5/J6: PCB-mounted 2.5 mm mono probe jacks for PIT, MEAT 1 and MEAT 2.
  They face one short end of the landscape enclosure. The opposite short end
  groups USB-C power, J9 barrel power and the powered J2 fan/servo RJ45.

## Power

```text
Adafruit 5807 V+  -> J1 pin 1 -> PD_12V -> K1 NC
Adafruit 5807 GND -> J1 pin 2 -> GND

Adapter center -> J9 pin 1/A -> WALL_12V -> K1 NO and coil
Adapter sleeve -> J9 pin 2/B -> GND
J9 pin 3/C -> unused (normally closes to pin 2/B, NOT pin 1/A)
K1 COM -> +12V
K1 coil -> raw WALL_12V / GND
D3 across coil: cathode WALL_12V, anode GND
K1 de-energized = USB-PD; energized = wall input

+12V -> U2 pin 1 (VIN)
GND  -> U2 pin 2
U2 pin 3 (5 V) -> +5V

+5V -> JP1 -> +5V_WT32 -> WT32 EXT pin 1
+5V --------------------> RJ45 pin 3 (MG90S supply)
GND ---------------------> WT32 EXT pin 2 and RJ45 pin 4
```

U2 is the fixed-output Traco TSR 2-2450N. Do not fit a Mini100 or adjustable
module in this 3-pin footprint. Configure MOD1 for a 12 V / 3 A request and
meter-check voltage and polarity before connection.

Use a regulated 12 V, 5.5 × 2.1 mm, center-positive wall adapter rated no more
than 3 A. K1 is the G5Q-1 DC12 SPDT relay: its coil is powered directly from
WALL_12V and draws approximately 33.3 mA / 0.4 W. The changeover contact selects
one positive input at a time. With both inputs connected, wall power has priority;
an unpowered barrel plug leaves USB-PD selected. JP2 is removed.

Switchover may briefly interrupt power and restart the controller. D3 suppresses
the coil but slows release. This is wall-presence selection, not a voltage
supervisor: use a regulated adapter and test brownout, contact inrush and restart
behavior with the actual loads. K1 NC is rated 3 A at 30 VDC; NO is 5 A at 30 VDC.
See the [Omron G5Q datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf).

The S2 wiring used J9's sleeve switch as a positive selector and would short PD
to ground with an empty jack. Use the corrected S4 mapping above.

F1–F4 are absent. Use only protected/current-limited regulated 12 V sources
rated no more than 3 A.
The carrier and output branches do not have independent overcurrent protection.
JP1 is retained only to isolate the WT32's carrier 5 V feed when its USB port is
used; it is not a fuse.

C1/C2 decouple +12V to ground. C3 (470 uF) and C4 decouple +5V to ground. D1,
C5, C7 and C13 are removed. For a 12 V request the 5807/HUSB238 overvoltage
shutdown acts below the former P6KE18A's minimum breakdown; C3 consolidates the
former two 5 V bulk capacitors.

## WT32 EXT

| EXT pin | Net | Carrier connection |
|---:|---|---|
| 1 | +5V_WT32 | From +5V through JP1 |
| 2 | GND | Common ground |
| 3 | GPIO10 | ADS1115 SDA |
| 4 | GPIO11 | ADS1115 SCL |
| 5 | GPIO12 | R2/Q2 blower command |
| 6 | GPIO13 | R4/R5 servo signal |
| 7 | GPIO14 | R6/passive piezo |
| 8 | GPIO21 | Unconnected spare |

## WT32 DEBUG analog supply

| WT32 DEBUG pin | J7 pin | Connection |
|---:|---:|---|
| 2 | 1 | +3V3_A for ADS1115 and probe excitation |
| 7 | 2 | Ground |

No 3.3 V LDO is fitted. Never inject an external supply into J7. Verify the
actual DEBUG orientation and loaded 3.3 V rail; keep motor current out of this
harness. The carrier has no C7/C13 or R17/R18: install the ADC module only after
confirming it has local supply bypassing and SDA/SCL pull-ups to VDD.

## Blower, servo and buzzer

```text
                       Q1 IRF5305PBF P-channel
+12V ---------------- source
+12V -- R1 1k ------- gate
                       drain -----------------> FAN_OUT -> RJ45 pin 5
                         |
                         +---- D2 cathode
                              D2 anode -> GND

GPIO12 -> R2 2.2k -> Q2 base
Q2 emitter -> GND; Q2 collector -> Q1 gate
R3 100k from Q2 base to GND

GPIO13 -> R4 220R -> SERVO_SIG -> RJ45 pin 6
SERVO_SIG -> R5 10k -> GND

GPIO14 -> R6 330R -> BZ1 pin 1
BZ1 pin 2 -> GND
```

GPIO12 high turns the blower on. Firmware starts at 100 Hz power PWM with a
100% kick-start; characterize startup, duty range and heating on the actual fan.
D2 is the inductive flyback path and is not an
overcurrent fuse. Drive BZ1 near 4 kHz and hold GPIO14 low when silent; this
direct drive is only for the selected passive piezo.

## HeaterMeter RJ45 pinout

| Pin | T568B conductor | Function |
|---:|---|---|
| 1 | white/orange | NC |
| 2 | orange | NC |
| 3 | white/green | +5 V MG90S supply |
| 4 | blue | Common blower + servo ground |
| 5 | white/blue | Switched 12 V blower supply |
| 6 | green | Servo PWM |
| 7 | white/brown | NC |
| 8 | brown | NC |

RJ45 pin 4 carries combined blower and servo return current. Confirm numbering
through the actual jack/cable with a continuity meter and validate the shared
contact under worst-case load.

## Probe and ADC channels

Each channel uses a 10 k 1% pull-up to +3V3_A, a 1 k series resistor to the ADC
input and a 100 nF input capacitor to ground. On each MJ1-2503A, pin 1 is sleeve/
ground and pins 2/3 both connect to the probe node. Calibrate all three channels;
the 1% bias part can contribute roughly 0.2–0.5 °C worst-case error across typical
cooking temperatures.

| Jack | Bias | Series/filter | ADS1115 |
|---|---|---|---|
| J4 PIT | R10 | R13/C10 | AIN0 |
| J5 MEAT 1 | R11 | R14/C11 | AIN1 |
| J6 MEAT 2 | R12 | R15/C12 | AIN2 |

R16 connects +3V3_A to AIN3 so firmware can use the measured excitation count:

```text
Rprobe = 10000 * raw_probe / (raw_supply - raw_probe)
open   = raw_probe >= 0.98 * raw_supply
```

Keep the probe/ADC region away from the buck converter and blower current loops
when routing.
