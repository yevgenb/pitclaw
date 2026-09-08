#include <unity.h>
#include "Arduino.h"

// Exercise embedded calls through the fake HAL instead of compiling them out.
#undef NATIVE_BUILD
#include "fan_controller.cpp"
#include "alarm_manager.cpp"

void setUp() {
    fakeNow = 0;
    failSetup = false;
    attachedPin = -1;
    outputLevel = -1;
    outputDuty = 0;
    writeCount = 0;
    toneChannel = 255;
}
void tearDown() {}

void test_pwm_clock_divider_fits_esp32_s3() {
    FanController fan;
    fan.begin();
    // S3 LEDC XTAL is 40 MHz; the divider has 10 integer and 8 fractional bits.
    const uint32_t divider = uint64_t(40000000) * 256 /
                             (setupFrequency * (1U << setupResolution));
    TEST_ASSERT_GREATER_OR_EQUAL_UINT32(256, divider);
    TEST_ASSERT_LESS_OR_EQUAL_UINT32(0x3ffff, divider);
    TEST_ASSERT_EQUAL_UINT32(100, setupFrequency);
    TEST_ASSERT_EQUAL_INT(PIN_FAN_PWM, attachedPin);
    TEST_ASSERT_EQUAL_UINT32(0, outputDuty);
}

void test_public_duty_scales_to_hardware_range() {
    FanController fan;
    fan.begin();
    fan.setManualDuty(128);
    TEST_ASSERT_EQUAL_UINT8(128, fan.getCurrentDuty());
    TEST_ASSERT_EQUAL_UINT32(514, outputDuty);
    fan.setManualDuty(255);
    TEST_ASSERT_EQUAL_UINT32(1023, outputDuty);
    fan.off();
    TEST_ASSERT_EQUAL_UINT32(0, outputDuty);
}

void test_failed_setup_never_attaches_or_writes_pwm() {
    failSetup = true;
    FanController fan;
    fan.begin();
    fan.setSpeed(100);
    fan.update();
    fan.setManualDuty(255);
    fan.off();
    TEST_ASSERT_EQUAL_INT(-1, attachedPin);
    TEST_ASSERT_EQUAL_INT(LOW, outputLevel);
    TEST_ASSERT_EQUAL_UINT32(0, writeCount);
}

void test_kickstart_returns_to_requested_hardware_duty() {
    FanController fan;
    fan.begin();
    fan.setSpeed(50);
    fan.update();
    TEST_ASSERT_EQUAL_UINT32(1023, outputDuty);
    fakeNow = FAN_KICKSTART_MS + 1;
    fan.update();
    TEST_ASSERT_FALSE(fan.isKickStarting());
    TEST_ASSERT_EQUAL_UINT32(514, outputDuty);
}

void test_buzzer_uses_a_separate_timer() {
    AlarmManager alarm;
    alarm.begin();
    TEST_ASSERT_EQUAL_UINT8(4, toneChannel);
    TEST_ASSERT_NOT_EQUAL(FAN_PWM_CHANNEL / 2, toneChannel / 2);
    TEST_ASSERT_NOT_EQUAL(SERVO_PWM_TIMER, toneChannel / 2);
    TEST_ASSERT_NOT_EQUAL(7 / 2, toneChannel / 2);  // PanelLan backlight channel 7
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_pwm_clock_divider_fits_esp32_s3);
    RUN_TEST(test_public_duty_scales_to_hardware_range);
    RUN_TEST(test_failed_setup_never_attaches_or_writes_pwm);
    RUN_TEST(test_kickstart_returns_to_requested_hardware_duty);
    RUN_TEST(test_buzzer_uses_a_separate_timer);
    return UNITY_END();
}
