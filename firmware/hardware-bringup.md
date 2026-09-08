# Carrier firmware bring-up

Temperature processing now matches the carrier's 10 k pull-up / NTC-to-ground
divider and uses ADS1115 AIN3 as the measured excitation reference. The accepted
reference range is 3.0–3.6 V; invalid excitation makes every sampled probe
unavailable. Open detection starts at 98% of excitation, short detection at
100 ADC counts, and each failure resets smoothing before recovery.

During normal control, an invalid pit reading immediately stops the blower and
closes the damper in every fan mode, including during kick-start or manual duty.
The PID command is cleared once per fault; outputs stay closed after reconnection
until the next valid scheduled PID calculation.

Blower defaults are provisionally 100 Hz power PWM with 100% startup for 500 ms.
Bench-test the actual two-wire blower for startup, minimum usable duty, current,
gate/output waveforms and MOSFET temperature before cooking.

## Display and touch backend

The original SPI/TFT_eSPI placeholders could not drive this board and overlapped
the carrier servo/buzzer pins GPIO13/14. They have been replaced with the vendor's
PanelLan `BOARD_SC01_PLUS` configuration and LovyanGFX in
[ui_init.cpp](src/display/ui_init.cpp). This configures the parallel display,
backlight on GPIO45, and capacitive touch on I2C controller 1. The carrier ADS1115
continues to use Arduino `Wire` (controller 0) on GPIO10/11.

LCD and touch share GPIO4 reset; firmware pulses it once before driver startup.
The LVGL display explicitly uses RGB565 with 16-bit draw buffers and synchronous
flush completion. LVGL uses the system allocator rather than a fixed 64 KB pool.
The memory configuration is `qio_qspi` for the board's 2 MB QSPI PSRAM; the previous
`qio_opi` setting selected the wrong PSRAM interface.

The manufacturer specifies an ST7796UI display with an 8-bit i8080 bus and an
FT6336U I2C touch controller. The board pin map is:

| Signal | GPIO |
|---|---|
| LCD D0–D7 | 9, 46, 3, 8, 18, 17, 16, 15 |
| LCD write / command-data | 47 / 0 |
| LCD and touch shared reset | 4 |
| Backlight, active high | 45 |
| Touch SDA / SCL / interrupt | 6 / 5 / 7 |

Source: [Wireless-Tag WT32-SC01 Plus datasheet, LCD/touch tables](https://www.tme.eu/Document/e40e2e0db8f76604c11099fc1b945dc2/WT32-SC01.pdf).

Driver reference: [vendor SC01 Plus configuration](https://github.com/smartpanle/PanelLan_esp32_arduino/blob/2bc0d086c9a55f5288d85da6c16968c22744fe5f/src/board/sc01_plus/sc01_plus.cpp).
PanelLan is pinned to that commit; LovyanGFX is pinned to 1.2.28.

The user confirmed the setup wizard is visible and touch works on the USB-only
board. Physical validation still needs to cover the full touch area, colors,
setup completion, and operation with the carrier attached.

## USB-only startup and PWM

An absent ADS1115 produces one diagnostic and leaves probes unavailable; firmware
does not keep polling an ADC that failed initialization. Connect the carrier and
reset to initialize the ADC before testing probes.

At 100 Hz, the S3's 40 MHz LEDC clock cannot generate the original 8-bit PWM
configuration. The hardware now uses 10 bits, with the existing 0–255 public duty
values scaled to 0–1023. Failed initialization leaves the blower pin low. Timer
assignments also prevent buzzer or backlight activity from changing fan PWM:

| Function | LEDC resource |
|---|---|
| Fan | Channel 0, timer 0, 100 Hz / 10 bits |
| Servo fallback | Timer 1 reserved through ESP32Servo (which may use MCPWM) |
| Buzzer | Channel 4, timer 2 |
| PanelLan backlight | Channel 7, timer 3 |

With no stored Wi-Fi network, firmware opens `BBQ-Setup` immediately instead of
making three failing `WiFi.begin()` calls (`0x300a`, invalid SSID). The portal
remains available until configured. The dashboard HTTP listener pauses while the
portal owns port 80, then resumes when provisioning completes. Provisioning is
serviced during the splash and setup wizard as well as normal operation.
WiFiManager normally destroys its portal inside `process()` after saving the
network; the handoff checks whether the portal is still active before stopping
it, avoiding a null-server crash from double shutdown.

Wi-Fi credentials are saved independently of wizard completion. A reboot during
setup can therefore reconnect to the saved network while the wizard is still
unfinished. The wizard now uses live Wi-Fi state: an active setup AP shows the
`BBQ-Setup` join QR, password `bbqsetup`, and portal address; a connected board
shows its current network and a dashboard URL QR instead. While reconnecting,
the join QR is hidden. QR codes use black modules on white with a quiet zone.

## Wizard verification, 2026-09-08

- The user confirmed the phone opens the dashboard at `192.168.0.29` on the home
  network. The stale setup QR was directing the phone to a hotspot that had
  already stopped after Wi-Fi provisioning.
- Firmware build passes: 147,632 bytes static RAM and 1,687,501 bytes flash.
- Simulator build passes with `CPATH=/opt/homebrew/include` to supply the local
  SDL headers. Headless rendering of the actual wizard checks AP-to-connected
  transitions, hidden QR while reconnecting, and layout with a 32-character SSID.
- Apple's Vision QR decoder reads the rendered setup code as
  `WIFI:T:WPA;S:BBQ-Setup;P:bbqsetup;;` and the connected code as
  `http://192.168.0.29`.
- Uploaded only the application partition at `0x10000`; the flash hash verified.
  Saved Wi-Fi and filesystem settings were preserved. The board reconnected at
  `192.168.0.29`, and both the dashboard and `/api/version` returned HTTP 200.
  Setup was already marked complete, so this reboot entered normal operation;
  the corrected wizard states were validated with the renderer above.

## Splash transition freeze, 2026-09-08

After setup was completed, reboot could stop on the splash even though the serial
log reported normal operation. HTTP remained responsive because it runs in an
asynchronous task. A WebSocket client received its initial snapshot but no
periodic messages, confirming that the main loop had stopped.

Splash cleanup deletes the active LVGL screen. The dashboard fade deferred
activation until an animation tick, allowing a refresh with a null active screen.
LVGL's default assertion handler then halted the main loop. `ui_switch_screen`
now loads immediately when no screen is active; ordinary navigation still fades.

The [headless display regression](test/ui/README.md) failed its active-screen
assertion before the fix and passes afterward, including rendered frames and
subsequent settings/dashboard navigation. The production build passes with
147,632 bytes static RAM and 1,687,581 bytes flash, including the payload fix below.

Once the main loop resumed, testing found corrupted error strings in initial
WebSocket snapshots. `buildDataPayload()` retained pointers into a local error
vector that was destroyed before serialization. The payload now owns copies of
the error text. This matters on the USB-only board because all three probes are
reported disconnected during normal operation.

The user confirmed that the uploaded splash fix displays the dashboard and that
the Settings and Graph tabs respond to touch.

The final app-only upload passed flash hash verification and preserved Wi-Fi and
filesystem settings. The dashboard and `/api/version` return HTTP 200. Three
fresh WebSocket connections each received five valid snapshots/periodic updates
with advancing timestamps, correct probe-disconnected messages, and zero fan and
damper output. This verifies main-loop progress beyond the asynchronous HTTP
response. Logs: `/private/tmp/pitclaw-boot-fix-startup.log` and
`/private/tmp/pitclaw-live-updates-check.log`.

## Verification, 2026-09-07

- `pio run -e wt32_sc01_plus`: build and link pass; 147,488 bytes static RAM,
  1,686,481 bytes flash with the corrected display, portal handling and filesystem checks.
- `pio test -e native`: 132 cases pass across nine suites. Five new cases compile
  the actual fan/buzzer hardware branches against a fake Arduino boundary to check
  S3 divider feasibility, duty scaling, kick-start timing, failed initialization,
  and buzzer timer separation.
- Three Wi-Fi tests exercise the actual manager against fake network/portal
  boundaries: first boot without an SSID, automatic portal shutdown after
  provisioning, and explicit shutdown when the portal remains active.
- Uploaded over USB to the ESP32-S3. Startup reports 2,095,103 bytes of PSRAM,
  480x320 RGB565 display initialization, and 100 Hz / 10-bit fan PWM without the
  previous LEDC error. First boot starts the setup AP without the invalid-SSID
  error, then reaches the touchscreen setup wizard.
- Reboot with the saved Wi-Fi network connects successfully; `/api/version`
  responds with HTTP 200 on the device at `192.168.0.29`.
- Final firmware and preserved filesystem image were flashed and their write
  hashes verified. The dashboard root and all six assets return HTTP 200 and
  match the local files byte for byte; `/HNAP1/` returns HTTP 404. The final
  startup capture has no runtime error or panic messages, with one expected
  absent-ADS1115 diagnostic. Log: `/private/tmp/pitclaw-final-startup.log`.

## Development release checks

`ENABLE_RELEASE_UPDATES=0` in `platformio.ini` disables the browser's automatic
and manual GitHub release checks. Set it to `1` to opt in with a stable `x.y.z`
firmware version. Development/prerelease version strings and the simulator skip
release checks. Manual firmware uploads at `/update` remain available on hardware.
The `/api/version` response exposes `releaseUpdatesEnabled` to the web UI.

Verify the browser gate with `node test/web/test_release_updates.cjs`.
Deploy both the firmware and web assets for this setting to take effect.

## Web files and filesystem preservation

The firmware upload does not include `data/`. The initial board had only
`config.json` in LittleFS, so dashboard requests produced missing-file diagnostics.
Missing cook-session files on first boot and missing HTTP paths now use `stat()`
against the configured mount path; Arduino-ESP32 2.0.14's `LittleFS.exists()` itself
logs an error for absent files. Static serving checks for real files before
handling a request and prefers the uncompressed assets in `data/`.

Before adding web files, the existing LittleFS partition was backed up from
`0xc90000`, size `0x360000`, to `/private/tmp/pitclaw-littlefs-before.bin`.
The backup was unpacked, `data/` was merged, and the resulting image was unpacked
again to compare every file. Existing `config.json` was preserved byte for byte.
The image is `/private/tmp/pitclaw-littlefs-with-web.bin`; verification hashes are
in `/private/tmp/pitclaw-filesystem-manifest.json`. Wi-Fi credentials in NVS are
outside the filesystem partition and are not overwritten.

The installed mklittlefs 2.3 utility cannot unpack the board's LittleFS 2.1 disk
format. For this migration, a local build of upstream `earlephilhower/mklittlefs`
with LittleFS 2.11.1 was used; the globally installed PlatformIO tools were unchanged.
Ordinary `pio run -e wt32_sc01_plus -t uploadfs` replaces the filesystem, so back
up settings and session data first if they need to be retained.

## Verification, 2026-09-05

- `pio test -e native`: all 120 existing cases pass, including eight tests of the actual
  `TempManager::processSample()` path rather than duplicated conversion formulas.
- The additional four `test_control_outputs` cases pass against the production
  output helper, fan controller and servo controller; the 20 PID cases also pass
  after adding the fault interlock (124 native cases total).
- `pio run -e wt32_sc01_plus`: compiles and links with the locally installed
  Espressif32 6.6.0 / Arduino 2.0.14 / TFT_eSPI 2.5.43 dependencies. Build success
  does not validate display pin assignments or touch support.
- No board was connected: ADC fixture tests, blower waveforms/temperature and
  display/touch operation remain unmeasured. The embedded ADC open test now
  requires PIT to be unplugged and actually asserts a rail-relative reading.

Both commands used an isolated writable `PLATFORMIO_CORE_DIR`; no firmware was
flashed. Repeat hardware validation on the actual assembled carrier.

## Reverse-proxy UI deployment, 2026-09-08

Flashed the current firmware and all six web assets to the WT32-SC01 Plus.
A fresh LittleFS backup was merged with `data/` and verified by unpacking the
new image. The saved `config.json` remained byte-for-byte identical, including
when read back from the running controller. Backup, image, and flash logs are
in `/private/tmp/pitclaw-proxy-deploy/`.

Firmware and filesystem flash hashes passed, and serial output confirmed normal
startup at `192.168.0.29`. All six served assets match the source files; GitHub
checks remain disabled and the manual `/update` page responds successfully.
The firmware build and both web regression checks passed. A temporary local
Nginx instance verified the deployed assets, API, and continuing WebSocket
readings under different prefixes over HTTP and HTTPS. The user's Nginx server
still needs the [proxy configuration](docs/reverse-proxy.md).

Mobile header follow-up: deployed a CSS fix that reserves space for the logo
and puts cook times below the logo/buttons on narrow screens, with cache version
`v4`. The previous filesystem image matched the device's full partition digest
before merging the change. Saved configuration, flash hash, normal startup, and
all six served assets were verified. Images and logs are in
`/private/tmp/pitclaw-mobile-header/`. Phone visual verification was unavailable
because no browser was connected.
