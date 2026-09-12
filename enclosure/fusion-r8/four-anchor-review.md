# Four-anchor enclosure reference review

Reviewed 2026-09-11. **The four-anchor proposal clears the declared geometry
checks and is a suitable target for the native Fusion model.** This is a
geometric review of the isolated reference, not structural qualification or
verification of the subsequently created Fusion bodies.

## Geometry and load path

Coordinates are centered on the 60 × 92 mm WT32, in millimeters. Replace the
two anchors at (±35.5,0) with four at **(±35.5,±40)**. Retain the 2.5 mm frame,
70 × 96 mm outer ring, 60.8 × 92.8 mm inner opening and existing four OEM tabs.
The OEM screw centers remain X±25.695, Y−39.48/+35.66.

| Check | Nominal result |
|---|---:|
| New Ø9 anchor to nearest Ø9 closure boss at (±38,±28) | 12.258 mm center distance; 3.258 mm solid-body gap |
| New anchor pad to the Ø10 closure scallop in the retainer | 2.758 mm gap |
| New anchor-pad overall bounds | X±40, Y±44.5; within the existing retainer envelope |
| Pad to straight inside sidewall at X±40.5 | 0.5 mm clearance |
| Top anchor inner edge at X±31 to display-pocket edge at X±30.6 | 0.4 mm clearance |
| Anchor row offsets from OEM rows | 0.52 mm at the −Y end; 4.34 mm at the +Y end |

The new pads overlap the existing long rails, so they form one connected frame.
Keep each OEM tab's existing convex bridge from its Ø6.4 mm pad to the small
round endpoint at X±32. The M3 anchor holes must not sever these bridges or the
inner rail strip. The reference mesh confirms a connected retainer after all
holes and closure scallops are subtracted.

Do not place the +Y anchors directly at Y35.66: that would leave only 8.058 mm
between the Ø9 anchor and Ø9 closure-column centers, producing a clash. The
proposed ±40 rows avoid it. They shorten the former long-rail load path, but
no new deflection, strength or creep rating is claimed.

## Requirements for the Fusion implementation

- Preserve Z datums: bottom exterior 0, seam 27.6, retainer underside 30.1,
  retainer/top-boss seating plane 32.6, glass front 43.4 and top exterior 44.9.
- Use four top hard-stop bosses, Ø9 mm, from Z32.6 to the front structure.
  Retain Ø4 mm blind insert pilots, 5 mm deep, opening at the retainer plane.
  The bosses must remain joined to the top after its cavity is cut.
- Give all four retainer anchors Ø3.4 mm through holes. M3×6 button-head screws
  retain 3.5 mm nominal engagement through the 2.5 mm frame. This changes the
  enclosure total from ten to twelve common inserts, and retainer screws from
  two to four. OEM screws remain four separate, sample-selected screws.
- Update the insertion relief for **all four new anchor pads**, and remove the
  old center pads, bosses and reliefs. Preserve the 70.8 × 97 mm ring passage
  plus Ø10 mm anchor-pad passages through the lip/shoulder. Relief ends at
  approximately Z28.62, below the Z32.6 hard stops. Do not enlarge the retainer
  length: that would thin the short-end locating lip.
- Straight driver access from the open rear is available at the four anchors;
  a nominal Ø6 mm shaft clears the nearby display pocket, wall and closure
  column. Install these screws before joining the case halves. Actual screw
  heads and driver access still require a physical assembly check.

## Reference and verification evidence

[reference/carrier-case.scad](reference/carrier-case.scad) is a copy of r7 with
only the revision comment and anchor list changed. Its interface is an exact
copy. The original r7 source, print files and PCB were not modified.

- Reference SCAD SHA256: `7236fdce2082045b21b59c48783767b32c5fc8e226d100e59f5f91dd63796ab7`.
- All **12 collision scenarios pass**: eleven empty intersections and only
  the intentional, zero-thickness Z27.6 seam contact for shell closure.
- Top, bottom and retainer reference STLs are each one watertight, consistently
  wound solid and begin at Z=0 in their print orientations.
- The bottom STL is byte-identical to r7. Its connector and carrier interfaces
  are therefore unchanged.

Exact commands, witness tolerances, source hashes, mesh hashes and seam-contact
measurements are recorded in [reference/fit-verification.json](reference/fit-verification.json)
and [reference/reference-source-manifest.json](reference/reference-source-manifest.json).
Rerun with Python plus NumPy/Trimesh using
`python3 enclosure/fusion-r8/reference/verify_reference.py`.

Purchased WT32 boss dimensions, its small screws, light glass-pad preload,
printed insert alignment and actual operating temperature remain physical
checks. Increased stiffness must not be used to force an incorrect display
stack into the top. The Fusion model requires its own body/export comparison
against this checked reference.
