#include <unity.h>
#include "Arduino.h"
#undef NATIVE_BUILD
#include "servo_controller.cpp"

void setUp() {
    failSetup=false; attachReadsPreviousDuty=false; calls.clear();
    for (auto& channel:channels) channel={};
    for (auto& channel:pinChannel) channel=-1;
    for (auto& level:pinLevel) level=-1;
    for (auto& input:inputEnabled) input=false;
}
void tearDown() {}
static double pulseUs() {
    const auto& c=channels[SERVO_PWM_CHANNEL];
    return double(c.duty)*1000000/(c.frequency*(1UL<<c.bits));
}
void test_50hz_precision_and_each_adjustment_reaches_hardware() {
    ServoController servo; servo.begin();
    TEST_ASSERT_EQUAL_UINT32(50,servo.getPwmFrequencyHz());
    TEST_ASSERT_EQUAL_INT(PIN_SERVO,calls[calls.size()-2].pinOrChannel);
    TEST_ASSERT_EQUAL_CHAR('A',calls[calls.size()-2].type);
    TEST_ASSERT_GREATER_THAN_UINT32(0,calls[calls.size()-2].value);
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
    attachReadsPreviousDuty=true; // A 50 Hz duty update need not latch before attach reads it.
    ServoController servo; servo.begin();
    TEST_ASSERT_FLOAT_WITHIN(0.62f,544,pulseUs());
    for (int repeat=0; repeat<4; ++repeat) {
        servo.setPulseWidth(1500); calls.clear(); servo.detach();
        TEST_ASSERT_EQUAL_UINT32(0,servo.getPwmDutyTicks());
        TEST_ASSERT_EQUAL_INT(-1,pinChannel[PIN_SERVO]); TEST_ASSERT_EQUAL_INT(LOW,pinLevel[PIN_SERVO]);
        TEST_ASSERT_EQUAL_CHAR('W',calls[0].type); TEST_ASSERT_EQUAL_UINT32(0,calls[0].value);
        TEST_ASSERT_EQUAL_CHAR('D',calls[1].type);
        calls.clear(); servo.setPulseWidth(1550);
        TEST_ASSERT_EQUAL_UINT32(3,calls.size());
        TEST_ASSERT_EQUAL_CHAR('W',calls[0].type); TEST_ASSERT_EQUAL_CHAR('A',calls[1].type);
        TEST_ASSERT_EQUAL_UINT32(calls[0].value,calls[1].value);
        TEST_ASSERT_EQUAL_CHAR('W',calls[2].type);
        TEST_ASSERT_EQUAL_UINT32(calls[0].value,calls[2].value);
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
void test_pin_sampling_is_bounded_and_does_not_reconfigure_output() {
    ServoController servo; servo.begin(); servo.setPulseWidth(1500); calls.clear();
    const auto sample=servo.sampleSignal();
    TEST_ASSERT_UINT32_WITHIN(2,1500,sample.highUs);
    TEST_ASSERT_EQUAL_UINT32(20000,sample.highUs+sample.lowUs);
    TEST_ASSERT_EQUAL_UINT32(3,calls.size());
    TEST_ASSERT_EQUAL_CHAR('I',calls[0].type);
    TEST_ASSERT_EQUAL_CHAR('R',calls[1].type); TEST_ASSERT_EQUAL_UINT32(50000,calls[1].value);
    TEST_ASSERT_EQUAL_CHAR('R',calls[2].type); TEST_ASSERT_EQUAL_UINT32(50000,calls[2].value);
    TEST_ASSERT_EQUAL_UINT16(1500,servo.getCurrentPulseUs());
    pinChannel[PIN_SERVO]=-1; // Lost GPIO routing: timer registers alone still look healthy.
    TEST_ASSERT_EQUAL_UINT32(50,servo.getPwmFrequencyHz());
    TEST_ASSERT_EQUAL_UINT32(0,servo.sampleSignal().highUs);
}
int main() {
    UNITY_BEGIN();
    RUN_TEST(test_50hz_precision_and_each_adjustment_reaches_hardware);
    RUN_TEST(test_stop_and_resume_preloads_new_pulse_without_power_cycle);
    RUN_TEST(test_servo_does_not_reconfigure_other_pwm_timers);
    RUN_TEST(test_setup_failure_holds_signal_low_and_never_attaches);
    RUN_TEST(test_pin_sampling_is_bounded_and_does_not_reconfigure_output);
    return UNITY_END();
}
