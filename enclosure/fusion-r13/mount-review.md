# R13 accessory-mount review

The case retains its custom **72 × 74 mm M3 accessory pattern**, centered at
X±36, Y±37. Four interior Ø10 mm bosses extend from Z2.5 to Z7.5 and join the
floor, walls and closure columns through webs. No exterior projections are
added. The intended purpose is supporting the controller itself; no load rating
or mounting-standard compatibility is claimed.

## Insert and screw geometry

- The selected pilots are **Ø4.2 mm and 5 mm deep**. The user's insert measures
  4.0 mm minimum and 5.0 mm maximum outside diameter; a 4 mm length remains an
  assumption to confirm. No particular supplier insert is prescribed.
- A 4 mm insert installed flush at Z7.5 occupies Z3.5…7.5, leaving 1 mm space
  above the pilot floor. The Ø10 boss retains 2.5 mm radial plastic around the
  maximum insert diameter. The other Ø9 enclosure bosses retain 2.0 mm.
- Exterior screw access remains **Ø3.4 mm through the 2.5 mm floor**. The
  Ø4.2-to-Ø3.4 step is 0.4 mm wide radially. Initial retention is carried by
  the heat-set joint and boss/webs; the floor is **secondary capture only**
  after insert movement, not direct support under a correctly seated insert.
- Target **6.5–7.0 mm actual screw protrusion** from the future bracket's
  case-contact surface. This gives approximately 3–3.5 mm thread engagement
  and keeps the tip below the Z7.5 boss face. Select total screw length only
  after including the bracket and washer thicknesses.

The four accessory inserts bring the total to **16 enclosure inserts**. The
guide, probe, USB and other non-fastener holes are not enlarged by this change.

## Access and physical checks

Install inserts while the shell is empty. The retained working-tool envelope
is Ø8 mm from just above Z7.5 to Z35, with 0.5 mm nominal sidewall clearance
and approximately 0.720 mm clearance to the nearest closure column. Existing
relief behind the front guide stops clears this path without cutting the
seating surface or changing the guide stop.

The 16 × 21 × 10 mm mount coupon checks local insert fit, screw entry and
engagement. It does not include the full wall/closure-column height, so a
successful coupon cannot establish clearance for a larger iron barrel. Match
the actual tool nose to the assumed envelope. Test heat-set grip in the chosen
material and confirm insert length before relying on the engagement figures.

## Verification

The [native checks](native-verification.json) pass for all four external screw
paths and Ø8 mm tool paths. The maximum-OD 5 mm insert envelopes clear other
parts. Four additional minimum-OD 4 mm checks confirm the secondary floor
barrier after the specified 1.5 mm outward displacement. Intentional heat-set
interference is excluded; these checks do not establish pull-out strength.

The [full native STL measurements](insert-hole-verification.json) verify all
16 pilots at Ø4.2 and all 12 plastic M3 screw passages at Ø3.4, at three depths
each: **84 sections pass**. The independent reference passes 37 geometry and
10 mesh checks; all four native part meshes pass comparison with the reference
within the declared 0.03 mm sampled allowance.

Reviewed native archive SHA-256:
`00ab8e3195ccaa0b291149328ca0acde9f45e5b6cc622f8dd61d751e90544316`.
Current source/export hashes are recorded in the verification reports and
package manifest. No remaining geometry objection was found. Material creep,
tightening torque and the future bracket's load distribution remain physical
checks.
