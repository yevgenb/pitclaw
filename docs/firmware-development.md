# Firmware Development

Guide for building, flashing, testing, and understanding the Pit Claw firmware.

## Prerequisites

### Quick Setup (Windows)

```powershell
# Run from an elevated (Admin) PowerShell in the repo root
powershell -ExecutionPolicy Bypass -File scripts\setup-dev.ps1
```

This installs Git, Python, Node.js, PlatformIO CLI, and OpenSCAD. The script is idempotent — safe to run again anytime.

### Manual Install

If you prefer to install tools yourself (or you're not on Windows):

1. [Git](https://git-scm.com/)
2. [Python 3.12+](https://www.python.org/)
3. [PlatformIO CLI](https://docs.platformio.org/en/latest/core/installation.html) — `pip install platformio`
4. [VS Code](https://code.visualstudio.com/) + [PlatformIO extension](https://platformio.org/install/ide?install=vscode) (recommended)

## Build Commands

All commands run from the `firmware/` directory.

```bash
# Build firmware
pio run -e wt32_sc01_plus

# Flash firmware via USB
pio run -e wt32_sc01_plus --target upload

# Upload web UI files to LittleFS
pio run -e wt32_sc01_plus --target uploadfs

# Build simulator (desktop, no hardware needed)
pio run -e simulator

# Clean build artifacts
pio run --target clean

# Serial monitor
pio device monitor --baud 115200
```

## Testing

```bash
# Desktop unit tests (PID, prediction, alarms — no hardware)
pio test -e native

# Single test suite
pio test -e native --filter test_desktop/test_pid

# On-device integration tests (requires connected hardware)
pio test -e wt32_sc01_plus

# Headless production LVGL checks (build the simulator first)
python3 test/ui/run_checks.py
```

Tests use the Unity framework with two environments:
- **`native`** — runs on desktop, tests pure logic (PID, prediction, alarms, fan logic, temperature conversion)
- **`wt32_sc01_plus`** — runs on device, tests hardware integration (ADC, fan PWM, servo, buzzer, I2C)

## OTA Updates

After the initial USB flash, firmware can be updated over Wi-Fi:

1. Open `http://bbq.local/update` in a browser
2. Upload the `.bin` file from `.pio/build/wt32_sc01_plus/firmware.bin`
3. The device reboots with the new firmware

The LittleFS partition (config, session data, web UI files) is preserved across firmware updates.

## Architecture

### Source Layout

```
firmware/
  src/
    main.cpp                    # Setup + main loop (Arduino setup/loop pattern)
    config.h                    # Pin assignments, constants, defaults
    config_manager.h/.cpp       # Load/save config.json on LittleFS
    wifi_manager.h/.cpp         # WiFiManager captive portal, mDNS, auto-reconnect
    ota_manager.h/.cpp          # Web-based OTA firmware update endpoint
    pid_controller.h/.cpp       # PID wrapper (QuickPID + lid-open, startup, split-range)
    temp_manager.h/.cpp         # ADS1115 reading, Steinhart-Hart, EMA filtering
    temp_predictor.h/.cpp       # Rolling linear regression for done-time prediction
    fan_controller.h/.cpp       # PWM output with kick-start, long-pulse, min-speed
    servo_controller.h/.cpp     # Damper servo control
    alarm_manager.h/.cpp        # Threshold logic, hysteresis, buzzer + web triggers
    cook_session.h/.cpp         # Session state, circular buffer, LittleFS persistence
    error_manager.h/.cpp        # Probe disconnect/short, fan stall, fire-out detection
    web_protocol.h/.cpp         # Shared WebSocket protocol (message building/parsing)
    web_server.h/.cpp           # ESPAsyncWebServer, REST + WebSocket handlers
    split_range.h               # Fan + damper coordination from PID output
    units.h                     # Temperature unit conversion utilities
    display/
      ui_init.h/.cpp            # LVGL screen setup (dashboard, graph, settings)
      ui_update.h/.cpp          # Real-time widget updates
      ui_setup_wizard.h/.cpp    # First-boot setup wizard screens
      ui_colors.h               # Shared LVGL color constants
      graph_history.h/.cpp      # Adaptive-condensing graph history buffer
    simulator/                  # Desktop simulator (see web-development.md)
      sim_main.cpp              # SDL2 + mongoose main loop
      sim_thermal.h/.cpp        # Charcoal smoker physics simulation
      sim_profiles.h            # Pre-built cook profiles
      sim_web_server.h/.cpp     # Mongoose HTTP + WebSocket server
      mongoose.h/.c             # Mongoose embedded web server library
  data/                         # Web UI files (uploaded to LittleFS)
  test/
    test_desktop/               # Native tests
    test_embedded/              # On-device tests
  platformio.ini
```

### Key Modules

**PID Controller** (`pid_controller.h/.cpp`) — wraps QuickPID with BBQ-specific features: proportional-on-measurement, derivative-on-measurement, integral anti-windup conditioning. Includes temperature-based lid detection with a warm-up guard, a two-minute timeout and shared UI controls.

**Temperature Manager** (`temp_manager.h/.cpp`) — reads ADS1115 ADC via I2C, converts raw ADC counts to temperature using Steinhart-Hart equation, applies EMA (exponential moving average) filtering, and supports per-probe calibration offsets.

**Fan + Damper Split-Range** (`split_range.h`) — the PID produces a single 0-100% output mapped to both actuators:
- Damper: linearly maps full PID range (0% = closed, 100% = open)
- Fan: activates above configurable threshold (default 30%), scales within its own min-max range
- Three modes: fan-only, fan+damper coordinated, damper-primary with fan boost

**Cook Session** (`cook_session.h/.cpp`) — stores the current cook as a circular buffer in RAM (600 samples, ~50 min at 5s intervals), flushed to LittleFS every 60 seconds for power-loss recovery. Only one session stored on device — web UI provides CSV/JSON download.

**Error Manager** (`error_manager.h/.cpp`) — detects probe disconnect (ADC max/open circuit), probe short (ADC zero), fire-out (pit declining >2°F/min for 10+ min at full fan), and Wi-Fi loss.

### Configuration

All user settings stored in `config.json` on LittleFS. Survives reboots and firmware OTA updates.

```json
{
  "wifi": { "ssid": "", "password": "" },
  "units": "F",
  "pid": { "p": 4.0, "i": 0.02, "d": 5.0 },
  "fan": { "mode": "fan_and_damper", "minSpeed": 15, "fanOnThreshold": 30 },
  "probes": {
    "pit":   { "name": "Pit",    "a": 7.3431401e-04, "b": 2.1574370e-04, "c": 9.5156860e-08, "offset": 0.0 },
    "meat1": { "name": "Meat 1", "a": 7.3431401e-04, "b": 2.1574370e-04, "c": 9.5156860e-08, "offset": 0.0 },
    "meat2": { "name": "Meat 2", "a": 7.3431401e-04, "b": 2.1574370e-04, "c": 9.5156860e-08, "offset": 0.0 }
  },
  "alarms": {
    "pitBand": 15,
    "pushover": { "enabled": false, "userKey": "", "apiToken": "" }
  },
  "setupComplete": false
}
```

### Technical Constants

**Thermoworks Pro-Series Steinhart-Hart Coefficients:**
- A = 7.3431401e-04, B = 2.1574370e-04, C = 9.5156860e-08
- Reference resistor: 10K ohm (1% metal film)
- 0.1uF ceramic filter cap on each ADC input

**PID Defaults (HeaterMeter-derived):**
- P = 4.0, I = 0.02, D = 5.0
- Temp sampling: 1s interval, 4-reading average
- PID compute: every 4 seconds
- Lid detection: arm after 30 seconds within ±2% of target; trigger below 94%, recover at 98%, timeout after two minutes.

**Fan Control:**
- PWM frequency: 100 Hz with 10-bit duty resolution (provisional; bench-verify the blower)
- Kick-start: 100% for 500ms
- Long-pulse mode below 10% (10s cycle)
- Min sustained speed: 15%

## Lid-open pause

The detector uses the internal Fahrenheit pit reading and target. It first waits
for 30 continuous seconds within ±2% of the target, checked with each 4-second PID
update. Only then can a reading below 94% of target trigger a pause. A setpoint
change or pit-probe fault clears and disarms automatic detection. An explicit
manual pause remains bounded by its original deadline; the probe interlock still
holds outputs off whenever the pit probe is invalid.

During a pause the fan is off, including any kick-start. Fan + Damper and Damper
Primary close the damper; Fan Only preserves its normal fully-open damper command.
The probe-fault interlock always stops the fan and closes the damper in every mode.

An automatic pause ends when the temperature reaches at least 98% of target, after a
two-minute timeout, when **Close lid** is pressed, or when detection is disabled.
PID integral/derivative history is reset using the current reading before control
resumes. Every exit requires a fresh settling period before another automatic pause can
trigger, so a still-cold pit cannot immediately retrigger it.

- Touchscreen: **Settings → Lid detection → Off** disables detection. Scroll below
  the Fan row if necessary. **Open lid / Close lid** is always available on the
  dashboard and in Settings. A small header label shows **Lid open** and the
  remaining pause time. Lid pauses keep the temperature cards and graph at full
  size; alarms and probe faults retain their banner. Settings shows whether the
  pause is manual or automatic.
- Web: **Settings → Lid detection** uses the same device setting. **Open lid /
  Close lid** is in the header and Settings; the pause banner displays remaining
  time without a second action button.
- Detection defaults to On, including when loading an older config. The setting is
  saved as `lid.enabled` in `/config.json`; it persists across device restarts.
  Close lid clears one pause without disabling future detection.

This is temperature inference, not a lid-position sensor. It retains the existing
6% threshold after arming; it does not measure the rate of cooling. Physical
blower behavior and PID tuning still need testing on the smoker.

Regression coverage: `pio test -e native` includes deterministic state/timer and
output-interlock tests. `python test/lid/run_checks.py` tests the actual QuickPID
engine, JSON command parsing and configuration migration/round-trips using cached
firmware dependencies. `python test/ui/run_checks.py` taps production LVGL controls;
`node test/web/test_lid_controls.cjs` checks browser commands and state synchronization.
Deploy both firmware and the LittleFS web assets to make the new controls available.

### Physical touch alignment check

Use **Settings → Touch test** to check the coordinates received from the physical
touchscreen. Tap the center of each numbered cross and lift your finger. The orange
ring stays at the reported position and the readout shows its X/Y coordinates.
Targets 1–5 are at (48,100), (432,100), (240,160), (48,236), and (432,236).
The same input coordinates drive the normal buttons. A consistent displacement
suggests a coordinate correction; missed taps or jumping positions need
input-driver/sensing investigation instead. Software-only hitbox tests do not
establish physical alignment.

For a device with measured correction values, **Try calibration** previews its
vertical correction. Retap the targets, then choose **Save calibration** only if
the orange ring aligns with your finger. **Cancel** or the 60-second timeout
restores the saved mapping. **Reset calibration** disables a saved correction,
retaining its values so it can be tried again. Failed saves leave the preview
unsaved. The test reports the corrected coordinates during preview and after Save.

`config.json` stores `touch.enabled`, `touch.yScale`, and `touch.yOffset`.
Absent/invalid settings preserve the panel's original mapping. A prepared profile
uses `enabled: false` until the owner saves it on the screen. Correction is applied
after panel rotation and before screen bounds: `y = yScale * reportedY + yOffset`.
X is unchanged. The reported Y readings 98, 101, 167, 257, 259 at targets
100, 100, 160, 236, 236 fit scale 0.85704777 and offset 15.216774, with a largest
fit residual of 1.8 pixels. These are measured device values, not firmware defaults;
physical verification, especially near the screen edges, is still required.

**Close test** returns to Settings. The test also closes after 60 seconds, waiting
for any held finger to lift before normal controls respond again. Cook control keeps
running during the test.

### Damper endpoint calibration

The damper percentage is a command, not physical position feedback. In
**Settings → Damper setup**, the blower is stopped and PID output is suspended.
Opening setup keeps the current servo command; it does not move to an endpoint.
Use the **±10 / ±50** microsecond adjustments to move the flap gradually. Mark
**Set closed** when it is physically closed without forcing its stop, then move
to the desired open position and mark **Set open**. Both positions must be marked
and at least 20 µs apart before the **0% / 50% / 100%** test buttons and
**Save & exit** are enabled. Test the positions visually before saving.

Closed and open can be in either numeric order, so reversed linkages need no
separate direction switch. `config.json` stores `damper.closedUs` and
`damper.openUs`. Old configs preserve the previous 544/1472 µs endpoints; invalid
values fall back to those defaults. Pulse commands stay within the existing
544–2400 µs driver range; these electrical limits do not establish the linkage's
safe mechanical travel. Saved endpoints also apply to startup and fault-close.

**Stop signal**, or 60 seconds without an adjustment/test/mark, detaches servo
pulses. Servo power remains connected. Setup stays open with the blower off;
an explicit adjustment/test resumes pulses. **Cancel** discards draft endpoints.
Save failure leaves the draft open and the live mapping unchanged. Save & exit
and Cancel return to normal control after a fresh PID computation, respecting any
remaining lid pause. During manual setup the servo is deliberately controlled by
the setup buttons even without a pit probe; the blower stays off in every mode.
Outside setup, the normal pit-probe fault interlock closes the calibrated damper.

### Optional meat probes and manual lid control

Meat 1 and Meat 2 are optional. An unplugged/open-circuit meat probe displays
`---`, leaves a gap in history, and produces no probe error. Existing meat targets
are retained for reconnection. A shorted meat probe remains a fault. The pit
probe is required: an open or shorted pit probe still stops fan/damper control.

Both UIs provide **Open lid / Close lid** on the dashboard and in Settings:

- **Open lid** immediately requests a manual fan pause, even before warm-up or
  when automatic detection is Off. It does not move the physical lid.
- A manual pause ignores temperature recovery and target changes. Turning auto
  detection On/Off does not cancel it. This lets you pause before lifting a hot lid.
- **Close lid** or the original two-minute deadline
  ends the pause. Repeated Open requests do not extend that deadline.
- No lid action overrides a pit-probe fault. A manual pause can remain indicated
  during a fault, but the outputs stay stopped and the fault is shown first.
- Manual pause is temporary, not a saved mode. The auto-detection setting remains
  the separate persistent On/Off option.

The same `ErrorManager::probeHasFault` rule supplies the error list and touchscreen
banner. Web telemetry keeps missing readings as null and reports shorts as -1;
completion estimates are cleared while meat readings are unavailable.
