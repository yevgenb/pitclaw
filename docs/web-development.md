# Web UI Development

Guide for developing the Pit Claw web interface and using the desktop simulator.
See the [project status](../README.md#current-project-state) for the currently
verified device build.

## Simulator

The simulator runs the LVGL touchscreen UI in an SDL2 window and serves the web UI via an embedded web server — no ESP32 hardware needed.

### Build and Run

```bash
cd firmware

# Build
pio run -e simulator

# Run (opens SDL2 window + web server at http://localhost:3000)
.pio/build/simulator/program
```

### Command-Line Options

```bash
.pio/build/simulator/program --speed 10         # 10x time acceleration
.pio/build/simulator/program --speed 50         # 50x speed (12-hour cook in ~15 min)
.pio/build/simulator/program --profile stall    # brisket stall scenario
.pio/build/simulator/program --port 8080        # custom web server port
```

### Cook Profiles

| Profile | Simulated scenario |
|---------|--------------------|
| `normal` | 225°F pit, meat targets of 203°F and 180°F |
| `stall` | 225°F pit with a 150–170°F brisket stall |
| `hot-fast` | 300°F pit, both meat targets at 185°F |
| `temp-change` | Pit target changes from 225°F to 275°F at four simulated hours |
| `lid-open` | Lid openings at two, five and eight simulated hours |
| `fire-out` | Fire goes out at four simulated hours |
| `probe-disconnect` | Meat 1 disconnects at three simulated hours |

### How It Works

- **SDL2 window** renders the LVGL touchscreen UI (same code as firmware)
- **Mongoose HTTP server** serves web UI files from `firmware/data/`
- **WebSocket** on the same port sends simulated data using the shared protocol (`web_protocol.cpp`)
- **Thermal model** (`sim_thermal.cpp`) supplies simplified fire, temperature and controller behavior for UI scenarios

Both interfaces receive the same simulated readings and shared protocol. The
thermal simulator has its own simplified controller; it does not run production
QuickPID and its pit model approaches the selected target directly. Use
`python3 test/lid/run_checks.py` for real-controller regression checks, then a
physical smoker test to assess warm-up and overshoot.

### Editing the Web UI

Web UI files live in `firmware/data/`:

```
firmware/data/
  index.html          # Main page
  app.js              # Application logic
  style.css           # Styles
  manifest.json       # PWA manifest
  favicon.svg         # App icon
  sw.js               # Service worker (offline shell caching)
```

With the simulator, edit these files and refresh your browser without recompiling.
For the ESP32, rebuild/upload firmware; it embeds these assets so web UI updates
preserve LittleFS settings and session history.

When changing the bundled interface, keep `UI_BUILD` in `app.js`, `WEB_UI_BUILD`
in `src/config.h`, the versioned script URL in `index.html`, and the worker's
`APP_SHELL` script URL synchronized. Bump `CACHE_VERSION` in `sw.js` too. The
dashboard announces a newer interface build and offers Reload; temperature edits
defer automatic reload rather than losing the draft. Check this with
`node test/web/test_ui_updates.cjs`.

**Key constraint:** The web UI code must work identically on both the simulator and the real ESP32. No simulator-specific code in the web UI — the abstraction boundary is the WebSocket protocol.

## Web UI Features

- **Live temperatures** — pit and both meat probes with set points
- **Temperature graph** — uPlot time-series chart with pit temp, meat temps, fan %, and damper %
- **Predictive curve** — dashed projection from current meat temp to target, with predicted done time
- **Controls** — pit/meat targets, fan mode, and manual/automatic lid pauses with an adjustable timeout
- **Cook timer** — starts with the first valid meat-probe reading; uses device timestamps and pauses its display while disconnected
- **Session export** — CSV of the controller's retained 600-point history (about 50 minutes at five-second sampling); download before New Session
- **OTA update** — manual file upload at `/update`; Settings reports the version, and GitHub release checks are disabled by default
- **Alarms** — local buzzer, browser audio and browser notifications where supported; Pushover delivery is not implemented
- **Optional authentication** — Settings → Access enables a shared password with
  a simple login screen. It protects the API, WebSocket and firmware upload too.
  See the [reverse proxy guide](../firmware/docs/reverse-proxy.md#optional-authentication)
  for HTTPS configuration, sessions and password recovery.
- **Diagnostics** — Settings → Diagnostics → Download Wi-Fi log exports the bounded, restart-persistent connection event log

The simulator saves login settings in `sim-auth.json` in its working directory,
outside its public asset directory. This local file is ignored by Git. Use a
temporary working directory for isolated auth checks. Run
`python3 test/auth/run_checks.py` from `firmware/` to test the production server
adapter and shared authentication policy without SDL or ESP32 hardware.

### Graph

The browser retains up to four hours of received readings with a two-hour default
chart window. A fresh connection replays the controller's latest 600 samples.
Dashed prediction curves appear when enough valid meat readings and a target are
available. They use rolling linear regression and do not predict stalls or replace
the measured temperature. All displayed times use the browser's local timezone.

### HTTP diagnostics and access

Live control/history uses WebSocket; authentication, diagnostics and OTA also use
HTTP. Paths below are relative to the installation root, including a proxy prefix.

| Method | Path | Purpose |
|---|---|---|
| GET | `api/auth` | Public authentication status |
| POST | `api/auth/login` | Sign in with a URL-encoded password |
| POST | `api/auth/logout`, `api/auth/settings` | End a session or change access settings |
| GET | `api/version` | Firmware version, UI build and release-check setting |
| GET | `api/wifi-log` | Download connection/IP events as an uncached JSON attachment |
| GET | `api/servo` | Read servo PWM diagnostics; `?sample=1` also samples GPIO13 |
| GET | `update` | ElegantOTA manual firmware-upload page |

When authentication is enabled, routes other than the shell and auth status/login
require a session. Raw LittleFS files are not HTTP resources, including for signed-in
clients. The Wi-Fi log contains 32 events in a fixed 1,040-byte checkpoint, with
changed snapshots saved at most once per minute. The simulator returns an empty
log marked as having no Wi-Fi hardware. See
[event fields, persistence and limits](firmware-development.md#wi-fi-event-diagnostics).

A changing signal reading shows radio activity, not verified IP reachability.
If the router lists the device offline, note its displayed IP/signal and the time,
then download the log after access is restored. An HTTP 401 from a protected API
means login is needed; a connection timeout is a different failure. The firmware
currently records events and trusts SDK connection status; it has no active
gateway reachability check.

### PWA

The web UI is a Progressive Web App:

- `manifest.json` defines the app name, icon, theme color, and `display: standalone`
- `sw.js` caches the app shell (HTML/JS/CSS) for offline loading — data still requires a WebSocket connection
- "Add to Home Screen" for a native-app experience on phones:
  - **iOS**: Safari → Share → Add to Home Screen
  - **Android**: Chrome → Menu → Add to Home Screen

## WebSocket Protocol

Temperature snapshots, history and control commands use JSON over WebSocket.
The examples store temperatures and targets in Fahrenheit, independently of display units.

### Server → Client

**Periodic data** (every 1-2 seconds):
```json
{
  "type": "data",
  "ts": 1707600000,
  "pit": 225.5,
  "meat1": 145.2,
  "meat2": 98.7,
  "fan": 45,
  "damper": 80,
  "sp": 225,
  "lid": false,
  "lidEnabled": true,
  "lidTimeoutSeconds": 120,
  "lidRemaining": 0,
  "lidManual": false,
  "fanMode": "fan_and_damper",
  "est": 1707614400,
  "meat1Target": 203,
  "meat2Target": null,
  "errors": []
}
```

**History dump** (on connect):
```json
{
  "type": "history",
  "sp": 225,
  "meat1Target": 203,
  "meat2Target": null,
  "data": [
    {"ts": 1707600000, "pit": 225.5, "meat1": 145.2, "meat2": null,
     "fan": 45, "damper": 80, "sp": 225, "lid": false}
  ]
}
```

**Session events:**
```json
{"type": "session", "action": "reset", "sp": 225}
{"type": "session", "action": "download", "format": "csv", "data": "timestamp,pit,meat1,...\n..."}
```

### Client → Server

```json
{"type": "set", "sp": 250}
{"type": "alarm", "meat1Target": 203, "meat2Target": 185, "pitBand": 15}
{"type": "session", "action": "new"}
{"type": "session", "action": "download", "format": "csv"}
{"type": "config", "fanMode": "fan_and_damper"}
```

### Timestamps

After network time synchronization, ESP32 timestamps are UTC epoch seconds. The
browser converts them to local time. Before synchronization, it normalizes boot
timestamps for display and avoids mixing them with old wall-clock history. PID
timing uses the monotonic hardware clock rather than these display timestamps.
History points currently carry the latest setpoint; the device does not retain
the original setpoint separately for every stored sample.

Partial alarm commands leave omitted targets unchanged. Send an explicit null,
for example `{"type":"alarm","meat1Target":null}`, to clear that target. Pit and
meat targets are runtime state: reboot restores the default 225°F pit target and
clears meat targets. Persistent configuration, authentication and history remain.

### Lid pause controls

`lid` reports an active pause. `lidEnabled` is the saved detection setting and
`lidRemaining` is the remaining timeout in seconds (zero when inactive).
`lidTimeoutSeconds` is the saved duration (30–600 seconds in 30-second steps). The
browser reads these from device snapshots so touchscreen changes and reconnects
stay synchronized. It disables the controls while disconnected or if older
firmware does not publish `lidEnabled`.

Send `{"type":"config","lidEnabled":false}` to disable detection (or `true` to
enable it), and `{"type":"lid","action":"resume"}` to end the current pause.
These are separate commands; a config command must not combine fan mode and lid
setting changes. The firmware applies requests on its control task, saves setting
changes, then broadcasts the new state. Resume never overrides a pit-probe fault.
The C++ thermal simulator uses the same detector while its physical lid events
continue separately; Resume does not pretend the simulated lid has closed.

`{"type":"config","lidTimeoutSeconds":180}` saves a three-minute timeout.
Do not combine it with another setting in the same command. Existing pauses keep
their original start time; changing the duration changes their deadline from that
time. The browser disables timeout editing when older firmware omits this field.

`{"type":"lid","action":"open"}` starts a manual pause. The dashboard
Open lid / Close lid button sends `open` or the existing `resume` action according
to the latest device state. `lidManual` identifies manual pauses and advertises
manual-control support; older firmware can still be resumed but cannot be sent
an unsupported Open action. Automatic detection may remain disabled throughout.
A manual pause ends only on Close/Resume or timeout, not on a warm reading.
Missing meat probes are normal null readings; shorts remain -1/ERR.
