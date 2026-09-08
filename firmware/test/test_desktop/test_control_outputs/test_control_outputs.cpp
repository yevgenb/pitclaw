#include <unity.h>
#include "control_outputs.h"
#include "fan_controller.cpp"
#include "servo_controller.cpp"

static FanController fan;
static ServoController damper;
static const char* modes[] = {"fan_only", "fan_and_damper", "damper_primary"};

void setUp(void) {
    fan = FanController();
    fan.begin();
    damper = ServoController();
    damper.begin();
}
void tearDown(void) {}

static void assertStopped() {
    fan.update();
    TEST_ASSERT_EQUAL_UINT8(0, fan.getCurrentDuty());
    TEST_ASSERT_FALSE(fan.isKickStarting());
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, damper.getCurrentPositionPct());
}

void test_fault_cancels_kickstart_and_closes_every_mode(void) {
    for (const char* mode : modes) {
        applyControlOutputs(fan, damper, true, 100.0f, mode, 30.0f);
        fan.update();
        TEST_ASSERT_TRUE(fan.isKickStarting());
        TEST_ASSERT_EQUAL_UINT8(255, fan.getCurrentDuty());
        applyControlOutputs(fan, damper, false, 100.0f, mode, 30.0f);
        assertStopped();
    }
}

void test_fault_overrides_manual_duty_in_every_mode(void) {
    for (const char* mode : modes) {
        fan.setManualDuty(255);
        damper.setPosition(100.0f);
        applyControlOutputs(fan, damper, false, 100.0f, mode, 30.0f);
        assertStopped();
        // Fault also releases manual mode, so subsequent valid PID can run.
        applyControlOutputs(fan, damper, true, 100.0f, mode, 30.0f);
        fan.update();
        TEST_ASSERT_TRUE(fan.isKickStarting());
        fan.off();
    }
}

void test_outputs_stay_closed_until_control_is_ready(void) {
    for (const char* mode : modes) {
        // A connected probe alone is not readiness; wait for fresh computation.
        applyControlOutputs(fan, damper, false, 100.0f, mode, 30.0f);
        assertStopped();
        applyControlOutputs(fan, damper, false, 100.0f, mode, 30.0f);
        assertStopped();
        applyControlOutputs(fan, damper, true, 100.0f, mode, 30.0f);
        fan.update();
        TEST_ASSERT_EQUAL_UINT8(255, fan.getCurrentDuty());
        TEST_ASSERT_FLOAT_WITHIN(0.001f, 100.0f, damper.getCurrentPositionPct());
        fan.off();
    }
}

void test_valid_fan_only_zero_preserves_normal_damper_behavior(void) {
    applyControlOutputs(fan, damper, true, 0.0f, "fan_only", 30.0f);
    fan.update();
    TEST_ASSERT_EQUAL_UINT8(0, fan.getCurrentDuty());
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 100.0f, damper.getCurrentPositionPct());
}

int main(int argc, char** argv) {
    UNITY_BEGIN();
    RUN_TEST(test_fault_cancels_kickstart_and_closes_every_mode);
    RUN_TEST(test_fault_overrides_manual_duty_in_every_mode);
    RUN_TEST(test_outputs_stay_closed_until_control_is_ready);
    RUN_TEST(test_valid_fan_only_zero_preserves_normal_damper_behavior);
    return UNITY_END();
}
