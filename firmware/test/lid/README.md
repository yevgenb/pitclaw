# Lid-control integration checks

Build the firmware once to fetch its QuickPID and ArduinoJson dependencies, then
run `python test/lid/run_checks.py` from `firmware/`. The runner uses `CXX` (or
`c++`) and creates temporary executables.

- The real embedded `PidController` and QuickPID run against a fake clock/Serial
  boundary. Checks cover cold-start output and integral/derivative reset on
  recovery, resume, timeout and disabling detection. Manual pause tests also cover
  a hot pit with automatic detection Off.
- The real JSON codec and configuration serializer cover command validation,
  old-config migration, disabled-setting round trips, and complete status packets
  with all eight error slots occupied. These checks do not exercise flash hardware.

The PlatformIO native PID suite covers settling, threshold boundaries, target
changes, invalid readings, re-arming and clock wraparound. UI tests are in
`test/ui/` and `test/web/test_lid_controls.cjs`.
