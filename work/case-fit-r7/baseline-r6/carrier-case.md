# Landscape carrier enclosure — fit prototype r6

The Rev B carrier enclosure has **two outer parts: top bezel and bottom shell**.
The WT32 display sits inside the top, with a raised plastic rim protecting the
front and edges. A thin removable internal retainer attaches to its rear blind
mounts. The carrier screws independently into the bottom. There is no middle
shell or seam bracket.

![Landscape enclosure](review/carrier-assembled-draft.png)

The current outer envelope is **104 × 86 × 44.9 mm** in landscape orientation,
4.2 mm thinner than the previous 49.1 mm draft. Lower carrier posts save 3 mm
and flat Q1 mounting allows a 4 mm reduction in component height allowance.
The review also corrected the display mounting depth from an unsupported 8 mm
to the drawing's 10.8 mm, which adds 2.8 mm to the stack.
This is a fit prototype: component heights, connector seating and display
mounting still need sample verification. CAD checks do not establish physical fit.

## Connector arrangement

All cable connections are on the opposing **short ends**. USB-C power, the
12 V barrel inlet and the powered fan/servo RJ45 share one end. PIT, MEAT 1 and
MEAT 2 occupy the other. The long sides remain clear of connectors.

![Power end](review/carrier-power-face-draft.png)

The board stays 60 × 92 mm. Coordinates below are in the KiCad component-side
view, with (0,0) at the upper-left board corner. The landscape render rotates
this view 90 degrees.

| Interface | Carrier coordinates, mm | Enclosure treatment |
|---|---|---|
| RJ45 mouth | (9.5, 93.5) | Individual fitted opening; face flush with case |
| Barrel mouth | (26.5, 93.5) | Individual fitted opening; face flush with case |
| USB-C face | (44.5, 91.5) | Socket flush with floor of 2 mm exterior recess |
| Probe mouths | (13, −3), (30, −3), (47, −3) | Three separate Ø10.5 mm openings |
| Carrier M3 holes | (4.5, 4.5), (55.5, 4.5), (4.5, 62.5), (55.5, 62.5) | Ø3.2 mm holes over Ø9 mm insert bosses |
| USB module M2 holes | (36.753, 87.817), (51.993, 87.817) | M2 hardware envelope Ø5 mm maximum |

The power end has separate openings with solid plastic between them. RJ45 and
the barrel jack remain nominally flush with the outside wall. Their fitted
openings are 16.35 × 14.11 mm and 9.6 × 11.7 mm, including print and installation
clearance.

**USB-C fits a small opening in the recess floor.** The 20 × 10 mm rounded
outside pocket is 2 mm deep, level with the socket face. A 9.54 × 4.1 mm
through-opening closely surrounds the metal shell, including print clearance
and the carrier's 0.3 mm installation lift. The cable's plastic housing sits in
the outside pocket. Check that the actual cable fits and the plug seats fully.

An integral backing inside the bottom shell gives the recess floor a nominal
1.5 mm thickness. Small blind clearances behind it accommodate the USB PCB
and M2 screw heads, retaining at least 0.943 mm of plastic locally. These
clearances do not open onto the exterior. The pocket's bottom clears the
separate carrier-edge channel by 0.5 mm. That channel still clears the main
carrier PCB and leaves 1.3 mm of exterior plastic. The USB module stays in
its r5 position and the carrier remains shifted 4.5 mm toward the power end.
Continue to use ordinary M2 nuts and washers no larger than Ø5 mm, within
the reserved hardware envelope. The upper head and washer together must stay
within 2 mm above the USB module PCB.
The probe sockets are now recessed 7.5 mm; their Ø10.5 mm openings admit the
plug bodies. Confirm that the purchased probe plugs can reach and seat fully.

Four M3 carrier mounts use an independent 51 × 58 mm pattern. Two small passive
supports under the power edge resist board flex without adding screws. The
carrier reserves their underside contact patches against copper, pads and vias.
Its four insert bosses also have reserved underside sweeps for the 4 mm
installation slide. R1, R2 and Q2 move clear of those paths.
The WT32's 51.39 × 75.14 mm OEM pattern belongs only to the display retainer.

## Display and assembly stack

![Exploded assembly](review/carrier-exploded-draft.png)

From the bottom exterior toward the display, the provisional stack is:

| Item | Height, mm |
|---|---:|
| Bottom floor | 2.5 |
| Carrier insert bosses | 5.0 |
| Carrier PCB | 1.6 |
| Carrier components and mated harness allowance | 16.0 |
| Clearance to lowest retainer screw | 3.0 |
| Display, retainer and screw envelope | 15.3 |
| Recess below outer bezel face | 1.5 |
| **Total** | **44.9** |

The 15.3 mm display assembly allowance uses the drawing's 10.8 mm distance from
glass front to the OEM rear mounting plane, a 2.5 mm retainer and 2 mm screw
heads. The drawing's 8 mm callouts describe connector lengths along the module,
not its depth. Verify the actual module and rear connectors before assembly.

The 16 mm carrier allowance accounts for the 14 mm maximum seated C1, 13 mm C3,
approximately 13.6 mm RJ45 body, socketed ADC and mated JST-XH harness. K1 needs a local 16.2 mm seated
allowance, including the relay's 0.4 mm molded feet. The case stays 44.9 mm;
its local clearance to the upper assembly is checked separately, at least 2.8 mm.
[JST specifies 9.8 mm assembled height](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)
before the wire exit. The remaining 6.2 mm allows the wires to turn sideways;
verify the actual harness and complete ADC assembly stay within 16 mm. Q1's
flat body reserves 6.5 mm including 1 mm of insulating support and lead-forming
tolerance. Keep its live drain tab inside the carrier's reserved region.

The retainer stays 2.5 mm thick after review: reducing it to 2 mm would nearly
halve its bending stiffness for only 0.5 mm case-depth savings. Keep the 3 mm
nominal inter-assembly gap until the real cables and rear components are measured.

The retainer's four small screws enter the WT32 rear blind bosses. Its two
outer M3 screws fasten into inserts in the top bezel. Hard stops set the mounting
plane; the four case closure screws bear on separate columns. A thin compliant
strip contacts only the inactive display border, with a provisional compressed
thickness of 0.3 mm. Set that spacing from measurements so tightening screws
cannot load or bend the glass. The plastic window clears the active area and
leaves a 1.5 mm front recess. The locating lip has local relief so the retainer
can pass through it during assembly.

The electronics shown in the render are clearance witnesses, not detailed
supplier models. Antenna space, rear components, cable exits and harness bend
radii remain physical checks. Leave a service loop between the halves and keep
wires clear of the lip, bosses and display. Open the case to reach the WT32's
own programming USB port. Power-source selection is automatic; no internal
source selector remains.

## Mounting hardware

| Qty | Hardware | Purpose |
|---:|---|---|
| 10 | Ruthex RX-M3Sx4.0 short heat-set inserts | 4 carrier, 4 closure, 2 retainer anchors |
| 4 | M3 × 6 screws and 0.5 mm insulating washers, OD ≤7 mm | Carrier to bottom; nominal 3.9 mm engagement |
| 4 | M3 × 18 screws, head OD ≤6 mm and height ≤3 mm | Top to bottom; nominal 3.9 mm engagement |
| 2 | M3 × 6 button-head screws, head height ≤2 mm | Retainer to top; nominal 3.5 mm engagement |
| 4 | Small screws suited to the WT32 plastic blind bosses | Retainer to display; diameter and length require the sample |
| 1 | Compliant perimeter strip | Inactive display border; establish preload from fit |

The model starts with a 4.0 mm insert pilot, 5.0 mm blind bore and 9 mm boss OD
for the 4.6 mm OD × 4.0 mm insert. The carrier bore ends at the floor's top,
leaving the full 2.5 mm floor closed. Print an insertion coupon in the chosen
material and verify the bore, melt relief and screw engagement. Do not bottom
screws in the inserts or the WT32 blind bosses. The separate
[5807 hardware stack](../hardware/carrier-revb/mechanical/adafruit5807/README.md)
still uses two M2 screws, four washers, two 3 mm spacers, two nuts and an
insulating rear support. Mechanical parts are unpriced in the electrical BOM.

## Prototype assembly

1. Fit the heat-set inserts before installing electronics. Check each screw's
   engagement and the mating faces on the empty printed parts.
2. With the WT32 face down on a soft surface, attach the retainer from behind
   using four suitable small screws. Confirm the frame clears rear components.
3. Seat the display and retainer in the top bezel with the compliant strip on
   the inactive border. Secure the two retainer anchors without changing the
   measured display preload.
4. Fit the 5807 to the carrier. Trim solder tails to at most 3 mm and check the
   M2 stack. Start the populated carrier 4 mm behind its final position, toward
   the probe end. Lower it until its underside is 0.3 mm above the insert bosses,
   slide it 4 mm toward the power end to enter the three fitted openings, then
   lower the final 0.3 mm and fasten the four M3 screws. Reverse this sequence
   for removal. Do not force a board straight down into the closed port wall.
5. Fully insert all cable plugs and exercise the RJ45 latch. Connect the internal
   harness with enough slack to open the top for service.
6. Close the locating lip and secure four M3 × 18 screws. Confirm wires remain
   clear, the seam seats freely and the glass is not clamped by closure torque.

## Files and printing

- [Parametric OpenSCAD source](carrier-case.scad)
- [Top STL](review/carrier-top-draft.stl)
- [Bottom STL](review/carrier-bottom-draft.stl)
- [Internal retainer STL](review/carrier-retainer-draft.stl)
- [Section view](review/carrier-section-draft.png)
- [Verification results](review/verification.json)

The single-part exports are oriented for printing: top face down, bottom open
side up and retainer flat. Inspect the slicer's bridges/supports around the three
port roofs and blind channels; remove support material before installing the PCB.
Choose the final material and wall settings after the insert coupon and fit
test. These files do not establish weather resistance or a thermal rating.

After rebuilding the carrier CAD, run
`hardware/carrier-revb/tools/export_enclosure_interface.py` with KiCad Python.
It writes the shared `carrier-interface.scad` from the placed board. Export
`part="top"`, `"bottom"` and `"retainer"` from `carrier-case.scad` after changes;
`"assembled"`, `"exploded"` and `"section"` are review views.

## Review decisions and remaining measurements

Independent carrier and enclosure reviews challenged placement, screw hardware,
glass loads and the assembly path. The resulting fixes separated the carrier
mounts from the WT32 pattern, reserved support contacts under the power end,
provided plug access, connected the locating lip to the
top and relieved its opening for retainer insertion.

The thinning review retained the 2.5 mm retainer and 3 mm clearance after
challenging their stiffness and cable space. It replaced the long inserts with
the common short M3 version, moved Q1 into a flat mounting footprint and
corrected the WT32 rear mounting plane. The current seam retains the existing screw grip while preserving at least 2 mm
of plastic above each fitted opening. The 5807 M2 screw ends and all solder leads must clear the lowered
carrier's floor space. The fitted-port review moved the carrier and power faces, kept solid webs
between connectors, and corrected the barrel front profile to
9 × 10.8 mm with its bore 6.5 mm above the PCB, and checked the populated carrier's
lower/slide/seat path against the shell. This includes actual THT pad positions
with conservative solder envelopes, rather than only a flat PCB witness. The
r6 refinement replaces the oversized USB cable-body opening with a fitted
socket opening and makes the recess floor level with the socket face. Internal
backing strengthens the pocket, with blind PCB/head clearances. The rest of
the stack and the automatic power circuit remain unchanged.

Before treating this as a finished enclosure, measure the WT32 boss depth,
glass perimeter and rear-component/cable envelope; connector heights and real
plug bodies; carrier solder protrusions; insert fit and screw engagement.
The carrier still needs routing and electrical bring-up. Keep the initial
enclosure simple; an external stand can be designed later around the bottom.

Sources: [WT32-SC01 Plus V1.3 manual](https://github.com/janick/WT32-SqLn/blob/main/docs/WT32-SC01-Plus-V1.3-EN.pdf),
[Ruthex short insert dimensions](https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck),
[Tensility jack drawing](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf),
[Amphenol RJ45 drawing](https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/rjhsex080.pdf),
and [Adafruit board CAD](https://github.com/adafruit/Adafruit-USB-Type-C-Power-Delivery-Dummy-Breakout-PCB).
