#pragma once
#include "config.h"
#include <cmath>
#include <stdint.h>

// Shared by the device and thermal simulator. Time is injected for deterministic tests.
class LidDetector {
public:
    void reset() {
        _open = _manual = _armed = _warming = _haveTarget = false;
    }
    // Automatic detection and the operator's explicit pause are independent.
    void resetAutomatic() { if (!_manual) reset(); }
    void setEnabled(bool enabled) {
        if (_enabled != enabled) { _enabled = enabled; resetAutomatic(); }
    }
    bool openManual(uint32_t now) {
        const bool changed = !_open || !_manual;
        if (!_open) _openedAt = now; // Repeated commands never extend a pause.
        _open = _manual = true;
        _armed = _warming = _haveTarget = false;
        return changed;
    }
    bool isManual() const { return _open && _manual; }
    bool isEnabled() const { return _enabled; }
    uint16_t timeoutSeconds() const { return _timeoutMs / 1000; }
    bool setTimeoutSeconds(uint16_t seconds) {
        if (!isValidLidTimeoutSeconds(seconds)) return false;
        _timeoutMs = uint32_t(seconds) * 1000; // Preserve elapsed time in an active pause.
        return true;
    }
    bool isOpen() const { return _open; }
    bool isArmed() const { return _armed; }
    bool resume() {
        const bool wasOpen = _open;
        if (wasOpen) reset(); // Require a fresh warm-up, even after a timeout.
        return wasOpen;
    }
    uint16_t remainingSeconds(uint32_t now) const {
        if (!_open) return 0;
        const uint32_t elapsed = now - _openedAt;
        return elapsed >= _timeoutMs ? 0 :
            static_cast<uint16_t>((_timeoutMs - elapsed + 999) / 1000);
    }
    // Returns true when the pause starts or ends, so the PID can reset its history.
    bool update(float temp, float target, uint32_t now) {
        const bool wasOpen = _open;
        if (_manual) {
            // Hot readings, a changed target or auto-detection Off must not undo
            // an operator's pause while they are opening the lid.
            if (static_cast<uint32_t>(now - _openedAt) >= _timeoutMs) reset();
            return wasOpen != _open;
        }
        if (!_enabled || !std::isfinite(temp) || !std::isfinite(target) || target <= 0) {
            reset();
            return wasOpen;
        }
        if (!_haveTarget || target != _target) {
            reset();
            _target = target;
            _haveTarget = true;
        }
        const float recover = target * (1.0f - LID_OPEN_RECOVER_PCT / 100.0f);
        if (_open) {
            if (temp >= recover || static_cast<uint32_t>(now - _openedAt) >= _timeoutMs)
                reset();
        } else if (!_armed) {
            const bool nearTarget = std::fabs(temp - target) <= target * LID_OPEN_RECOVER_PCT / 100.0f;
            if (!nearTarget) _warming = false;
            else if (!_warming) { _warming = true; _warmSince = now; }
            else if (static_cast<uint32_t>(now - _warmSince) >= LID_OPEN_ARM_MS) {
                _armed = true;
                _warming = false;
            }
        } else if (temp < target * (1.0f - LID_OPEN_DROP_PCT / 100.0f)) {
            _open = true;
            _openedAt = now;
        }
        return wasOpen != _open;
    }
private:
    bool _enabled = true, _open = false, _manual = false, _armed = false, _warming = false, _haveTarget = false;
    float _target = 0;
    uint32_t _warmSince = 0, _openedAt = 0;
    uint32_t _timeoutMs = LID_OPEN_TIMEOUT_MS;
};
