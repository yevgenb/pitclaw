# Bezel key assessment — reinforced fit prototype implemented

Reviewed 2026-09-11 in response to the concern about the printed top lips.
The implemented R10 keys are now 12 mm wide and 2.1 mm thick, with a 0.4 mm
entry chamfer and reinforced mating keepers. The final CAD/assembly checks pass;
printed strength and repeated-use durability remain unmeasured. No additional
screws or heat-set inserts were introduced. The original analysis is preserved
below, followed by the final implementation review.

## Historical analysis: original section and load path

At each original key, the nominal section is:

| Assembly height | Thickness in the pull direction | Connection |
| --- | --- | --- |
| Z23–25.6 | 1.6 mm | Exposed lower key |
| Z25.6–27.6 | 2.1 mm | Key joined to the existing locating lip |
| At Z27.6 shoulder | 3.5 mm locally | Joined to the bezel shoulder |

The key is 6 mm wide. Its 1.6 mm-thick lower portion projects 2.6 mm below the
locating lip. The whole projection below the main shoulder is 4.6 mm. The key
and locating lip overlap 0.2 mm in Y; their Boolean union provides the stepped
section above. Neither a completely unbraced 4.6 mm tab nor a rigidly supported
2.6 mm tab describes the whole load path accurately.

The keeper engages Z23–25. Assembly is a clearance fit: the keys should enter
without bending or snapping. The existing case screws hold the top down.
The durability concern is a lateral load on the fascia, forced misalignment
during closure, or damage to exposed keys while the lid is removed.

With the top printed face-down, an outward Y force bends the projecting key
and generates tension across horizontal print-layer bonds. Clearance and load
position can make one key engage before the other. Equal force sharing must
not be assumed. Normal electrical plug extraction primarily loads the jack
and PCB; a plug body bearing on the recess can also load the fascia. These
loads have not been measured.

## Historical screening calculation, not a load rating

For a rectangular beam section, nominal bending stress is
`sigma = 6 F L / (b t^2)`. Applying a deliberately illustrative 20 N force to
one key, evaluating immediately below both section transitions, gives:

| Key width | Force applied at keeper mid-height Z24 | Force at tip Z23 |
| --- | --- | --- |
| 6 mm, existing | 16.3 MPa | 20.9 MPa |
| 12 mm, widened-only candidate | 8.2 MPa | 10.4 MPa |

These figures omit corner stress concentration, short-beam effects, local
contact, print voids, temperature, creep, dynamic loads and compliance of the
surrounding lip. They establish useful relative scaling, not safe working
loads. Doubling width halves nominal stress for the same load and section.

For context only, [Prusament's PETG datasheet](https://prusament.com/wp-content/uploads/2022/10/PETG_Prusament_TDS_2021_10_EN.pdf)
reports interlayer adhesion of 18 ± 4 MPa and states that properties depend
strongly on printing conditions. That specimen result is not an allowable
stress for these keys. The user's PETG brand and HT-PLA formulation are unknown.
Neither material option presently qualifies the joint.

## Recommendation that led to the revision

Reinforce both mating features. Enlarging the keeper alone leaves the narrow
bezel key as a plausible failure location. Wider keys, a smooth transition
into their support, and clearance that avoids forced flexing are preferable
to treating the keys as snap catches. Any increased thickness or root radius
must also be checked against the fascia notch, its permitted vertical play,
and the display-retainer insertion path.

The assembly review found room for a 2.1 mm-thick lower key, extending its
rear face from Y−49 to Y−48.5 while keeping its front at Y−50.6. This matches
the existing locating lip's inner edge and preserves 0.5 mm nominal clearance
to the retainer front at Y−48 throughout its straight insertion path. A mating
notch rear at Y−48.25 retains 0.25 mm clearance and leaves 2.75 mm of the proposed
keeper's rear strap. Combined with 12 mm width, this is the preferred candidate
for subsequent CAD checks. Removing the lower thickness step helps locally;
the upper 2.1 mm section still controls the simple beam stress estimate above.
This is an analytical fit assessment, not a newly completed collision test.

A short joint sample printed in the same orientations and material as the
case should be checked for smooth closure, repeated assembly and withdrawal
resistance before printing the full enclosure. A hand-held sample checks local
fit and exposes gross weakness; it does not reproduce all full-case loads.

## Historical paused artifacts

The paused 12 mm-wide candidate is preserved under
`work/keeper-reinforcement-study/paused-wide-key-candidate/`. Its diagnostic run
was canceled before completion. The R10 reference SCAD and verifier were
restored from `work/r10-thin-keeper-reference/` to match the existing meshes.
Restored SCAD SHA-256:
`4fe9a3198ca9390f14120a2f89c34ed95d2afd378bc2ce497dcccf2b7c8cd391`.
That was the state before the implementation documented below. The paused
candidate and thin-key files are historical, not the current print geometry.

## Final independent implementation review

The final source has keys at X±21 with a 12 × 2.1 mm constant section from
Z23.4 upward. The bottom chamfer ends at an 11.2 × 1.3 mm tip at Z23. Keeper
blocks are 18.6 mm wide and 4.2 mm high, with 3 mm side arms, a 2.75 mm rear
strap and connected outboard support webs. No root fillet was added.

The mating clearance is **0.3 mm per X side and 0.25 mm per Y side**. The
chamfer leaves **1.6 mm of full-thickness contact height**, Z23.4…25, rather
than the unchamfered 2 mm. This becomes 1.9 mm at the permitted 0.3 mm fascia
lift. The key/web rear edge remains 0.5 mm ahead of the actual moving retainer.
The keeper top remains clear of the locating lip throughout that permitted
lift. The notches open through the fascia top, so no upper skin blocks entry.

Verification reviewed against the frozen artifacts:

- **24/24 reference fit and assembly scenarios pass**, including continuous
  carrier/fascia sweeps and the approached +0.2999 mm lift endpoint.
- **7/7 reference meshes pass** as single, watertight, consistently wound
  solids. The widened coupon crop X10…43 includes the complete right joint.
- **131 native component/case tests pass**, with no positive-volume clashes or
  timeline health issues. The native retention checks block the specified
  outward, inward and excessive upward translations; they do not measure force.
- All four native/print meshes pass integrity and sampled comparison with the
  reference within the declared 0.03 mm allowance. Their current hashes were
  independently matched to [mesh-verification.json](mesh-verification.json).

Frozen reference SCAD SHA-256:
`b254ba542ad2bcb8e305b896ef5324aa3ea8fb102d517171a3a28076a1230dd2`.
Reference report SHA-256:
`26c761a175be9072f77cd0707bdc9c5c7b5468fcd2ff4e153427d71e1fb1c184`.
Native Fusion archive SHA-256:
`7b8a72a4156941832957eb7e3d6639795637ddd2f38485d4052f308b51262fd7`.

### Printing and assembly qualifications

Print the top display-face down and fascia probe-face down, as supplied. The
key chamfer tapers inward at the end of the print. The fascia has a **12.6 mm
bridge over each keeper notch** as well as the 12 mm pocket-floor bridge.
Inspect these in the slicer: notch supports, if needed, may have to start on
the part rather than the build plate. They must be removable through the open
edge without damaging the keeper or leaving material in its clearance.

Hold the fascia seated while lowering the top. The chamfer improves initial
entry, but the keys still start entering before the main locating lip aligns
the halves; do not force them as snap catches. During service, withdraw the
fascia straight off the three jack noses before lifting it. Check real plug
seating at the rear stop and across the permitted fascia play.

No additional geometry blocker was found in this review. The reinforced
joint is suitable for a physical fit prototype. Print the full joint coupon
and test smooth closure, repeated assembly and withdrawal resistance in the
chosen material. Those checks, and the complete case's real handling loads,
remain necessary before making a durability claim.
