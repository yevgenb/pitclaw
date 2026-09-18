# R13 independent enclosure reference

This self-contained reference contains the accepted enclosure geometry, generated
carrier interface, five full-part STLs and six coupons. It requires no older
enclosure archive or fit-test source. The main release uses native Fusion meshes
for the five complete parts; its six coupons come from this reference.

Run with Python containing `numpy` and `trimesh`, and OpenSCAD installed:

```sh
python enclosure/fusion-r13/reference/export_reference.py --copy-coupons
```

The exporter renders all eleven meshes, runs all 37 assembly/interface checks, and
measures both full guide profiles. `--copy-coupons` copies only the six verified
coupons to `../stl`; it does not replace the five native Fusion part exports.
On macOS it uses the installed OpenSCAD app through `arch -x86_64`; elsewhere it
finds `openscad` on PATH. `--jobs` controls parallel rendering, defaulting to three.

- `carrier-case.scad`, `carrier-interface.scad` and `adafruit5807-base.scad`: complete local geometry inputs.
- `base-geometry.json`: printed USB base dimensions and source geometry.
  The base is included in the carrier insertion and closure sweeps.
- `verify_reference.py`: full assembly sweeps, seated clearances, closure, tool and
  screw access, guide capture and two-land support checks, plus mesh integrity.
- `verify_running_clearance.py`: measurements from actual full-part STL sections.
- `geometry-contract.json`: accepted dimensions and hardware assumptions.
- `fit-verification.json`: combined check, mesh and measured-clearance results.
- `reference-manifest.json`: source, verifier, report and STL hashes.

The working enclosure pilots are Ø4.2 mm for the user's measured Ø5 mm maximum
insert envelope. The calibration coupon deliberately retains its labelled
4.0/4.1/4.2 mm trial holes. Insert length remains the stated 4 mm assumption.

Acceptance of the printed fit coupons does not establish full-case load, heat,
or weather ratings. See the [main assembly guide](../README.md) for the current
parts, hardware, assembly sequence and validation limits.
