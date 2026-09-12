# Independent reinforced r10 enclosure reference

This directory contains an independently constructed OpenSCAD reference for the
native Fusion enclosure. Its three exterior pieces are the bottom, top, and
removable probe fascia; the display retainer remains internal. The four complete
parts in the user-facing package are native Fusion exports. The three joint
coupon fragments come from this independently checked reference.

The carrier PCB, screen, connector positions, and 86×104×44.9 mm case envelope
remain unchanged. The approved pocket has a 60×19 mm outer opening, centered at
Z11.15 and Y−52.02, and a 50×12 mm floor at Y−44.5, centered at Z11.65. Its lower
entry is 1 mm lower than the appearance concept. The nominal jack bore is
Ø5.6 mm with a Ø6.4 mm rear lead-in. Real Pro-Series plug seating remains a
physical coupon check.

## Current retention geometry

- Two keeper blocks are centered at X±21 mm, each 18.6 mm wide, extending
  Y−52…−45.5 and Z20.8…25. Their 12.6 mm notches leave 3 mm side arms.
- Notches extend Y−50.85…−48.25 and Z20.78…27.32, through the fascia top. The
  rear strap is 2.75 mm deep; the block is 4.2 mm thick.
- Lid keys are 12 mm wide and 2.1 mm thick, extending Y−50.6…−48.5. Their bottom
  has a 0.4 mm insertion chamfer: 11.2×1.3 mm at Z23 expands to 12×2.1 mm at
  Z23.4, followed by a constant section up to Z28.6. There is no root fillet.
- Each root web is 12 mm wide, Y−51.5…−48.5, Z27.6…29.6. The existing locating
  lip also joins the key from Z25.6 upward. Its rear edge stays at Y−48.5,
  leaving 0.5 mm to the actual retainer front at these X positions.
- Integrated outboard webs occupy |X|29…31.3, Y−49.5…−45.5, Z18…25. They connect
  the keeper blocks to the backing without entering the probe pocket.
- Open-top side guide channels avoid bridge roofs. The outer guide fences are
  2.7 mm thick. Small front runner covers mask the entry gaps.

The nominal key/notch clearance is 0.3 mm on each X side and 0.25 mm on each Y
side. Outward movement is stopped after approximately 0.25 mm of free play.
Even after the entry chamfer, the full key section engages the rear strap over
Z23.4…25, or 1.6 mm height. At the maximum 0.3 mm upward fascia play this height
becomes 1.9 mm. These dimensions establish a mechanical blocking relationship,
not a measured pull-out load or printed material strength.

## Assembly

1. Keep the fascia and top off. Lower the populated carrier at its original
   starting offset, slide it 4 mm toward the power end at 0.3 mm lift, and seat it.
2. Fasten the carrier. Push the fascia straight inward along +Y over the probe
   collars. Its tongues rest at Z3.8 and stop at Y−43.
3. Connect the display harness and lower the assembled top/display/retainer.
   Its chamfered keys enter the fascia notches. The existing four case screws
   close the enclosure; this mechanism adds no screws or heat-set inserts.
4. For service, remove the top, withdraw the fascia, then reverse PCB removal.

## Verification

`verify_reference.py` runs the original 23 declared fit/assembly scenarios and
one additional check approaching the maximum 0.3 mm fascia lift with a 0.0001 mm
numerical margin. The production case
geometry stays nominal while explicit PCB/module thickness and placement
witnesses vary. No check silently incorporates unspecified printer error.

Carrier installation uses continuous swept boxes and cylinders, including the
5.1×8 mm probe housings and separate Ø4 mm collars. Fascia insertion uses a
continuous nonconvex Minkowski sweep over 12 mm. Its line kernel is 0.00001 mm
thick in X/Z; only intentional Z3.8 support and Y−43 end contact are trimmed by
0.0001 mm in the fixed reference to prevent numerical contact artifacts.

Lid closing conservatively sweeps every part of the original lid below the
seam plus full-size prisms enclosing the new chamfered keys. The remainder of
the lid and retainer remain above the highest fixed solid, enforced by height
assertions. Display/retainer insertion into the top is checked separately.
The additional fascia-lift check evaluates +0.2999 mm, approaching the maximum
+0.3 mm play within a 0.0001 mm numerical margin. At exactly +0.3 mm, the fascia
top meets the Z27.6 seam and the front runner cover meets the Z8.1 channel edge.
These are intended stops; the approached endpoint must be an empty intersection.

All seven reference meshes must be watertight, consistently wound, one connected
solid each, and placed at print Z0. Physical print fit, layered material strength,
OEM fasteners, glass preload, wiring, heat performance, and sealing are not
established by these checks.

## Three-piece guide/key coupon

All three fragments use the assembled crop X10…43, Y−52…−40.5. This includes the
entire shifted keeper block, key, and right guide. Print the supplied orientations
and hold the top against the bottom by hand while testing insertion and capture.
The coupon has no case screw clamp and cannot establish full-shell pull-out
strength. Print the actual fascia separately to check the three probe plugs.

| Reference STL | Dimensions, mm | Orientation |
|---|---|---|
| carrier-bottom.stl | 86×104×27.6 | Floor down |
| carrier-top.stl | 86×104×21.9 | Display face down |
| carrier-retainer.stl | 80×96×2.5 | Flat |
| probe-fascia.stl | 72×27.3×9.5 | Probe outer face down |
| joint-coupon-bottom.stl | 33×11.5×27.6 | Floor down |
| joint-coupon-top.stl | 33×11.5×21.9 | Display face down |
| joint-coupon-fascia.stl | 26×27.3×9.5 | Probe outer face down |

The coupon still requires inspection in the slicer, particularly its pocket and
keeper bridges. The key chamfer is an assembly lead-in, not a substitute for
checking the printed key roots and layer adhesion.
