#include "servo_controller.h"

#ifndef NATIVE_BUILD
#include <Arduino.h>
#endif

ServoController::ServoController()
    : _currentPulseUs(_calibration.closedUs)
    , _attached(false)
{
}

void ServoController::begin() {
#ifndef NATIVE_BUILD
    // Keep the LEDC fallback away from fan, buzzer and LCD backlight timers.
    ESP32PWM::allocateTimer(SERVO_PWM_TIMER);
    _servo.setPeriodHertz(50);  // Standard 50Hz servo frequency
    _servo.attach(PIN_SERVO, SERVO_MIN_US, SERVO_MAX_US);
    _attached = true;
#endif

    // Start at closed position
    setPosition(0);

#ifndef NATIVE_BUILD
    Serial.printf("[SERVO] Attached to pin %d, closed=%u us, open=%u us\n",
                  PIN_SERVO, _calibration.closedUs, _calibration.openUs);
#endif
}

void ServoController::setPosition(float percent) {
    writeMicroseconds(_calibration.pulseAt(percent));
}

void ServoController::setCalibration(const DamperCalibration& calibration) {
    if (calibration.valid()) _calibration = calibration; // No movement on configuration alone.
}

void ServoController::setPulseWidth(uint16_t us) {
    if (us < SERVO_MIN_US) us = SERVO_MIN_US;
    if (us > SERVO_MAX_US) us = SERVO_MAX_US;
    writeMicroseconds(us);
}

void ServoController::setAngle(uint8_t angleDeg) {
    if (angleDeg > 180) angleDeg = 180;

    uint16_t us = angleToMicroseconds((float)angleDeg);
    writeMicroseconds(us);
}

uint8_t ServoController::getCurrentAngle() const {
    return uint8_t(std::lround((_currentPulseUs - SERVO_MIN_US) * 180.0f / (SERVO_MAX_US - SERVO_MIN_US)));
}

float ServoController::getCurrentPositionPct() const {
    return _calibration.percentAt(_currentPulseUs);
}

void ServoController::detach() {
#ifndef NATIVE_BUILD
    if (_attached) {
        _servo.detach();
        _attached = false;
        Serial.println("[SERVO] Detached.");
    }
#endif
}

void ServoController::writeMicroseconds(uint16_t us) {
    _currentPulseUs = us;
#ifndef NATIVE_BUILD
    if (!_attached) {
        _servo.attach(PIN_SERVO, SERVO_MIN_US, SERVO_MAX_US);
        _attached = true;
    }
    _servo.writeMicroseconds(us);
#endif
}

uint16_t ServoController::angleToMicroseconds(float angle) const {
    // Linear interpolation from 0-180 degrees to SERVO_MIN_US-SERVO_MAX_US
    // This maps the full servo range. The damper only uses 0-90 degrees.
    if (angle < 0.0f) angle = 0.0f;
    if (angle > 180.0f) angle = 180.0f;

    float us = (float)SERVO_MIN_US +
               (angle / 180.0f) * (float)(SERVO_MAX_US - SERVO_MIN_US);
    return (uint16_t)(us + 0.5f);
}
