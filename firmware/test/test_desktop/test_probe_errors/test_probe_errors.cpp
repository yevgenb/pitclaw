#include <unity.h>
#include "error_manager.h"
#include "error_manager.cpp"

static ErrorManager errors;
static ProbeState probes[3];
void setUp() {
    errors = ErrorManager();
    probes[0] = {true,false,false,250};
    probes[1] = probes[2] = {false,true,false,0};
}
void tearDown() {}
static void update() { errors.update(250,0,probes); }
void optional_meat_probes_are_not_errors() {
    update(); TEST_ASSERT_EQUAL_UINT8(0,errors.getErrorCount());
    probes[1]={true,false,false,160}; update();
    probes[1]={false,true,false,0}; update();
    TEST_ASSERT_EQUAL_UINT8(0,errors.getErrorCount());
}
void missing_pit_is_still_an_error() {
    probes[0]={false,true,false,0}; update();
    TEST_ASSERT_EQUAL_UINT8(1,errors.getErrorCount());
    TEST_ASSERT_TRUE(errors.hasError(ErrorCode::PROBE_OPEN));
}
void meat_shorts_are_faults_and_unplugging_clears_them() {
    probes[1]=probes[2]={false,false,true,0}; update();
    TEST_ASSERT_EQUAL_UINT8(2,errors.getErrorCount());
    TEST_ASSERT_TRUE(errors.hasError(ErrorCode::PROBE_SHORT));
    probes[1]=probes[2]={false,true,false,0}; update();
    TEST_ASSERT_EQUAL_UINT8(0,errors.getErrorCount());
}
void pit_short_stays_visible() {
    probes[0]={false,false,true,0}; update();
    TEST_ASSERT_EQUAL_UINT8(1,errors.getErrorCount());
    TEST_ASSERT_TRUE(errors.hasError(ErrorCode::PROBE_SHORT));
}
void ui_and_error_list_share_policy() {
    for(uint8_t i=0;i<3;++i) {
        TEST_ASSERT_EQUAL(i==0,ErrorManager::probeHasFault(i,true,false));
        TEST_ASSERT_TRUE(ErrorManager::probeHasFault(i,false,true));
        TEST_ASSERT_FALSE(ErrorManager::probeHasFault(i,false,false));
    }
}
int main() {
    UNITY_BEGIN();
    RUN_TEST(optional_meat_probes_are_not_errors); RUN_TEST(missing_pit_is_still_an_error);
    RUN_TEST(meat_shorts_are_faults_and_unplugging_clears_them); RUN_TEST(pit_short_stays_visible);
    RUN_TEST(ui_and_error_list_share_policy);
    return UNITY_END();
}
