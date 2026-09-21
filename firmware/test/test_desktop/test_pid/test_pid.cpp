// Real controller state machine with an injected clock. QuickPID numerical output
// is compiled out here; firmware and integration builds cover that dependency.
#include <unity.h>
#include <cmath>
#include <initializer_list>
#include <stdint.h>
#include "pid_controller.h"
#include "pid_controller.cpp"

static PidController* pid;
void setUp() { pid = new PidController(); pid->begin(); }
void tearDown() { delete pid; }
static void arm(uint32_t start = 0, float target = 250) {
    pid->compute(target, target, start);
    pid->compute(target, target, start + LID_OPEN_ARM_MS);
}
static void pause() {
    arm(); pid->compute(230,250,32000); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void defaults() {
    TEST_ASSERT_TRUE(pid->isEnabled()); TEST_ASSERT_TRUE(pid->isLidDetectionEnabled());
    TEST_ASSERT_FALSE(pid->isLidOpen()); TEST_ASSERT_EQUAL_FLOAT(0,pid->getOutput());
    TEST_ASSERT_EQUAL_FLOAT(PID_KP,pid->getKp());
    TEST_ASSERT_EQUAL_FLOAT(PID_KI,pid->getKi()); TEST_ASSERT_EQUAL_FLOAT(PID_KD,pid->getKd());
}
void tuning() {
    pid->setTunings(8,.1f,3); TEST_ASSERT_EQUAL_FLOAT(8,pid->getKp());
    TEST_ASSERT_EQUAL_FLOAT(.1f,pid->getKi()); TEST_ASSERT_EQUAL_FLOAT(3,pid->getKd());
    pid->begin(1,2,3); TEST_ASSERT_EQUAL_FLOAT(1,pid->getKp());
}
void cold_start_never_pauses() {
    for(uint32_t t=0;t<600000;t+=4000) pid->compute(70+t/10000.0f,250,t);
    TEST_ASSERT_FALSE(pid->isLidOpen());
}
void warm_up_must_be_continuous() {
    pid->compute(250,250,0); pid->compute(250,250,29000);
    pid->compute(240,250,30000); // Interrupt settling.
    pid->compute(250,250,31000); pid->compute(250,250,60000);
    pid->compute(230,250,61000); TEST_ASSERT_FALSE(pid->isLidOpen());
    arm(62000); pid->compute(230,250,94000); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void overshoot_does_not_count_as_settled() {
    pid->compute(270,250,0); pid->compute(270,250,60000);
    pid->compute(230,250,64000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void thresholds_and_recovery() {
    arm(); pid->compute(235,250,31000); TEST_ASSERT_FALSE(pid->isLidOpen());
    TEST_ASSERT_EQUAL_FLOAT(0,pid->compute(234.9f,250,32000)); TEST_ASSERT_TRUE(pid->isLidOpen());
    pid->compute(240,250,36000); TEST_ASSERT_TRUE(pid->isLidOpen());
    pid->compute(245,250,40000); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->compute(230,250,44000); TEST_ASSERT_FALSE(pid->isLidOpen()); // Requires settling again.
    arm(48000); pid->compute(230,250,80000); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void target_change_clears_and_disarms() {
    arm(); pid->compute(250,350,32000); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->compute(250,350,100000); TEST_ASSERT_FALSE(pid->isLidOpen());
    arm(104000,350); pid->compute(320,350,136000); TEST_ASSERT_TRUE(pid->isLidOpen());
    pid->compute(320,400,140000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void timeout_resumes_without_retriggering() {
    pause();
    TEST_ASSERT_EQUAL_UINT16(120,pid->lidRemainingSeconds(32000));
    pid->compute(200,250,151999); TEST_ASSERT_TRUE(pid->isLidOpen());
    TEST_ASSERT_EQUAL_UINT16(1,pid->lidRemainingSeconds(151999));
    pid->compute(200,250,152000); TEST_ASSERT_FALSE(pid->isLidOpen());
    TEST_ASSERT_EQUAL_UINT16(0,pid->lidRemainingSeconds(152000));
    pid->compute(200,250,156000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void resume_now_requires_fresh_settling() {
    pause(); pid->resumeLid(); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->compute(200,250,36000); pid->compute(200,250,600000);
    TEST_ASSERT_FALSE(pid->isLidOpen());
    arm(604000); pid->compute(230,250,636000); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void disable_and_reenable() {
    pause(); pid->setLidDetectionEnabled(false);
    TEST_ASSERT_FALSE(pid->isLidOpen()); TEST_ASSERT_FALSE(pid->isLidDetectionEnabled());
    arm(36000); pid->compute(200,250,68000); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->setLidDetectionEnabled(true); pid->compute(200,250,72000); TEST_ASSERT_FALSE(pid->isLidOpen());
    arm(76000); pid->compute(230,250,108000); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void duplicate_enable_does_not_interrupt_a_pause() {
    pause(); pid->setLidDetectionEnabled(true); TEST_ASSERT_TRUE(pid->isLidOpen());
}
void invalid_measurement_or_target_clears_pause() {
    for(float bad : {NAN,INFINITY,-INFINITY}) {
        pid->begin(); pause(); pid->compute(bad,250,36000); TEST_ASSERT_FALSE(pid->isLidOpen());
        pid->compute(230,250,40000); TEST_ASSERT_FALSE(pid->isLidOpen());
        arm(44000); pid->compute(230,250,76000); TEST_ASSERT_TRUE(pid->isLidOpen());
        pid->compute(230,bad,80000); TEST_ASSERT_FALSE(pid->isLidOpen());
    }
    pid->begin(); pause(); pid->compute(200,0,36000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void fault_reset_disarms() {
    pause(); pid->resetLidDetection(); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->compute(230,250,36000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void disabling_pid_clears_pause_and_output() {
    pause(); pid->setEnabled(false); TEST_ASSERT_FALSE(pid->isLidOpen());
    TEST_ASSERT_EQUAL_FLOAT(0,pid->compute(250,250,36000));
    pid->setEnabled(true); pid->compute(230,250,40000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void begin_clears_transient_state() {
    pause(); pid->begin(); TEST_ASSERT_FALSE(pid->isLidOpen());
    pid->compute(230,250,36000); TEST_ASSERT_FALSE(pid->isLidOpen());
}
void timer_wraparound() {
    uint32_t start=UINT32_MAX-40000;
    arm(start); uint32_t opened=start+32000;
    pid->compute(230,250,opened); TEST_ASSERT_TRUE(pid->isLidOpen());
    pid->compute(230,250,opened+LID_OPEN_TIMEOUT_MS-1); TEST_ASSERT_TRUE(pid->isLidOpen());
    pid->compute(230,250,opened+LID_OPEN_TIMEOUT_MS); TEST_ASSERT_FALSE(pid->isLidOpen());
}
int main() {
    UNITY_BEGIN();
    RUN_TEST(defaults); RUN_TEST(tuning); RUN_TEST(cold_start_never_pauses);
    RUN_TEST(warm_up_must_be_continuous); RUN_TEST(overshoot_does_not_count_as_settled);
    RUN_TEST(thresholds_and_recovery); RUN_TEST(target_change_clears_and_disarms);
    RUN_TEST(timeout_resumes_without_retriggering); RUN_TEST(resume_now_requires_fresh_settling);
    RUN_TEST(disable_and_reenable); RUN_TEST(duplicate_enable_does_not_interrupt_a_pause);
    RUN_TEST(invalid_measurement_or_target_clears_pause); RUN_TEST(fault_reset_disarms);
    RUN_TEST(disabling_pid_clears_pause_and_output); RUN_TEST(begin_clears_transient_state);
    RUN_TEST(timer_wraparound);
    return UNITY_END();
}
