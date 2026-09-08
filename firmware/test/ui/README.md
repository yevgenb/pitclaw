# Display lifecycle regression check

`test_boot_transition.cpp` creates the production widgets on a headless LVGL
display with the board's RGB565 format. It checks that deleting the boot splash
and loading the dashboard leaves an active screen immediately, renders new
frames, and still permits navigation. Before the fix, the active-screen
assertion fails; refreshing in that state can halt LVGL.

Build the simulator first so its LVGL library and display objects are available:

```sh
pio run -e simulator
```

Then compile and run this check from the firmware directory. The command below
uses the macOS Homebrew SDL include layout; use your SDL installation's include
paths on other systems. With the local PlatformIO installation, building the
simulator also requires `CPATH=/opt/homebrew/include` before `pio run`.

```sh
c++ -std=c++17 \
  -DSIMULATOR_BUILD -DLV_CONF_SKIP=1 -DLV_COLOR_DEPTH=32 \
  -DLV_TICK_PERIOD_MS=5 -DLV_MEM_SIZE=262144 \
  -DLV_FONT_MONTSERRAT_14=1 -DLV_FONT_MONTSERRAT_16=1 \
  -DLV_FONT_MONTSERRAT_18=1 -DLV_FONT_MONTSERRAT_24=1 \
  -DLV_FONT_MONTSERRAT_36=1 -DLV_FONT_MONTSERRAT_48=1 \
  -DLV_USE_QRCODE=1 -DLV_USE_SDL=1 \
  -I.pio/libdeps/simulator/lvgl \
  -I/opt/homebrew/include -I/opt/homebrew/include/SDL2 \
  test/ui/test_boot_transition.cpp \
  .pio/build/simulator/src/display/ui_update.o \
  .pio/build/simulator/src/display/graph_history.o \
  .pio/build/simulator/lib*/liblvgl.a \
  -L/opt/homebrew/lib -lSDL2 -o /tmp/pitclaw_boot_transition
/tmp/pitclaw_boot_transition
```

This check includes the production screen implementation directly to exercise
its widgets without starting an SDL window. It is separate from the test-only
`native` environment, which does not link LVGL.
