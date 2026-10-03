# Lid-control integration checks

Build the firmware once to fetch its QuickPID and ArduinoJson dependencies, then
run `python test/lid/run_checks.py` from `firmware/`. The runner uses `CXX` (or
`c++`) and creates temporary executables.

- The real embedded `PidController` and QuickPID run against a fake clock/Serial
  boundary. Checks cover cold-start output and integral/derivative reset on
  recovery, resume, timeout and disabling detection. Manual pause tests also cover
  a hot pit with automatic detection Off.
- The tuning fixture holds the measured pit at 210°F against a 225°F target,
  compares the old and new integral gains through the real fan/damper mapping,
  and checks that above-target readings remove heat demand. It measures controller
  response only; actual smoker overshoot and settling require a cook test.
- The settling fixture drives the production controller with below-target
  temperature ripple and compares it with legacy conditional anti-windup. It
  checks accumulated demand, unchanged cold warm-up, 10°F/15°F mode hysteresis,
  overshoot correction, and reset behavior after a fault, target change or pause.
  Cold-start and hot-restart closed-loop checks use an illustrative thermal
  model; their temperature results do not predict this smoker's overshoot.
- The real JSON codec and configuration serializer cover command validation,
  old-config migration, disabled-setting round trips, and complete status packets
  with all eight error slots occupied. These checks do not exercise flash hardware.
  Legacy factory PID settings migrate once without changing damper calibration;
  custom tunings and an explicitly saved rollback survive subsequent loads.

The PlatformIO native PID suite covers settling, threshold boundaries, target
changes, invalid readings, re-arming and clock wraparound. UI tests are in
`test/ui/` and `test/web/test_lid_controls.cjs`.
