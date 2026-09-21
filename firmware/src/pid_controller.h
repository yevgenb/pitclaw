#pragma once

#include "config.h"
#include "lid_detector.h"
#include <stdint.h>

#ifndef NATIVE_BUILD
#include <QuickPID.h>
#endif

class PidController {
public:
    PidController();

    // Initialize PID with defaults from config.h. Call once from setup().
    void begin();

    // Initialize PID with custom tunings
    void begin(float kp, float ki, float kd);

    // Run one PID computation if the sample interval has elapsed.
    // Returns the PID output (0-100%). Handles lid-open detection internally.
    float compute(float currentTemp, float setpoint);
    float compute(float currentTemp, float setpoint, uint32_t nowMs);

    // PID output in the range [0..100] percent
    float getOutput() const;

    // Update tuning parameters at runtime
    void setTunings(float kp, float ki, float kd);

    // Get current tuning values
    float getKp() const { return _kp; }
    float getKi() const { return _ki; }
    float getKd() const { return _kd; }

    // Lid-open detection
    bool isLidOpen() const;
    bool isLidDetectionEnabled() const { return _lid.isEnabled(); }
    void setLidDetectionEnabled(bool enabled);
    void resumeLid();
    void openLid(uint32_t nowMs);
    bool isLidManual() const { return _lid.isManual(); }
    // Re-arm automatic detection after a fault/target change; retain an explicit manual pause.
    void resetLidDetection();
    uint16_t lidRemainingSeconds(uint32_t nowMs) const { return _lid.remainingSeconds(nowMs); }

    // Reset integrator for bumpless transfer on setpoint change
    void resetIntegrator();

    // Enable or disable PID computation
    void setEnabled(bool enabled);
    bool isEnabled() const;

private:
    void restartPid(bool automatic);

    float _kp, _ki, _kd;

    // QuickPID uses float references for input/output/setpoint
    float _pidInput;
    float _pidOutput;
    float _pidSetpoint;

#ifndef NATIVE_BUILD
    QuickPID* _pid;
#endif

    LidDetector _lid;
    bool _pidNeedsReset;
    bool _enabled;

};
