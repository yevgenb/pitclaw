#pragma once
#include "config.h"
#include <cmath>
#include <stdint.h>

struct DamperCalibration {
    uint16_t closedUs = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * DAMPER_CLOSED / 180;
    uint16_t openUs = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * DAMPER_OPEN / 180;
    bool valid() const {
        const int span = int(openUs) - int(closedUs);
        return closedUs >= SERVO_MIN_US && closedUs <= SERVO_MAX_US &&
               openUs >= SERVO_MIN_US && openUs <= SERVO_MAX_US && (span >= 20 || span <= -20);
    }
    uint16_t pulseAt(float percent) const {
        if (!std::isfinite(percent) || percent < 0) percent = 0;
        if (percent > 100) percent = 100;
        return uint16_t(std::lround(closedUs + (int(openUs) - int(closedUs)) * percent / 100));
    }
    float percentAt(uint16_t pulse) const {
        if (!valid()) return 0;
        const float pct = (int(pulse) - int(closedUs)) * 100.0f / (int(openUs) - int(closedUs));
        return pct < 0 ? 0 : pct > 100 ? 100 : pct;
    }
};
