#include "servo_controller.h"

#ifndef NATIVE_BUILD
#include <Arduino.h>
#include <hal/gpio_ll.h>
#endif

ServoController::ServoController()
    : _currentPulseUs(_calibration.closedUs)
    , _attached(false)
    , _pwmReady(false)
{
}

void ServoController::begin() {
    detach();
#ifndef NATIVE_BUILD
    pinMode(PIN_SERVO, OUTPUT);
    digitalWrite(PIN_SERVO, LOW);
    _pwmReady = ledcSetup(SERVO_PWM_CHANNEL, SERVO_PWM_FREQ, SERVO_PWM_RESOLUTION) != 0;
    if (!_pwmReady) Serial.println("[SERVO] PWM setup failed; signal held low.");
#else
    _pwmReady = true;
#endif

    // Start at closed position
    setPosition(0);

#ifndef NATIVE_BUILD
    Serial.printf("[SERVO] GPIO%d channel %d: %lu Hz, closed=%u us, open=%u us\n",
                  PIN_SERVO, SERVO_PWM_CHANNEL, (unsigned long)getPwmFrequencyHz(), _calibration.closedUs, _calibration.openUs);
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
    if (_attached) {
#ifndef NATIVE_BUILD
        ledcWrite(SERVO_PWM_CHANNEL, 0);
        ledcDetachPin(PIN_SERVO);
        pinMode(PIN_SERVO, OUTPUT);
        digitalWrite(PIN_SERVO, LOW);
        Serial.println("[SERVO] Signal stopped.");
#endif
        _attached = false;
    }
}

void ServoController::writeMicroseconds(uint16_t us) {
    _currentPulseUs = us;
    if (!_pwmReady) return;
#ifndef NATIVE_BUILD
    // Keep a continuous 50 Hz train. Preload the requested pulse before routing
    // the pin, including after Stop, so reattachment cannot emit a neutral pulse.
    const uint32_t ticks = (uint64_t(us) * SERVO_PWM_FREQ * (1UL << SERVO_PWM_RESOLUTION) + 500000) / 1000000;
    ledcWrite(SERVO_PWM_CHANNEL, ticks);
#endif
    if (!_attached) {
#ifndef NATIVE_BUILD
        ledcAttachPin(PIN_SERVO, SERVO_PWM_CHANNEL);
        // Arduino's attach reads the *latched* duty, which may still be zero
        // until the next 20 ms frame. Reapply after binding the pin/timer.
        ledcWrite(SERVO_PWM_CHANNEL, ticks);
#endif
        _attached = true;
    }
}

uint32_t ServoController::getPwmFrequencyHz() const {
#ifndef NATIVE_BUILD
    return ledcReadFreq(SERVO_PWM_CHANNEL);
#else
    return 0;
#endif
}

uint32_t ServoController::getPwmDutyTicks() const {
#ifndef NATIVE_BUILD
    return ledcRead(SERVO_PWM_CHANNEL);
#else
    return 0;
#endif
}

ServoSignalSample ServoController::sampleSignal() const {
    ServoSignalSample sample;
#ifndef NATIVE_BUILD
    // Enable only the pad's input receiver. pinMode(INPUT/OUTPUT) would reset
    // its output matrix routing and disturb the servo being diagnosed.
    gpio_ll_input_enable(&GPIO, static_cast<gpio_num_t>(PIN_SERVO));
    sample.highUs = pulseIn(PIN_SERVO, HIGH, 50000);
    sample.lowUs = pulseIn(PIN_SERVO, LOW, 50000);
#endif
    return sample;
}

uint16_t ServoController::angleToMicroseconds(float angle) const {
    // Linear interpolation from 0-180 degrees to SERVO_MIN_US-SERVO_MAX_US
    // Direct angle tests use the full range; saved endpoints set damper travel.
    if (angle < 0.0f) angle = 0.0f;
    if (angle > 180.0f) angle = 180.0f;

    float us = (float)SERVO_MIN_US +
               (angle / 180.0f) * (float)(SERVO_MAX_US - SERVO_MIN_US);
    return (uint16_t)(us + 0.5f);
}
