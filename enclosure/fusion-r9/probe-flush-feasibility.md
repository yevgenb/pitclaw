# Flush probe face — feasibility assessment only

The r9 model was read without changing CAD, PCB placement or STL files.
All dimensions below are nominal millimeters in the current assembly frame.

| Landmark | Y position / length |
|---|---:|
| Current probe-side outer wall | −52 |
| J4–J6 front collars | −44.5 |
| Current recess | 7.5 |
| Flush RJ45/barrel faces and power-side outer wall | +52 |
| Straight enclosure length with both ends flush | 96.5 |
| WT32 outer envelope | 92, currently −46…+46 |
| Retainer outer length | 96, currently −48…+48 |
| Current enclosure length | 104 |

## A simple trim does not work

Moving only the probe wall to −44.5 with 2.5 mm walls places its inner face at −42.
That conflicts with the current WT32 envelope by 4 mm and retainer by 6 mm.
Even after translating the display, a 96.5 mm outer enclosure with 2.5 mm end walls
has only91.5 mm inside: less than the 92 mm screen before any fit allowance.
The screen pocket needs92+2×0.6=93.2 mm, or98.2 mm outside with those end walls.
The existing retainer and locating-lip arrangement require still more space.

## A compact enclosure redesign is plausible

Keep the PCB fixed. Centering the 92 mm WT32 between the new outer end faces
moves it **3.75 mm toward the power end**. With0.6 mm clearance at each end,
the available end-wall thickness at screen height is:

(96.5−92−2×0.6)/2 = **1.65 mm per end**.

Thus the screen is not an absolute dimensional blocker. The nominal compact
outline can be96.5×86×44.9 mm, but this needs a shorter/reworked retainer,
reworked end registration lips, shifted screen/window, revised anchor positions
and a new assembly sequence. The thick lower connector walls need not all be
reduced to 1.65 mm; thinner upper end walls can accommodate the screen separately.
Actual WT32 rear connectors, cable exits and measured tolerances remain inputs.

The current closed-port installation path cannot be retained. For a vertical
lowering between two flush2.5 mm end walls, the carrier translation would need
to be≥+2.5 mm at the probe end and≤−2.5 mm at the power end simultaneously.
The existing4 mm slide therefore fails. A probe fascia split between the two
halves, open slots closed by the top, or a removable face requires design and
swept-volume checks. A power-end-first tilt is a candidate, not a verified path.

## Alternative: locally flush bottom, unchanged upper footprint

A stepped/tapered lower probe face can move inward 7.5 mm while the screen housing
stays104 mm long. The current Ø10.5 opening roof is atZ16.9. A transition beginning
aboveZ18.9 can slope outward 7.5 mm and reach the old perimeter atZ26.4, below the
Z27.6 seam and Z30.1 retainer underside. This shows available vertical space;
it does not prove a completed wall/port/joint design. The same assembly issue
must be resolved. Overall device length would remain104 mm.

For the 0.4 mm nozzle,1.65 mm is not inherently too thin to print, but it is a
reduced wall allowance and needs slicer/fit checks. Prusa lists approximately
1.35 mm for three and1.8 mm for four 0.45 mm perimeters:
[Prusa modeling guide](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).

Conclusion: exact flush ports and a shorter overall case are geometrically
plausible without a PCB change, with an enclosure/display-mount redesign.
They are not achievable by simply shortening the existing box. No new print
files or manufacturing-readiness claim result from this assessment.
