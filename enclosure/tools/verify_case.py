#!/usr/bin/env python3
"""Check the printable case and its modeled installation tolerance cases.

Run with Python 3 plus trimesh, for example:
  /tmp/pitclaw-mesh-check/bin/python enclosure/tools/verify_case.py

The case's production dimensions remain fixed. Only the diagnostic electronics
witnesses vary. This script reads the PCB/project as bytes; it never invokes
KiCad or rewrites manufacturing files. Passing checks establish geometric fit
of the declared envelopes, not physical fit of unmeasured purchased parts.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    "enclosure/carrier-case.scad",
    "enclosure/carrier-interface.scad",
    "hardware/carrier-revb/mechanical/enclosure-interface.json",
    "hardware/carrier-revb/pitclaw-carrier.kicad_pcb",
    "hardware/carrier-revb/pitclaw-carrier.kicad_pro",
    "hardware/carrier-revb/verification/drc.json",
)
INPUT_NAMES = (
    "check_pcb_thickness", "check_pd_thickness", "check_pd_spacer_height",
    "check_board_edge_growth", "check_module_shift_x",
)
EMPTY_MESSAGE = "Current top level object is empty."
EXPECTED_SIZE = {
    "top": [86, 104, 19.3],
    "bottom": [86, 104, 27.6],
    "retainer": [80, 96, 2.5],
    "coupon": [86, 22, 27.6],
    "insert_coupon": [36, 16, 7.5],
}
MESH_NAMES = {
    "top": "carrier-top.stl",
    "bottom": "carrier-bottom.stl",
    "retainer": "carrier-retainer.stl",
    "coupon": "fit-coupon.stl",
    "insert_coupon": "insert-coupon.stl",
}


@dataclass(frozen=True)
class Check:
    name: str
    part: str
    values: tuple[float, float, float, float, float]

    def as_dict(self):
        return {"name": self.name, "part": self.part,
                "witness_inputs_mm": dict(zip(INPUT_NAMES, self.values))}


def scenarios() -> list[Check]:
    checks = [Check("nominal-" + part, part, (1.6, 1.6, 3, 0, 0)) for part in (
        "insertion-check", "carrier-installation-check", "electronics-closure-check",
        "shell-closure-check")]
    # Use the full edge allowance with each stack/X corner. These are explicit
    # design scenarios, not claims about the tolerances of every purchased part.
    for label, stack in (("low", (1.44, 1.44, 2.9)), ("high", (1.76, 1.76, 3.1))):
        for x in (-0.2, 0.2):
            for part in ("carrier-installation-check", "electronics-closure-check"):
                name = f"{label}-stack-x-{'minus' if x < 0 else 'plus'}-0.2-{part}"
                checks.append(Check(name, part, (*stack, 0.2, x)))
    return checks


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    return {relative: sha256(ROOT / relative) for relative in SOURCES}


def echo_vector(log: str, label: str) -> list[float]:
    match = re.search(r'ECHO:\s*"' + re.escape(label) + r'",\s*(\[[^\]]*\])', log)
    if match is None:
        raise ValueError(f"Required diagnostic echo is missing: {label}")
    return json.loads(match.group(1))


def near_vector(actual, expected, tolerance=0.0001):
    return len(actual) == len(expected) and all(
        abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected))


def openscad_command(explicit: str | None) -> list[str]:
    if explicit:
        return [explicit]
    app = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
    if sys.platform == "darwin" and app.is_file():
        # The installed desktop Qt build requires x86_64 on this host.
        return ["arch", "-x86_64", str(app)]
    executable = shutil.which("openscad")
    if not executable:
        raise RuntimeError("OpenSCAD was not found; provide --openscad PATH")
    return [executable]


def run_check(check: Check, command: list[str], output: Path, timeout: float) -> dict:
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    target = logs / (check.name + "-intersection.stl")
    logfile = logs / (check.name + ".log")
    target.unlink(missing_ok=True)
    args = command + ["-o", str(target), "-D", 'part="' + check.part + '"']
    for variable, value in zip(INPUT_NAMES, check.values):
        args.extend(["-D", f"{variable}={value:g}"])
    args.append(str(ROOT / "enclosure/carrier-case.scad"))
    start = time.monotonic()
    record = check.as_dict()
    record["command"] = args
    try:
        process = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        log = process.stdout + process.stderr
        logfile.write_text(log)
        record.update({"returncode": process.returncode,
                       "log": str(logfile.relative_to(output)),
                       "log_sha256": sha256(logfile)})
        if "WARNING:" in log or "ERROR:" in log:
            raise ValueError("OpenSCAD emitted a warning or error; inspect the complete log")
        # OpenSCAD returns 1 for an intentionally empty top-level object.
        if process.returncode not in (0, 1):
            raise ValueError(f"Unexpected OpenSCAD exit status: {process.returncode}")
        witnessed = echo_vector(log, "FIT_CHECK_INPUTS")
        if not near_vector(witnessed, check.values):
            raise ValueError(f"Witness overrides were not applied: {witnessed}")
        case = echo_vector(log, "DRAFT case W,L,H")
        if not near_vector(case, [86, 104, 44.9]):
            raise ValueError(f"Case dimensions changed with diagnostic witnesses: {case}")
        datums = echo_vector(log, "Seam / retainer underside / glass front")
        if not near_vector(datums, [27.6, 30.1, 43.4]):
            raise ValueError(f"Nominal shell/display datums moved with the witnesses: {datums}")
        if EMPTY_MESSAGE in log and not target.exists():
            record["result"] = "PASS: empty intersection"
        elif check.part == "shell-closure-check" and target.is_file() and process.returncode == 0:
            # Some OpenSCAD backends retain the shared meeting-face triangles.
            # Accept this only for shell closure and only at the known seam;
            # zero signed volume alone would not exclude a real collision.
            import numpy as np
            import trimesh

            contact = trimesh.load(target, force="mesh", process=False)
            if not len(contact.vertices) or not len(contact.faces):
                raise ValueError("Unexpected empty shell-contact mesh")
            triangles = contact.triangles
            signed_volume = float(np.einsum("ij,ij->i", triangles[:, 0],
                np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)
            max_plane_error = float(np.max(np.abs(contact.vertices[:, 2] - 27.6)))
            thickness = float(contact.bounds[1][2] - contact.bounds[0][2])
            tolerance = 0.00001
            record["intentional_seam_contact"] = {
                "file": str(target.relative_to(output)), "sha256": sha256(target),
                "bounds_mm": contact.bounds.tolist(), "triangles": len(contact.faces),
                "signed_volume_mm3": signed_volume, "z_thickness_mm": thickness,
                "maximum_distance_from_seam_mm": max_plane_error,
                "seam_z_mm": 27.6, "numeric_tolerance": tolerance,
            }
            if not (np.isfinite(contact.vertices).all() and np.isfinite(signed_volume)
                    and max_plane_error <= tolerance and thickness <= tolerance
                    and abs(signed_volume) <= tolerance):
                raise ValueError("Shell contact is not confined to the intentional zero-thickness seam")
            record["result"] = "PASS: intentional coplanar seam contact"
        else:
            raise ValueError("Collision check did not produce the required empty intersection")
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        log = (stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout)
        log += (stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr)
        log += f"\nVERIFY_CASE_ERROR: exceeded {timeout:g} second timeout\n"
        logfile.write_text(log)
        record.update({"result": "FAIL", "error": "OpenSCAD timeout",
                       "log": str(logfile.relative_to(output)),
                       "log_sha256": sha256(logfile)})
    except (ImportError, OSError, ValueError) as error:
        record.update({"result": "FAIL", "error": str(error)})
    record["elapsed_seconds"] = round(time.monotonic() - start, 2)
    return record


def connected_components(mesh) -> int:
    # Avoid trimesh.split's optional scipy/networkx dependency. Shared vertices
    # join the triangles after trimesh's standard duplicate-vertex merge.
    parents = list(range(len(mesh.vertices)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    used = set()
    for face in mesh.faces:
        a, b, c = (int(i) for i in face)
        used.update((a, b, c))
        parents[find(b)] = find(a)
        parents[find(c)] = find(a)
    return len({find(i) for i in used})


def check_mesh(part: str, path: Path, coupon_components: int) -> dict:
    record = {"file": path.name}
    try:
        import trimesh

        before = sha256(path)
        mesh = trimesh.load(path, force="mesh", process=True)
        components = connected_components(mesh)
        expected_components = coupon_components if part == "coupon" else 1
        record.update({"sha256": before, "connected_components": components,
                       "watertight": bool(mesh.is_watertight),
                       "consistent_winding": bool(mesh.is_winding_consistent),
                       "bounds_mm": mesh.bounds.tolist(),
                       "size_mm": mesh.extents.tolist(),
                       "volume_mm3": round(float(mesh.volume), 3),
                       "triangles": len(mesh.faces)})
        if not (components == expected_components and mesh.is_watertight
                and mesh.is_winding_consistent and mesh.volume > 0):
            raise ValueError("Mesh is not the expected number of closed, consistently oriented solids")
        if abs(float(mesh.bounds[0][2])) > 0.001:
            raise ValueError("Print-oriented mesh does not start at Z=0")
        if part in EXPECTED_SIZE and not near_vector(mesh.extents, EXPECTED_SIZE[part], 0.01):
            raise ValueError(f"Unexpected print dimensions: {mesh.extents.tolist()}")
        if sha256(path) != before:
            raise ValueError("Mesh changed during validation")
        record["result"] = "PASS"
    except (ImportError, OSError, ValueError) as error:
        record.update({"result": "FAIL", "error": str(error)})
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=ROOT / "enclosure/print/carrier-r7")
    parser.add_argument("--openscad", help="Executable path; default uses the installed macOS app via arch -x86_64")
    parser.add_argument("--jobs", type=int, default=3, help="Concurrent OpenSCAD checks (default: 3)")
    parser.add_argument("--timeout", type=float, default=600, help="Seconds allowed for each OpenSCAD process")
    parser.add_argument("--coupon-components", type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diagnostics-only", action="store_true")
    mode.add_argument("--meshes-only", action="store_true")
    mode.add_argument("--list-cases", action="store_true", help="Print the scenario matrix without running tools")
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout <= 0 or args.coupon_components < 1:
        parser.error("jobs, timeout, and coupon-components must be positive")
    checks = scenarios()
    if args.list_cases:
        print(json.dumps([check.as_dict() for check in checks], indent=2))
        return 0

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sources_before = source_hashes()
    report = {
        "status": "RUNNING", "revision": "carrier-enclosure-r7",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "sources_sha256": sources_before,
        "verifier_sha256": sha256(Path(__file__)),
        "scope": "Declared nominal geometry and explicit tolerance scenarios; no physical print or purchased-part fit test.",
        "assumptions": [
            "Carrier PCB and USB module thickness 1.44–1.76 mm; USB spacer 2.9–3.1 mm.",
            "Board edge growth 0.2 mm and USB module lateral placement shift ±0.2 mm.",
            "Purchased USB-module/spacer tolerances are design allowances requiring sample measurement.",
            "Case geometry stays nominal; printer dimensional error is not silently added to witnesses.",
            "Only shell closure may retain triangles strictly coplanar at Z=27.6 mm; all other intersections must be empty.",
            "The programmed 0.3 mm installation lift, clipped solder tails, and declared M2 hardware envelopes apply.",
            "No modeled tolerance establishes OEM screw suitability, glass-pad preload, cable reach, or thermal/weather qualification.",
        ],
        "geometry_checks": {}, "meshes": {},
    }
    if not args.meshes_only:
        command = openscad_command(args.openscad)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_check, check, command, output, args.timeout): check for check in checks}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                report["geometry_checks"][result["name"]] = result
                print(result["name"], result["result"], result.get("error", ""), flush=True)
    if not args.diagnostics_only:
        for part, filename in MESH_NAMES.items():
            result = check_mesh(part, output / filename, args.coupon_components)
            report["meshes"][part] = result
            print(part, result["result"], result.get("error", ""), flush=True)
    sources_after = source_hashes()
    report["sources_unchanged"] = sources_after == sources_before
    if sources_after != sources_before:
        report["sources_sha256_after"] = sources_after
    results = list(report["geometry_checks"].values()) + list(report["meshes"].values())
    passed = sources_after == sources_before and all(r["result"].startswith("PASS") for r in results)
    report["status"] = "PASS: FIT PROTOTYPE" if passed else "FAIL"
    suffix = "-diagnostics" if args.diagnostics_only else "-meshes" if args.meshes_only else ""
    report_path = output / ("fit-verification" + suffix + ".json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(str(report_path), report["status"], flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
