# Pit Claw 3D printed parts

The controller enclosure is [Fusion r12](fusion-r12/README.md): a 104 × 86 ×
44.9 mm case with a top bezel, bottom shell, internal display retainer and
removable probe fascia with continuous captured guides. Four internal M3 inserts provide a 72 × 74 mm mounting
pattern with screw access from underneath.

- [Print package and editable Fusion model](fusion-r12/pitclaw-enclosure-r12.zip)
- [Print settings, coupons, hardware and assembly](fusion-r12/README.md)
- [Native Fusion design](fusion-r12/pitclaw-enclosure-r12.f3d)
- [Mounting interface](fusion-r12/mount-interface.json)
- [Independent OpenSCAD reference and checks](fusion-r12/reference/README.md)

Only the latest controller enclosure is kept in the working tree. Older designs
remain in Git history. The CAD checks pass; physical fit, printed joint strength
and mounting load capacity still need prototype testing.

## Separate blower and damper assembly

The smoker-mounted blower/damper is a separate part, retained alongside the
controller enclosure. Use [bbq-fan-assembly.scad](bbq-fan-assembly.scad),
[blower-housing.stl](stl/blower-housing.stl) and
[uds-pipe-adapter.stl](stl/uds-pipe-adapter.stl).

Open the fan source in OpenSCAD, select the desired `part`, render and export in
millimeters. Print the blower housing open-side-up and the pipe adapter upright.
Check fit with the actual fan, servo and smoker intake. Its geometry is separate
from the r12 controller fit verification.

### Hardware

| Qty | Item | Notes |
|-----|------|-------|
| 2 | M3x10mm screws | Mount 5015 blower fan to housing |
| 2 | M2 or M2.5 screws | Mount MG90S servo (servo-specific) |
| 1 | Small screw + nut | Attach damper plate to servo horn |
| 2 | Small hose clamps (25-40mm range) | One for pipe adapter to pipe nipple, one for duct to adapter (if not press-fit) |
| 1 | High-temp gasket tape (or PTFE tape) | Wrap around NPT pipe before inserting into adapter for air-tight seal |

### Assembly

1. **Mount the servo**: Press-fit or screw the MG90S servo into the servo pocket on the intake side of the blower housing.

2. **Attach damper plate**: Attach the butterfly damper plate to a servo horn using a small screw. The damper plate should be centered in the intake opening when the servo is at its midpoint.

3. **Install the servo horn**: Press the horn with damper plate onto the servo shaft. Verify the damper opens fully (parallel to airflow) and closes fully (perpendicular to airflow) across the servo's range of motion.

4. **Mount the blower fan**: Place the 5015 blower into the housing cavity. Secure with 2x M3x10mm screws through the top mounting holes.

5. **Prepare the UDS pipe adapter**: Wrap high-temp gasket tape around the 3/4" NPT pipe nipple on the drum. Slide the pipe adapter over the nipple and secure with a hose clamp in the groove.

6. **Connect housing to adapter**: Insert the blower housing output duct into the adapter's duct mating end. If the fit is loose, secure with a second hose clamp. If press-fit is snug, no clamp is needed.

7. **Route wires**: Run the fan power wires (2-pin) and servo signal wires (3-pin) through the wire channels on the housing, back to the controller enclosure.

### Airflow Path

```
Outside air -> [butterfly damper] -> [5015 blower fan] -> [duct] -> [UDS pipe adapter] -> drum
               (servo controlled)    (PWM speed)          (sealed)   (clamped to pipe)
```

The PID controller modulates both the fan speed (PWM) and damper position (servo angle) to maintain the target pit temperature. Cap all other intake pipes on the UDS -- this assembly controls all airflow.
