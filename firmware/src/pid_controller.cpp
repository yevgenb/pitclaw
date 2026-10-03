#include "pid_controller.h"

#ifndef NATIVE_BUILD
#include <Arduino.h>
#endif

PidController::PidController()
    : _kp(PID_KP)
    , _ki(PID_KI)
    , _kd(PID_KD)
    , _pidInput(0.0f)
    , _pidOutput(0.0f)
    , _pidSetpoint(0.0f)
#ifndef NATIVE_BUILD
    , _pid(nullptr)
#endif
    , _pidNeedsReset(true)
    , _enabled(true)
    , _settling(false)
{
}

void PidController::begin() {
    begin(PID_KP, PID_KI, PID_KD);
}

void PidController::begin(float kp, float ki, float kd) {
    _kp = kp;
    _ki = ki;
    _kd = kd;
    _pidInput = 0.0f;
    _pidOutput = 0.0f;
    _pidSetpoint = 0.0f;
    _lid.reset();
    _pidNeedsReset = true;
    _enabled = true;
    _settling = false;

#ifndef NATIVE_BUILD
    if (_pid != nullptr) {
        delete _pid;
    }

    _pid = new QuickPID(&_pidInput, &_pidOutput, &_pidSetpoint,
                        _kp, _ki, _kd,
                        QuickPID::pMode::pOnMeas,
                        QuickPID::dMode::dOnMeas,
                        QuickPID::iAwMode::iAwCondition,
                        QuickPID::Action::direct);

    _pid->SetOutputLimits(PID_OUTPUT_MIN, PID_OUTPUT_MAX);
    _pid->SetSampleTimeUs(PID_SAMPLE_MS * 1000UL);
    _pid->SetMode(QuickPID::Control::automatic);


    Serial.printf("[PID] Initialized: Kp=%.2f Ki=%.3f Kd=%.2f, interval=%dms\n",
                  _kp, _ki, _kd, PID_SAMPLE_MS);
#endif
}

float PidController::compute(float currentTemp, float setpoint) {
#ifndef NATIVE_BUILD
    return compute(currentTemp, setpoint, millis());
#else
    return compute(currentTemp, setpoint, 0); // Tests use the explicit clock overload.
#endif
}

float PidController::compute(float currentTemp, float setpoint, uint32_t nowMs) {
    if (!_enabled || !std::isfinite(currentTemp) || !std::isfinite(setpoint) || setpoint <= 0) {
        if (!_enabled) _lid.reset();
        else _lid.update(currentTemp, setpoint, nowMs); // Manual pause still expires during a probe fault.
        _pidNeedsReset = true;
        _settling = false;
        _pidOutput = 0;
        return 0;
    }
    if (setpoint != _pidSetpoint) _pidNeedsReset = true;
    // Supply fresh measurements BEFORE initializing derivative/integral history.
    _pidInput = currentTemp;
    _pidSetpoint = setpoint;
    if (_lid.update(currentTemp, setpoint, nowMs)) _pidNeedsReset = true;
    if (_lid.isOpen()) {
        _pidOutput = 0;
        if (_pidNeedsReset) restartPid(false);
        return 0;
    }
    if (_pidNeedsReset) restartPid(true);
    const float error = std::fabs(setpoint - currentTemp);
    if (error <= PID_SETTLING_ENTER_F) _settling = true;
    else if (error > PID_SETTLING_EXIT_F) _settling = false;
#ifndef NATIVE_BUILD
    if (_pid) {
        // With pOnMeas, conditional anti-windup can make the integral increment
        // negative on a small rise even while below target and unsaturated.
        // Clamp near target so a persistent shortfall builds demand. Keep the
        // existing conditional damping for warm-up and large disturbances;
        // changing modes preserves the accumulated output and measurement history.
        _pid->SetAntiWindupMode(_settling ? QuickPID::iAwMode::iAwClamp
                                        : QuickPID::iAwMode::iAwCondition);
        _pid->Compute();
    }
    if (_pidOutput < PID_OUTPUT_MIN) _pidOutput = PID_OUTPUT_MIN;
    if (_pidOutput > PID_OUTPUT_MAX) _pidOutput = PID_OUTPUT_MAX;
#endif
    return _pidOutput;
}

void PidController::restartPid(bool automatic) {
    _pidOutput = 0;
    _settling = false;
#ifndef NATIVE_BUILD
    if (_pid) {
        _pid->SetMode(QuickPID::Control::manual);
        _pid->SetAntiWindupMode(QuickPID::iAwMode::iAwCondition);
        _pid->Reset();
        if (automatic && _enabled) _pid->SetMode(QuickPID::Control::automatic);
    }
#endif
    _pidNeedsReset = false;
}

float PidController::getOutput() const {
    return _pidOutput;
}

void PidController::setTunings(float kp, float ki, float kd) {
    _kp = kp;
    _ki = ki;
    _kd = kd;

#ifndef NATIVE_BUILD
    if (_pid != nullptr) {
        _pid->SetTunings(_kp, _ki, _kd);
    }
    Serial.printf("[PID] Tunings updated: Kp=%.2f Ki=%.3f Kd=%.2f\n", _kp, _ki, _kd);
#endif
}

void PidController::resetIntegrator() {
    _pidOutput = 0;
    _pidNeedsReset = true;
    _settling = false;
}

bool PidController::isLidOpen() const { return _lid.isOpen(); }

void PidController::setLidDetectionEnabled(bool enabled) {
    const bool paused = _lid.isOpen();
    _lid.setEnabled(enabled);
    if (paused && !_lid.isOpen()) resetIntegrator();
}

void PidController::openLid(uint32_t nowMs) {
    if (_enabled && _lid.openManual(nowMs)) resetIntegrator();
}

void PidController::resumeLid() {
    if (_lid.resume()) resetIntegrator();
}

void PidController::resetLidDetection() {
    _lid.resetAutomatic();
    resetIntegrator();
}

void PidController::setEnabled(bool enabled) {
    if (_enabled != enabled) { _lid.reset(); resetIntegrator(); }
    _enabled = enabled;
    if (!enabled) _pidOutput = 0;
}

bool PidController::isEnabled() const { return _enabled; }
