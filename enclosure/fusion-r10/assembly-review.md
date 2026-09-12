# Probe fascia assembly review

**Design history:** the dimensions below record earlier proposals. Use the
implemented [r10 print and assembly guide](README.md) and the
[final bezel-key assessment](bezel-key-assessment.md) for current geometry.

Reviewed 2026-09-11. **Use a removable probe fascia captured by the top.** This
keeps the existing carrier installation sequence and avoids relying on a new
tilt maneuver through the tightly fitted power ports and USB blind clearances.
The recommendations below are implementation constraints, not a report that
the final r10 parts have passed collision or physical-fit tests.

## Fixed interface

Keep the PCB and display coordinates unchanged. The fascia's visible entry is
60 × 19 mm at Y−52, centered at Z11.15; its lower edge is Z1.65 and its upper
edge remains Z20.65. The 50 × 12 mm pocket floor remains at Y−44.5, centered at
Z11.65. Depth is still 7.5 mm. The three jack axes stay at X−17/0/+17, Z11.65.

A 2.0 mm floor plate would end at Y−42.5, leaving 1.0 mm nominal clearance to
the seated PCB/jack-body front at Y−41.5. Keep the fascia behind-face geometry
no farther inward than Y−42.0; that only leaves 0.5 mm nominal clearance.
The board's 0.2 mm edge allowance must also be considered. Do not seat the
fascia against jack bodies, soldered pins or the PCB edge.

The concept's Ø4.6 mm holes give only 0.3 mm nominal radial clearance around a
Ø4 mm nose. About Ø5.0 mm plus a small rear lead-in chamfer is a reasonable
starting allowance for a rigid three-hole fascia. Alternatively, deliberate
guide float must accommodate actual jack height and print error. Retain the
approved visible pocket profile and verify the actual three plugs together.

## Positive retention without more screws

- Two side guides locate the fascia in X and Z while it slides inward in +Y.
  Keep fixed guides outside the carrier corridor, preferably at |X|≥31.5.
  The tested PCB envelope reaches |X|30.2; front carrier bosses reach |X|30.0.
- Rear stops on those side guides set the final Y position and the flush jack
  faces. The stops act on fascia ears, not on electronics.
- Two downward keys on the top enter **open-top notches** in the ears. Their
  Y-facing surfaces prevent outward withdrawal after the case closes. Merely
  covering the ears from above would not stop horizontal withdrawal.
- A useful initial key/notch region is |X|≈33–36, Y−48…−46. Keep top keys/ribs
  forward of Y−45.3 to clear the front retainer anchor's Ø10 insertion envelope.
  Join them to the front-wall region; do not run through the retainer pad at
  Z30.1…32.6. Start with 2–3 mm-thick keys and roughly 0.25–0.3 mm running
  clearance, then check actual sweeps and print fit.

Retain the concept's localized pocket backing rather than filling the full
fascia depth up to the seam. A full-depth upper bar would obstruct the existing
locating lip at Y−49.2…−48.5, Z25.6…27.6. The upper joint must preserve that
passage or provide a deliberate matching relief.

The fascia should carry the local lower entry lip. A fixed 2.5 mm-high sill
across the 60 mm mouth would obstruct most of the approved relief down to
Z1.65. A raised mating ledge could also leave the removable lip much thinner
than 1.65 mm; account for the actual split and its clearance rather than adding
the thicknesses of two separated pieces. Support the fascia at its side ears.

## Assembly and removal

1. Install the inserts and USB module. Leave the fascia and top off.
2. Lower the populated carrier at its existing position 4 mm toward the probe
   end, 0.3 mm above the posts; slide it 4 mm toward power, lower and fasten it.
   At the initial position the PCB edge is Y−45.5 and probe noses are Y−48.5.
   Fixed fascia guides or a rear wall must not obstruct this path. Preserve
   the existing maximum 3 mm solder-tail envelope below the PCB.
3. Slide the fascia inward horizontally over the three jack noses until its
   ears meet the rear stops. It should seat without forcing the jacks.
4. Fit the top so its keys enter the ear notches, then tighten the existing
   closure screws. Leave clearance so closure torque does not push the fascia
   into the electronics. Test full plug seating and downward cable clearance.

For service, remove the top, withdraw the fascia, then unbolt and reverse-slide
the carrier. Provide access to the released ears from inside; do not require
pulling on the thin lower cable lip. The carrier must not be reverse-slid while
the fascia remains fitted.

Before release, check the carrier sweep with the fascia absent, fascia insertion
over the seated three noses, top-key engagement with fascia fitted, and reverse
removal. Include the front retainer's insertion passage and the new lower lip
in print checks. The real ThermoWorks plug photo supports the extra entry
clearance but does not qualify the completed printed fit.

## Frozen proposal review

The following selected geometry supersedes the initial guide/key locations and
hole-size suggestions above. The proposal uses open-top bottom guides and two
top keys forward of the retainer passage; no extra fascia screws are needed.

- Bottom guides begin at |X|33.3, giving 3.1 mm clearance from the grown PCB
  envelope. Their outer edges are |X|39. The channel's outer face is |X|36.3,
  leaving a 2.7 mm fence. Cutting the channel through Z8.1 removes the roof of
  the Z0…8 guide, avoiding an unsupported horizontal channel ceiling.
- Tongues occupy |X|32.7…36, Y−52…−43 and Z3.8…5.8. They rest on the Z3.8
  ledges; rear stops at Y−43 set insertion depth. The stop material extends
  to Y−40.5 and is 2.5 mm thick. The fascia rear plane at Y−42.5 clears the
  grown carrier edge at Y−41.7 by 0.8 mm.
- Top keys are 6 mm wide at X±27, Y−50.6…−49 and Z23…28.6. Their root webs
  overlap the top's front wall. They stay 0.5 mm forward of the retainer
  insertion passage at Y−48.5. Keeper blocks are 9.5 mm wide, Y−52…−47.5,
  Z22.5…25; 6.5 mm-wide notches give 0.25 mm clearance in X and Y and
  2 mm nominal engagement below the block top.
- **The key clearance must remain open through the entire fascia top at
  Z27.3**, approximately to Z27.32. Cutting only through the keeper block to
  Z25.02 would leave main-fascia material in the key's vertical insertion path.
- The open-top guides do not latch the fascia vertically. Before the top is
  fitted it can lift or withdraw; hold it against the rear stops while lowering
  the lid. After closure, the fascia/top gap limits upward motion to 0.3 mm,
  while the keys prevent withdrawal. The Z3.8 ledge and Y−43 rear-stop faces
  are intentional contacts, not clearances to be hidden by a general collision
  tolerance.

The selected Ø5.6 jack holes and Ø6.4 rear lead-ins provide more alignment
allowance while keeping the approved pocket profiles. Test the actual plug
with the fascia at its rear stop and at the approximately 0.25 mm allowed
outward play: outward fascia motion places the fixed jack face behind its
pocket floor by the same amount. Nominal flushness alone does not establish
full plug seating throughout that play.

Printing the fascia with Y−52 on the build plate produces a nominal
72 × 27.3 × 9.5 mm part. The tapered pocket walls build inward gradually; the
floor is a 12 mm bridge at 7.5 mm print height. Any support is accessible
through the 60 × 19 mm mouth. Keepers and guide fit should be represented in
the coupon as well as the pocket, and clean support from the plug seating
surface and holes. These conclusions cover the proposal's geometry; final
native insertion/closure checks and a physical fit check remain required.

## Reinforced plastic keeper assessment

The subsequent reinforced-plastic proposal is geometrically credible and
addresses the thin keeper directly, without additional fasteners. It moves
keepers, keys and notches together to X±25.5. A 12.5 mm-wide block around a
6.5 mm notch gives 3 mm arms. Extending the block rear to Y−45.5 gives a
3.25 mm rear strap; extending its bottom to Z20.8 gives 4.2 mm vertical height.
The notch still needs to remain open through the full fascia top.

Relative to the earlier keeper, arm section area increases about 3.36× and the
rear strap's local bending section about 29.5×, assuming the same span and
material. These are section comparisons, not a strength rating for the whole
retention system. The top key and its nominal 2 mm engagement are unchanged.
Their roots, print bonding and actual pull loads still limit the assembly.

The keeper top at Z25 clears the locating lip at 25.6 by 0.6 mm, or 0.3 mm with
the fascia at its permitted upper position. Its bottom remains above the
pocket's maximum roof at 20.65. The web at |X|30.5…31.75, Y−49.5…−45.5 is
outside the tapered pocket and can connect the outer arm down to Z18. For the
64 × 20 mm backing with 4 mm corner radius, the backing top near |X|31.75 is
about Z19.04; that web provides about 1 mm of real overlap there. It must not
be omitted based on the backing's 21.65 mm height at its center.

No nominal clash was found in this proposed reinforcement. It is a reasonable
plastic prototype to print and test, rather than a reason to add screws by
default. This assessment does not assert that the revised native CAD or a
physical printed keeper has already been validated.
