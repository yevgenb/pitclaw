# R13 guide and seam review

R13 promotes the accepted joint-fit geometry to both guides of the full case.
The guide roof and outer-side clearance remain continuous along the 9 mm
engagement. The lower surface deliberately uses relieved travel sections,
ramps and two bearing lands.

| Feature | Accepted geometry |
|---|---|
| Outer-side clearance | 0.30 mm |
| Normal roof clearance | 0.40 mm, equivalent to 0.5657 mm vertically |
| Lower running clearance | 0.30 mm; receiver floor Z3.5 |
| Seating lands | Z3.8 at Y−50…−49.2 and Y−44…−43 |
| Rear stop | Y−43 |
| Minimum receiver roof | Approximately 1.534 mm |
| Fascia side / upper / rear-floor joints | 0.20 mm each; rear-floor gap is along Y |

The male profile is unchanged. On the positive side the receiver outer wall is
X36.3, leaving 2.7 mm of material to X39. Its roof is
`Z=41.8+sqrt(2)*0.4−X`. The opposite guide is mirrored. The floor follows:

```text
(Y,Z): (−52.1,3.5), (−50.6,3.5), (−50,3.8), (−49.2,3.8),
       (−48.6,3.5), (−44.6,3.5), (−44,3.8), (−43,3.8)
```

The early ramp raises a low-running fascia at insertion offsets −7.6…−7 mm,
before the collars enter near −2 mm. The long runner stays over the front land
afterward. The rear land provides a second support about 6.1 mm away, preserving
the original seated height and controlling pitch. The two lands intentionally
contact the runner; they are not lower-clearance regions.

The fascia's upper edge is Z27.4, and key notches extend through Z27.42. Only
the bottom floor strip extends rearward to Y−42.2. The probe plate remains at
Y−44.5…−42.5 and its axes remain Z11.65. The top/bottom seam remains Z27.6.
The lip's outer radius is 2.2; its inner radius stays 1.0.

Sideways and upward offsets are coupled by the sloping guide. Their nominal
clearances are not independent movement allowances. The clamped coupon uses
the actual case screw and tall closure post, rather than relying on hand
pressure alone. Smooth seating must precede screw tightening.

## Verification

The promoted full R13 reference passes **37 geometry and 10 mesh checks**,
including the low-entry slide/rise, both bearing lands and closure with the
fascia. Native checks pass 131 component/case pairs, ten local guide-capture
checks and eight seating-land checks. The allowed +0.1999 mm fascia lift is
clear; larger specified motions meet their retaining surfaces.

The [full native mesh measurements](running-clearance-verification.json)
confirm the accepted gaps at 14 sections across both guides, including ramps
and lands. All four native case meshes pass integrity and sampled comparison
with the reference within 0.03 mm. Their native, reference and print hashes
were checked against [mesh-verification.json](mesh-verification.json).

The unchanged key chamfer leaves 1.6 mm of full-face keeper engagement at the
seated datum, increasing to 1.8 mm at the 0.2 mm upper stop. Its notches remain
open through the raised fascia edge. No added hardware is used for retention.

Reference source SHA-256:
`4531ee58aa448ceb6a8686a38cc279357e2b913e9a52384ae681c15a8758413c`.
Reference report SHA-256:
`7f9874e066741a7a4ae35eb564d4a64a0780356dde2a0d08856bf8f5161a14c9`.
Native archive SHA-256:
`8198eecc4b9cd7a57a5312d8c23e085012d4658d8eb8328b3f4c280ce7d9437d`.

No additional geometry blocker was found. Full physical assembly and printed
durability remain to be checked; intersection volumes are not force ratings.
