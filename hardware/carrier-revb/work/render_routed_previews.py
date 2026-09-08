#!/usr/bin/env python3
"""Export native KiCad review layers without modifying the PCB.

Run once routing and zone filling are final. PNG rendering is optional and uses
Node.js plus sharp when --node and --node-modules are supplied. The back image
is mirrored, as viewed from the solder side; the front image is the component
side. Native SVGs remain the source for every preview.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cli", default="/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
    parser.add_argument("--node", type=Path)
    parser.add_argument("--node-modules", type=Path)
    parser.add_argument("--views", nargs="+", choices=("front-copper", "back-copper", "assembly"),
                        default=("front-copper", "back-copper", "assembly"))
    args = parser.parse_args()
    board = args.board.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(board.read_bytes()).hexdigest()
    views = [
        ("front-copper", "F.Cu,F.Silkscreen,Edge.Cuts", False),
        ("back-copper", "B.Cu,B.Silkscreen,Edge.Cuts", True),
        ("assembly", "F.Fab,Edge.Cuts", False),
    ]
    artifacts = []
    for name, layers, mirror in views:
        if name not in args.views:
            continue
        target = output / f"carrier-{name}.svg"
        command = [args.cli, "pcb", "export", "svg", "--mode-single",
                   "--layers", layers, "--page-size-mode", "2",
                   "--exclude-drawing-sheet", "--drill-shape-opt", "2"]
        if mirror:
            command.append("--mirror")
        command += ["-o", str(target), str(board)]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        # Keep native plot geometry and copper colors. The editor's pale silk
        # and edge colors need more contrast on a white review background.
        svg = target.read_text()
        for old, new in {"#F2EDA1": "#59636E", "#E8B2A7": "#59636E", "#D0D2CD": "#25313C",
                         "#AFAFAF": "#65717D"}.items():
            svg = svg.replace(old, new)
        target.write_text(svg)
        artifacts.append({"file": target.name, "layers": layers,
                          "view": "solder side (mirrored)" if mirror else "component side"})
        if args.node and args.node_modules:
            png = target.with_suffix(".png")
            script = """
const [svg, png, modules] = process.argv.slice(1);
const sharp = require(require.resolve('sharp', {paths: [modules]}));
sharp(svg, {density: 240}).flatten({background: '#ffffff'})
  .resize({height: 2200}).png().toFile(png)
  .catch(error => { console.error(error); process.exit(1); });
"""
            subprocess.run([str(args.node), "-e", script, str(target), str(png),
                            str(args.node_modules)], check=True)
            artifacts[-1]["png"] = png.name
    if hashlib.sha256(board.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("The PCB changed during preview export; rerun after routing is final")
    (output / "preview-source.json").write_text(json.dumps({
        "board": str(board), "sha256": source_hash, "artifacts": artifacts,
        "description": "Native KiCad layer plots; front and back copper are separate views."
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
