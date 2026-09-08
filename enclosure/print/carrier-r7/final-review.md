# Independent r7 print and assembly review

Reviewed 2026-09-07. **No further confirmed CAD blocker was found for printing
these five parts as fit prototypes.** This review used the frozen SCAD, actual
STL cross-sections and print previews. It did not operate a printer or slicer.

SCAD SHA256: `020d5e0470524c1742362970488d83ba45f6cac7366a4743800ca568c94a07bf`.
The five STL hashes agree with [export-manifest.json](export-manifest.json).

## Checks completed

- Independently loaded every STL: each is one connected, watertight solid with
  consistent winding and its lowest surface at Z=0. Top, bottom and retainer
  are correctly oriented face down, open side up and flat, respectively.
- Actual bottom-mesh sections confirm the 1.0 mm carrier-channel exterior skin,
  0.943 mm local USB PCB skin, 0.983 mm hardware skin and 1.5 mm floor at the
  shifted pocket's upper edge. The pocket and its backing move together.
  The channel/pocket separation is 0.8 mm in the final source.
- The retained short-end locating lip is 0.7 mm thick; retainer end rails remain
  1.6 mm wide. The rejected enlargement that would leave a 0.3 mm lip is absent.
- Insert coupon sections confirm Ø4.0/4.1/4.2 mm pilots, Ø9 mm bosses, 5 mm bore
  depth and an intact 2.5 mm floor. Its bores open upward. Labels identify the
  sequence; their fine engraving may need a pen mark on a coarse print.
- Nominal screw engagement remains 3.9 mm for M3×6 carrier screws with 0.5 mm
  washers, 3.5 mm for M3×6 retainer screws, and 3.9 mm for M3×18 closure screws.
  The case screws have 1.1 mm nominal bore-bottom clearance. Insert and driver
  access is available before installing the corresponding electronics.
- The matching [verification report](fit-verification.json) passes all 12
  nominal/tolerance scenarios. The shell-closure output was independently
  checked: it is only the intentional Z27.6 seam plane, with zero thickness
  and volume, rather than a solid clash. Other collision checks require empty
  intersections.

## Printing and physical fit

The working assumption is a 0.4 mm FDM nozzle. The sub-1 mm USB skins are thin
features: inspect that the slicer preserves continuous walls. Port roofs span
up to 16.75 mm and the head counterbores also require bridges. Check cooling and
local supports in the slicer; any supports in the shallow blind channels must
be removable. Prusa's [modeling guide](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
explains that wall paths and unsupported bridges depend on nozzle and settings.

Print the two coupons first. The power-end coupon reproduces the actual ports,
blind reliefs and support ledges, but the full carrier must be held level beyond
it. It does not validate the four M3 mount positions. Locate the USB socket face
against the recessed floor before tightening its module hardware: the modeled
±0.2 mm placement variation is in X, while the blind clearance in Y remains
0.2 mm. The USB boot pocket has 4.5 mm below and 5.5 mm above the nominal socket
axis; actual cable-body fit and complete plug seating remain unmeasured.

At the tested stack extremes the USB shell opening retains only 0.18 mm vertical
margin before printer error. The thin skins, tight carrier M3-hole alignment,
insert fit, probe plug reach and 7.5 mm recess still require physical checking.
The insert coupon helps select a pilot; it does not establish screw torque or
align all four inserts to a real board.

Measure the purchased WT32's blind bosses and choose its small screws before
fastening the retainer. Establish the glass-pad compression from that module,
and check the rear connectors, harness and fully seated ADC height. The hard
stops separate enclosure closure load from the display, but cannot validate
an unmeasured mounting datum. These are prototype prints, without physical
strength, heat or weather qualification.
