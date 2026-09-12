# Physical PCB handedness correction

Reviewed 2026-09-11. **The r7/r8 bottom-shell coordinate mapping was reflected
relative to the manufactured PCB.** The physical correction is to mirror the
bottom across X=0, while placing the actual KiCad STEP with a proper 180°
rotation about Z. The PCB itself must not be mirrored or changed.

## Evidence from the actual STEP

The STEP assembly relationships were followed from named component occurrences
to their placement transforms. All 22 exported supplier-component placements
match `STEP X = board X − 30`, `STEP Y = 46 − board Y` exactly, with their local
Z axes pointing upward. Board coordinates here omit KiCad's (100,50) offset.

| Landmark | Board XY, mm | Native STEP XYZ, mm |
|---|---|---|
| J7 | 40,12 | 10,34,1.595 |
| D3 | 55,31 | 25,15,1.595 |
| J1 | 54,51 | 24,−5,1.595 |
| Q2 | 5.5,74 | −24.5,−28,1.595 |

The actual board solid also contains the asymmetric Ø2.4 mm USB mounting-hole
axes at STEP XY (6.753,−41.817) and (21.993,−41.817). This independently confirms
the mapping without relying on a component body's drawing origin.
The parsed evidence and source STEP hash are in
[step-coordinate-evidence.json](step-coordinate-evidence.json).

The old case mapping would require `(X, −Y+4.5, Z+offset)` from STEP coordinates.
Its linear part has determinant −1: it is a reflection, not a rigid placement.
The four main mounting holes and three probe positions are symmetric in X, so
checking those alone conceals the error. The asymmetric power connectors and
USB mounting holes expose it.

## Correct placement and parts affected

Use the following proper rigid transform, in millimeters:

```text
case X = −STEP X
case Y = −STEP Y + 4.5
case Z =  STEP Z + 7.5
```

The rotation has determinant +1 and keeps components facing upward. For custom
missing-component witnesses built from board coordinates `(u,v)`, map every XY
point as `(30−u, v−41.5)`. Do not mix that mapping with the old unreflected X.
Fusion API translation values are centimeters: `(0,0.45,0.75)` for this offset.

After correction the power-face centers are RJ45 `(20.5,52)`, barrel `(3.5,52)`
and USB-C `(−14.5,50)` mm. The two USB mounting holes become
`(−6.753,46.317)` and `(−21.993,46.317)` mm.

- **Bottom shell:** mirror the complete solid, including power openings, USB
  recess/backing/reliefs and passive support ledges. Mirroring only the visible
  openings would leave the hidden features on the wrong side.
- **Power-end fit coupon:** mirror with the bottom. The r9 reference derives
  it from the corrected bottom automatically.
- **Top and retainer:** their shapes are X-symmetric and need no handedness
  change. The r8 four-anchor layout is retained. Reference top/retainer STLs
  are byte-identical between r8 and r9.
- **Insert calibration coupon:** no handedness dependency; leave its numbered
  bores and labels unchanged.

The earlier intersection tests checked a case and a witness using the same
coordinate convention. They established their relative clearance, but did not
establish agreement with the manufactured PCB's handedness. The archived r7/r8
bottom and power-coupon files therefore should not be used for the physical
board; use the corrected r9 versions.

## Z datum: rendering versus physical thickness

The STEP substrate's topological vertices span Z0…1.51 mm. Exported pad copper
spans −0.04…1.55, bottom/top mask sheets are at −0.05/1.56, and silk is at 1.585.
Supplier component origins are at 1.595; that is a placement datum, not the
substrate thickness.

The chosen +7.5 mm offset places the substrate origin on the nominal support
plane and component origins at 9.095, within 0.005 mm of the case's nominal
PCB-top datum 9.1. Exported bottom mask/copper then extend 0.05/0.04 mm below the
support plane. These are explicit rendering-layer offsets, not new physical
interference or thickness measurements. Aligning the outermost mask sheet
instead would require +7.55 mm and place component origins at 9.145; do not
silently interchange those conventions. Keep physical-fit checks based on the
declared PCB thickness, support datum and tested tolerance scenarios.

## Corrected reference checks

The isolated [reference source](reference/carrier-case.scad) preserves the r8
four-anchor top/retainer and all Z datums. Only the bottom, populated-carrier
render witness and carrier collision sweep receive the X reflection, plus the
r9 revision comment. Original r7/r8 files and the PCB are preserved.

All **12 scenarios pass**: eleven empty intersections and the intentional
zero-thickness seam at Z27.6. The three exported reference meshes are each one
watertight, consistently wound solid in their print orientations. Source and
mesh hashes are in [reference/reference-source-manifest.json](reference/reference-source-manifest.json);
results are in [reference/fit-verification.json](reference/fit-verification.json).
Native Fusion bodies and exports still require their own comparison with this
reference. No structural, thermal or physical-part qualification is asserted.
