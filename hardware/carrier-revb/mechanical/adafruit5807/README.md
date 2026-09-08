# Adafruit 5807 direct carrier mount

The active Rev B-T2F0-A5807-S4 design mounts the Adafruit 5807 HUSB238 breakout
directly above the carrier at its power short end. No printed cradle is required.
The carrier mounts independently in the bottom shell on a 51 × 58 mm M3
pattern; the WT32 belongs to the top assembly. See the
[current enclosure fit prototype](../../../../enclosure/carrier-case.md).

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
layout view. The carrier remains shifted 4.5 mm toward the power end, while
only the USB module moves back 2 mm. Its socket is now 2 mm behind the exterior,
level with the floor of a 2 mm-deep, 20 × 10 mm outside recess. Its fitted
10.14 × 4.7 mm r7 opening clears the declared metal shell, thickness/spacer
allowances and installation lift; the cable
housing sits in the exterior recess. The module PCB clears the normal inner
wall by 0.643 mm and its reserved mounting envelope by 0.533 mm. The pocket's
integral internal backing has blind PCB/spacer/head clearances, retaining at least
0.943 mm of plastic locally. No board/hardware cutouts reach the outside.
The H5/H6 drill edges retain 2.983 mm to the carrier power edge. Verify the actual
cable boot, plug seating and mounting stack before final printing. Earlier
perfboard case SCAD/STLs are
legacy files and do not fit this carrier.

## Provisional hardware stack

Install each fastener from the module side as:

```text
M2 screw head -> washer -> 5807 -> 3 mm nylon spacer -> carrier -> washer -> M2 nut
```

Use ordinary M2 nuts, screw heads no larger than Ø4 mm and washers no larger
than Ø5 mm, with 3 mm spacers also no larger than Ø5 mm. Keep the combined head and washer height above the module PCB at
most 2 mm, within the enclosure's reserved clearance. Verify the underside stack
height before substituting locking nuts or other hardware.
M2 x 10 mm screws are a starting length, not a released specification. Verify
thread engagement and clearance to the WT32 before purchasing a production
quantity. Add one 3 mm-high adhesive insulating support under the rear/free end
of the module so the two front screws do not allow it to rock. Keep that support
away from module components and solder joints.

Do not install the supplied 3.5 mm terminal block if it interferes with the
stack. Instead, solder a short red/black 20-22 AWG pair from the 5807 V+/GND
output pads to the J1 harness. Secure and insulate the wire; it must not carry
USB insertion force.

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
