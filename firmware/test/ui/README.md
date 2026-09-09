# Display interaction and lifecycle checks

These checks create the production widgets on a headless LVGL 480×320 display
with the board's RGB565 format and inject pointer events through LVGL's input
timer. They use a deterministic clock and do not measure ESP32 rendering or
physical touch latency. They are separate from the PlatformIO `native` tests,
which do not link LVGL.

- `test_boot_transition.cpp` checks splash lifetime, startup countdown, reset
  hold timing, and 123 navigation taps covering edges, drift, and rapid changes.
- `test_interactions.cpp` checks committed editor values, independent targets,
  Cancel, one-degree and held adjustments, bounds, Fahrenheit/Celsius conversion,
  condensed history timestamps, axis layout, alarms on all main screens and over
  editors, Settings scrolling, and setup navigation/test feedback. It also checks
  raised degree symbols through changing digit widths, negative/zero Celsius
  readings, disconnection/reconnection, and compact alarm layouts.

Build the simulator to obtain the matching LVGL library, then run both checks:

```sh
CPATH=/opt/homebrew/include pio run -e simulator
python3 test/ui/run_checks.py
```

The runner defaults to Homebrew SDL on macOS and `/usr` elsewhere. Supply
`--sdl-prefix /path/to/prefix` for another SDL installation. It compiles checks in
a temporary directory and removes the executables after running them.

To also capture the actual production screens as PNGs:

```sh
python3 test/ui/run_checks.py --capture-dir work/ui-implementation/screens
```

The capture process uses LVGL rendering and Python's standard library; it needs
no browser or image packages. The static comparison under `work/ui-comparison`
preserves the earlier before/proposed screenshots.
