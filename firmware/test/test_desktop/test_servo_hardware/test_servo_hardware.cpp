#include <unity.h>
#include "Arduino.h"
#undef NATIVE_BUILD
#include "servo_controller.cpp"

void setUp() {
    failSetup=false; calls.clear();
    for (auto& channel:channels) channel={};
    for (auto& channel:pinChannel) channel=-1;
    for (auto& level:pinLevel) level=-1;
}
void tearDown() {}
static double pulseUs() {
    const auto& c=channels[SERVO_PWM_CHANNEL];
    return double(c.duty)*1000000/(c.frequency*(1UL<<c.bits));
}
void test_50hz_precision_and_each_adjustment_reaches_hardware() {
    ServoController servo; servo.begin();
    TEST_ASSERT_EQUAL_UINT32(50,servo.getPwmFrequencyHz());
    TEST_ASSERT_EQUAL_INT(PIN_SERVO,calls.back().pinOrChannel);
    TEST_ASSERT_EQUAL_CHAR('A',calls.back().type);
    TEST_ASSERT_GREATER_THAN_UINT32(0,calls.back().value); // Preloaded before routing the GPIO.
    for (int us=544; us<=2394; us+=10) {
        servo.setPulseWidth(us);
        TEST_ASSERT_FLOAT_WITHIN(0.62f,us,pulseUs());
        const auto before=servo.getPwmDutyTicks();
        servo.setPulseWidth(us+10);
        TEST_ASSERT_GREATER_THAN_UINT32(before,servo.getPwmDutyTicks());
    }
    unsigned setups=0, attaches=0;
    for (auto call:calls) { setups+=call.type=='S'; attaches+=call.type=='A'; }
    TEST_ASSERT_EQUAL_UINT32(1,setups); TEST_ASSERT_EQUAL_UINT32(1,attaches);
}
void test_stop_and_resume_preloads_new_pulse_without_power_cycle() {
    ServoController servo; servo.begin();
    for (int repeat=0; repeat<4; ++repeat) {
        servo.setPulseWidth(1500); calls.clear(); servo.detach();
        TEST_ASSERT_EQUAL_UINT32(0,servo.getPwmDutyTicks());
        TEST_ASSERT_EQUAL_INT(-1,pinChannel[PIN_SERVO]); TEST_ASSERT_EQUAL_INT(LOW,pinLevel[PIN_SERVO]);
        TEST_ASSERT_EQUAL_CHAR('W',calls[0].type); TEST_ASSERT_EQUAL_UINT32(0,calls[0].value);
        TEST_ASSERT_EQUAL_CHAR('D',calls[1].type);
        calls.clear(); servo.setPulseWidth(1550);
        TEST_ASSERT_EQUAL_UINT32(2,calls.size());
        TEST_ASSERT_EQUAL_CHAR('W',calls[0].type); TEST_ASSERT_EQUAL_CHAR('A',calls[1].type);
        TEST_ASSERT_EQUAL_UINT32(calls[0].value,calls[1].value);
        TEST_ASSERT_FLOAT_WITHIN(0.62f,1550,pulseUs());
    }
}
void test_servo_does_not_reconfigure_other_pwm_timers() {
    ledcSetup(FAN_PWM_CHANNEL,100,10); ledcSetup(BUZZER_PWM_CHANNEL,4000,10); ledcSetup(7,21111,9);
    ServoController servo; servo.begin(); servo.setPulseWidth(1500); servo.detach(); servo.setPulseWidth(1000);
    TEST_ASSERT_EQUAL_UINT32(100,channels[FAN_PWM_CHANNEL].frequency);
    TEST_ASSERT_EQUAL_UINT32(4000,channels[BUZZER_PWM_CHANNEL].frequency);
    TEST_ASSERT_EQUAL_UINT32(21111,channels[7].frequency);
    TEST_ASSERT_EQUAL_UINT32(50,channels[SERVO_PWM_CHANNEL].frequency);
    const uint32_t divider=uint64_t(40000000)*256/(50*(1UL<<SERVO_PWM_RESOLUTION));
    TEST_ASSERT_GREATER_OR_EQUAL_UINT32(256,divider); TEST_ASSERT_LESS_OR_EQUAL_UINT32(0x3ffff,divider);
}
void test_setup_failure_holds_signal_low_and_never_attaches() {
    failSetup=true; ServoController servo; servo.begin(); servo.setPulseWidth(1500);
    TEST_ASSERT_EQUAL_INT(LOW,pinLevel[PIN_SERVO]); TEST_ASSERT_EQUAL_INT(-1,pinChannel[PIN_SERVO]);
    for (auto call:calls) { TEST_ASSERT_NOT_EQUAL('A',call.type); TEST_ASSERT_NOT_EQUAL('W',call.type); }
}
int main() {
    UNITY_BEGIN();
    RUN_TEST(test_50hz_precision_and_each_adjustment_reaches_hardware);
    RUN_TEST(test_stop_and_resume_preloads_new_pulse_without_power_cycle);
    RUN_TEST(test_servo_does_not_reconfigure_other_pwm_timers);
    RUN_TEST(test_setup_failure_holds_signal_low_and_never_attaches);
    return UNITY_END();
}
