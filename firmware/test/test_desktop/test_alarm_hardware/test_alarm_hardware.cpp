#include <unity.h>
#undef NATIVE_BUILD
#include "alarm_manager.cpp"
#include "lid_detector.h"

void setUp() { fakeNow = 0; buzzerSounding = false; toneCalls = 0; }
void tearDown() {}

void test_automatic_lid_pause_does_not_start_low_alarm_or_buzzer() {
    AlarmManager alarm;
    alarm.begin();
    LidDetector lid;
    lid.update(250, 250, 0);
    lid.update(250, 250, LID_OPEN_ARM_MS);
    fakeNow = LID_OPEN_ARM_MS + 4000;
    lid.update(200, 250, fakeNow);
    TEST_ASSERT_TRUE(lid.isOpen());
    for (unsigned i = 0; i < 10; ++i) {
        fakeNow += 1000;
        alarm.update(200, 0, 0, 250, true, lid.isOpen());
        TEST_ASSERT_FALSE(alarm.isAlarming());
        TEST_ASSERT_FALSE(buzzerSounding);
    }
    TEST_ASSERT_EQUAL_UINT32(0, toneCalls);
    fakeNow += LID_OPEN_TIMEOUT_MS;
    lid.update(200, 250, fakeNow);
    TEST_ASSERT_FALSE(lid.isOpen());
    alarm.update(200, 0, 0, 250, true, lid.isOpen());
    TEST_ASSERT_TRUE(alarm.isAlarming());
    TEST_ASSERT_TRUE(buzzerSounding);
}

void test_manual_lid_pause_silences_existing_low_alarm_immediately() {
    AlarmManager alarm;
    alarm.begin();
    fakeNow = ALARM_BUZZER_PAUSE;
    alarm.update(200, 0, 0, 250, true);
    TEST_ASSERT_TRUE(buzzerSounding);
    LidDetector lid;
    lid.setEnabled(false); // Manual opening also works with auto detection off.
    lid.openManual(++fakeNow);
    alarm.update(200, 0, 0, 250, true, lid.isOpen());
    TEST_ASSERT_FALSE(buzzerSounding); // No wait for the current tone to finish.
    TEST_ASSERT_FALSE(alarm.isAlarming());
    AlarmType active[MAX_ACTIVE_ALARMS];
    TEST_ASSERT_EQUAL_UINT8(0, alarm.getActiveAlarms(active, MAX_ACTIVE_ALARMS));
    lid.resume();
    fakeNow += ALARM_BUZZER_PAUSE;
    alarm.update(200, 0, 0, 250, true, lid.isOpen());
    TEST_ASSERT_TRUE(buzzerSounding);
}

void test_lid_pause_keeps_independent_meat_and_high_temperature_alarms() {
    AlarmManager alarm;
    alarm.setMeat1Target(165);
    fakeNow = ALARM_BUZZER_PAUSE;
    alarm.update(200, 170, 0, 250, true, true);
    TEST_ASSERT_TRUE(buzzerSounding);
    AlarmType active[MAX_ACTIVE_ALARMS];
    TEST_ASSERT_EQUAL_UINT8(1, alarm.getActiveAlarms(active, MAX_ACTIVE_ALARMS));
    TEST_ASSERT_EQUAL(AlarmType::MEAT1_DONE, active[0]);
    alarm.acknowledge();
    fakeNow += ALARM_BUZZER_PAUSE;
    alarm.update(300, 170, 0, 250, true, true);
    TEST_ASSERT_TRUE(buzzerSounding);
    TEST_ASSERT_EQUAL_UINT8(1, alarm.getActiveAlarms(active, MAX_ACTIVE_ALARMS));
    TEST_ASSERT_EQUAL(AlarmType::PIT_HIGH, active[0]);
}

void test_lid_warning_needs_no_acknowledgment_and_rearms_low_alarm() {
    AlarmManager alarm;
    fakeNow = ALARM_BUZZER_PAUSE;
    alarm.update(200, 0, 0, 250, true);
    alarm.acknowledge();
    alarm.update(200, 0, 0, 250, true, true);
    TEST_ASSERT_FALSE(buzzerSounding);
    fakeNow += ALARM_BUZZER_PAUSE;
    alarm.update(200, 0, 0, 250, true, false);
    TEST_ASSERT_TRUE(buzzerSounding);
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_automatic_lid_pause_does_not_start_low_alarm_or_buzzer);
    RUN_TEST(test_manual_lid_pause_silences_existing_low_alarm_immediately);
    RUN_TEST(test_lid_pause_keeps_independent_meat_and_high_temperature_alarms);
    RUN_TEST(test_lid_warning_needs_no_acknowledgment_and_rearms_low_alarm);
    return UNITY_END();
}
