# Adafruit 5807 direct carrier mount

The active Rev B-T2F0-A5807-S4 design mounts the Adafruit 5807 HUSB238 breakout
above the carrier at its power short end using a
[printed base](../../../../enclosure/fusion-r13/usb-base/README.md). The base
replaces both nylon spacers and the adhesive rear support while preserving the
3 mm module seating height and existing M2 mounting hardware.
The carrier mounts independently in the bottom shell on a 51 × 58 mm M3
pattern; the WT32 belongs to the top assembly. See the
[current enclosure fit prototype](../../../../enclosure/fusion-r13/README.md).

The geometry in `interface.json` is transcribed from Adafruit's published Eagle
board file:

- module PCB outline: 20.32 x 23.495 mm;
- two 2.5 mm plated module holes, 15.24 mm center-to-center;
- carrier hole centers: H5 = (36.753, 87.817) mm and H6 = (51.993, 87.817) mm;
- module envelope: X = 34.340–54.660 mm, Y = 66.862–90.357 mm;
- module PCB front edge is 1.643 mm inside carrier Y = 92.000 mm;
- USB-C connector face at (44.500, 91.500) mm: 1.143 mm beyond the module
  PCB and **0.500 mm inside the carrier edge**;
- Ø5 mm maximum M2 hardware uses a Ø5.3 mm reserved PCB footprint envelope.

Coordinates are relative to the carrier's upper-left board corner in the KiCad
layout view. The carrier remains shifted 4.5 mm toward the power end. The
existing socket position is 2 mm behind the exterior,
level with the floor of a 2 mm-deep, 20 × 10 mm outside recess. Its fitted
10.14 × 4.7 mm r7 opening clears the declared metal shell, thickness/spacer
allowances and installation lift; the cable
housing sits in the exterior recess. The module PCB clears the normal inner
wall by 0.643 mm and its reserved mounting envelope by 0.533 mm. The pocket's
integral internal backing has blind PCB/spacer/head clearances, retaining at least
0.943 mm of plastic locally. No board/hardware cutouts reach the outside.
The H5/H6 drill edges retain 2.983 mm to the carrier power edge. Verify the actual
cable boot, plug seating and new base stack during installation. Earlier
perfboard case SCAD/STLs are
legacy files and do not fit this carrier.

## Hardware stack

Install each fastener from the module side as:

```text
M2 screw head -> washer -> 5807 -> printed base (3 mm total seat) -> carrier -> washer -> M2 nut
```

Use the existing M2 screws and ordinary nuts, screw heads no larger than Ø4 mm
and washers no larger than Ø5 mm. The base has Ø2.4 mm holes on the unchanged,
asymmetric 15.24 mm pitch. Its 0.8 mm floor is included in the 3 mm seat;
do not add the old spacers or adhesive support. Keep the combined head and washer height above the module PCB at
most 2 mm, within the enclosure's reserved clearance. Verify the underside stack
height before substituting locking nuts or other hardware.
M2 x 10 mm screws are a starting length, not a released specification. Verify
thread engagement and clearance to the WT32 before purchasing a production
quantity. The printed perimeter bearing and rear support replace the former
separate rear support. Rear stops resist insertion; the two M2 clamps carry
extraction. The small front/corner guides are not a strong extraction stop.

Do not install a terminal block under the module. Solder a short red/black
20–22 AWG pair from V+/GND to the J1 harness, routing over the module's top
through the **5.1 mm gap between the rear stops** (Eagle u=7.8…12.9 mm). Do not
trap wires under the bearing surfaces. Secure and insulate the wire; it must
not carry USB insertion force. Trim solder tails to at most **2.5 mm below the
module underside**, leaving 0.5 mm above the carrier. The underside windows
clear the modeled PTH solder, USB shell stakes and locating pegs; inspect the
actual solder before tightening the board flat onto its seat.

The base prints flat without supports, in the same PETG/HT-PLA process used for
the case. The original four case parts have unchanged geometry and need no
reprint. The new base's physical fit remains to be checked.

The breakout ships in its 5 V / 1 A configuration. Following Adafruit's guide,
open the 5 V selection and bridge the 12 V and 3 A selections; do not leave two
voltage selections bridged. Perform this before connecting J1, then verify
voltage and polarity with a meter. J1 feeds `PD_12V` into K1's normally closed
contact. Raw wall input energizes K1 and selects the wall adapter instead.
JP2 is removed; no internal adjustment is needed. J9's normally closed sleeve
contact (pin 3) remains unused. A supply change can briefly restart the controller.
The carrier remains fuse-free and is intended only for protected/current-limited
regulated 12 V sources rated no more than 3 A.

## Reproduce the mechanical interface

From `hardware/carrier-revb`, using KiCad 9 Python:

```sh
python3 tools/export_enclosure_interface.py
```

This reads the existing routed PCB without rebuilding it. Do not run the draft
board generator merely to refresh the enclosure interface. Export after any
intentional placement change so the case uses the current mounts and socket faces. These checks do not replace physical cable, screw-stack or enclosure
fit testing.

Sources:

- [Adafruit 5807 product](https://www.adafruit.com/product/5807)
- [Adafruit HUSB238 guide](https://learn.adafruit.com/adafruit-husb238-usb-type-c-power-delivery-breakout)
- [Adafruit published PCB source](https://github.com/adafruit/Adafruit-USB-Type-C-Power-Delivery-Dummy-Breakout-PCB)
