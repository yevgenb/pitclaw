#pragma once

#include "config.h"
#include "damper_calibration.h"
#include <stdint.h>

#ifndef NATIVE_BUILD
#include <ESP32Servo.h>
#endif

class ServoController {
public:
    ServoController();

    // Attach servo to PIN_SERVO. Call once from setup().
    void begin();

    // Set damper position from 0-100% (0=closed, 100=open).
    // Maps to the saved endpoints, in either direction.
    void setPosition(float percent);
    void setCalibration(const DamperCalibration& calibration);
    const DamperCalibration& getCalibration() const { return _calibration; }
    void setPulseWidth(uint16_t us);
    uint16_t getCurrentPulseUs() const { return _currentPulseUs; }

    // Move servo to a specific angle in degrees. Useful for testing.
    void setAngle(uint8_t angleDeg);

    // Commanded servo angle in degrees, not physical feedback.
    uint8_t getCurrentAngle() const;

    // Commanded position as a percentage of the calibrated range (0-100).
    float getCurrentPositionPct() const;

    // Detach the servo signal to avoid jitter when not actively moving
    void detach();

private:
    // Write microsecond pulse value to the servo
    void writeMicroseconds(uint16_t us);

    // Map angle to microseconds for precise control
    uint16_t angleToMicroseconds(float angle) const;

#ifndef NATIVE_BUILD
    Servo _servo;
#endif

    DamperCalibration _calibration;
    uint16_t _currentPulseUs;
    bool    _attached;
};
