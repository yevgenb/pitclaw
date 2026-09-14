# R12 fascia guide review

Reviewed 2026-09-14. **The CAD mismatch shown in the user's sections is corrected.**
The old guide combined a short raised front cover with a lower inner runner
and an open rear channel. Upper restraint was concentrated near the outside
face, although the lower ledge supported the runner along its length.

R12 replaces that arrangement with constant mating profiles over the complete
**9 mm depth, Y−52…−43**. The raised front cover is removed. Both sides use
the same geometry, mirrored in X.

## Verified geometry

Positive-side XZ profiles, in millimeters:

```text
Runner:   (32.7,3.8), (36.0,3.8), (36.0,5.8), (32.7,9.1)
Receiver: (32.7,3.8), (36.4,3.8), (36.4,5.9), (32.7,9.6)
```

The sloping faces are `Z=41.8−X` and `Z=42.3−X`. They provide a 0.5 mm vertical
separation, equivalent to **0.354 mm normal clearance**. The outer-side gap is
**0.4 mm**. The receiver roof reaches Z10.6, leaving **1.6 mm minimum material**
above the cavity at the receiver body's inner edge, X33.3.

The bearing plane remains **Z3.8** and the inward stop remains **Y−43**.
The taller fascia side web ends at X33, retaining 0.3 mm clearance from the
receiver body beginning at X33.3. The revised profiles preserve the probe
recess, connector locations and existing mounting/tool-access features.

## Evidence checked

- Sections extracted from the reference solids at **Y−51.8 and Y−47** have
  matching front and inner profiles, with maximum numerical variation below
  0.000001 mm. Both rails show the specified side and roof clearances.
  See [guide-section-verification.json](reference/guide-section-verification.json).
- Native verification passes **131 component/case checks**, with no
  positive-volume clashes or timeline health issues.
- Ten native local guide tests cover both rails at five depths. All clear
  nominally and at +0.3 mm upward displacement. At +0.7 mm, every location is
  blocked by its receiver roof, with approximately 0.106 mm³ intersection,
  **without the lid present**. This checks inner guide capture independently
  of the outer face and top keys. See [native-verification.json](native-verification.json).
- The independent reference passes **31 checks and 10 mesh checks**. All four
  native case meshes also pass integrity and sampled comparison against the
  reference within the declared 0.03 mm allowance. Current source, reference
  and print STL hashes were matched to the corresponding reports.

Reference SCAD SHA-256:
`37b97045a014de0b7f250b26c06991e2e7b8c5c206489d3bf380c2b89a6706ca`.
Reference report SHA-256:
`21d141b4c76710e13b368a6feb172652d491a5c18645a54c0cf407b677b61ab9`.
Native Fusion archive SHA-256:
`ca7851904af2cbe75ff7c9a623b59fd13645fee92741013a807a5e538b02906f`.

The correction establishes continuous guide geometry and the stated mechanical
restraint. The intersection volumes are geometric checks, not force or
durability ratings. No further CAD blocker was found in this review.
