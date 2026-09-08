"""Compile production LVGL interaction checks and optionally save screen PNGs."""
import argparse
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib


def save_png(ppm):
    header, dimensions, maximum, rgb = ppm.read_bytes().split(b"\n", 3)
    width, height = map(int, dimensions.split())
    assert header == b"P6" and maximum == b"255"
    assert len(rgb) == width * height * 3

    def chunk(tag, data):
        return (struct.pack("!I", len(data)) + tag + data
                + struct.pack("!I", zlib.crc32(tag + data) & 0xffffffff))

    raw = b"".join(b"\0" + rgb[y * width * 3:(y + 1) * width * 3]
                   for y in range(height))
    ppm.with_suffix(".png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    ppm.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--sdl-prefix", type=Path,
                        default=Path("/opt/homebrew") if Path("/opt/homebrew").exists() else Path("/usr"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    libraries = list((root / ".pio/build/simulator").glob("lib*/liblvgl.a"))
    if len(libraries) != 1:
        parser.error("Build the simulator first: CPATH=/opt/homebrew/include pio run -e simulator")
    definitions = ["SIMULATOR_BUILD", "LV_CONF_SKIP=1", "LV_COLOR_DEPTH=32",
                   "LV_THEME_DEFAULT_TRANSITION_TIME=0", "LV_THEME_DEFAULT_GROW=0",
                   "LV_MEM_SIZE=262144", "LV_USE_QRCODE=1", "LV_USE_SDL=1"]
    definitions += [f"LV_FONT_MONTSERRAT_{size}=1" for size in (14, 16, 18, 24, 36, 48)]
    flags = ["-std=c++17"] + [f"-D{item}" for item in definitions]
    flags += [f"-I{root / '.pio/libdeps/simulator/lvgl'}",
              f"-I{args.sdl_prefix / 'include'}", f"-I{args.sdl_prefix / 'include/SDL2'}"]
    env = os.environ.copy()
    if args.capture_dir:
        args.capture_dir = args.capture_dir.resolve()
        args.capture_dir.mkdir(parents=True, exist_ok=True)
        env["PITCLAW_UI_CAPTURE_DIR"] = str(args.capture_dir)
    with tempfile.TemporaryDirectory(prefix="pitclaw-ui-checks-") as temporary:
        for name in ("test_boot_transition", "test_interactions"):
            binary = Path(temporary) / name
            subprocess.run([os.environ.get("CXX", "c++"), *flags,
                            str(root / f"test/ui/{name}.cpp"),
                            str(root / "src/display/ui_update.cpp"),
                            str(root / "src/display/graph_history.cpp"), str(libraries[0]),
                            f"-L{args.sdl_prefix / 'lib'}", "-lSDL2", "-o", str(binary)], check=True)
            subprocess.run([str(binary)], env=env, check=True)
    if args.capture_dir:
        for ppm in args.capture_dir.glob("*.ppm"):
            save_png(ppm)
        print(f"Screen captures: {args.capture_dir}")


if __name__ == "__main__":
    main()
