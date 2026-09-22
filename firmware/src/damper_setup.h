#pragma once
#include "damper_calibration.h"

enum class DamperSetupAction { Begin, Jog, MarkClosed, MarkOpen, Test, Stop, Save, Cancel };
struct DamperSetupState {
    DamperCalibration endpoints;
    DamperCalibration savedEndpoints;
    uint16_t pulseUs = SERVO_MIN_US;
    bool active = false, stopped = false, closedMarked = false, openMarked = false;
    bool ready() const { return active && closedMarked && openMarked && endpoints.valid(); }
    const DamperCalibration& testEndpoints() const { return ready() ? endpoints : savedEndpoints; }
};

// No hardware I/O or automatic sweeps. The control task applies explicit moves.
class DamperSetup {
public:
    static constexpr uint32_t IDLE_MS = 60000;
    const DamperSetupState& state() const { return _state; }
    void begin(const DamperCalibration& saved, uint16_t current, uint32_t now) {
        _state = {};
        _state.savedEndpoints = saved.valid() ? saved : DamperCalibration{};
        _state.endpoints = _state.savedEndpoints; _state.pulseUs = current;
        _state.active = true; _lastMove = now;
    }
    bool jog(int delta, uint32_t now) {
        if (!_state.active || (delta != -50 && delta != -10 && delta != 10 && delta != 50)) return false;
        int pulse = int(_state.pulseUs) + delta;
        _state.pulseUs = pulse < SERVO_MIN_US ? SERVO_MIN_US : pulse > SERVO_MAX_US ? SERVO_MAX_US : pulse;
        _state.stopped = false; _lastMove = now; return true;
    }
    bool mark(bool closed, uint32_t now) {
        if (!_state.active || _state.stopped) return false;
        if (closed) { _state.endpoints.closedUs = _state.pulseUs; _state.closedMarked = true; }
        else { _state.endpoints.openUs = _state.pulseUs; _state.openMarked = true; }
        _lastMove = now; return true;
    }
    bool test(int percent, uint32_t now) {
        if (!_state.active || (percent != 0 && percent != 50 && percent != 100)) return false;
        // Testing never requires calibration. Preview a complete valid draft;
        // otherwise retain the known saved range, including after partial edits.
        _state.pulseUs = _state.testEndpoints().pulseAt(percent);
        _state.stopped = false; _lastMove = now; return true;
    }
    void stop() { if (_state.active) _state.stopped = true; }
    bool timeout(uint32_t now) {
        if (!_state.active || _state.stopped || uint32_t(now - _lastMove) < IDLE_MS) return false;
        stop(); return true; // Remain in setup with blower off until explicit exit.
    }
    void end() { _state.active = false; }
private:
    DamperSetupState _state;
    uint32_t _lastMove = 0;
};
