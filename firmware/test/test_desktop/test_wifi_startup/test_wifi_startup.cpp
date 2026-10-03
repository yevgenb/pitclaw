#include <unity.h>
#undef NATIVE_BUILD
#include "wifi_manager.cpp"

static bool listenerReleased;
static bool callbackBeforePortal;
static void releaseListener() {
    listenerReleased = true;
    callbackBeforePortal = !portalActive;
}

void setUp() {
    fakeNow = 0;
    timeSyncStarts = 0;
    WiFi = FakeWiFi();
    portalActive = provisionOnProcess = false;
    autoClosePortal = true;
    portalStarts = portalStops = duplicateStops = 0;
    listenerReleased = callbackBeforePortal = false;
}
void tearDown() {}

void test_first_boot_opens_portal_without_empty_ssid_attempts() {
    WifiManager manager;
    manager.onPortalStart(releaseListener);
    manager.begin();
    TEST_ASSERT_EQUAL_UINT32(0, WiFi.beginCount);
    TEST_ASSERT_EQUAL_UINT32(1, portalStarts);
    TEST_ASSERT_TRUE(manager.isAPMode());
    TEST_ASSERT_TRUE(listenerReleased);
    TEST_ASSERT_TRUE(callbackBeforePortal);
    TEST_ASSERT_LESS_THAN_UINT32(1000, fakeNow);
    TEST_ASSERT_EQUAL_UINT32(0, timeSyncStarts);
}

void test_successful_provisioning_does_not_close_destroyed_portal() {
    WifiManager manager;
    manager.begin();
    provisionOnProcess = true;
    manager.update();
    TEST_ASSERT_TRUE(manager.isConnected());
    TEST_ASSERT_FALSE(manager.isAPMode());
    TEST_ASSERT_EQUAL_UINT32(0, portalStops);
    TEST_ASSERT_EQUAL_UINT32(0, duplicateStops);
    TEST_ASSERT_EQUAL_UINT32(1, timeSyncStarts);
    TEST_ASSERT_EQUAL(0, timeGmtOffset);
    TEST_ASSERT_EQUAL(0, timeDstOffset);
}

void test_time_sync_on_saved_explicit_and_reconnected_networks() {
    for (bool explicitCredentials : {false, true}) {
        setUp();
        WiFi.saved = WiFi.connectOnBegin = true;
        WifiManager manager;
        manager.begin(explicitCredentials ? "test" : nullptr);
        TEST_ASSERT_EQUAL_UINT32(1, timeSyncStarts);
        fakeNow += 10000;
        manager.update();
        TEST_ASSERT_EQUAL_UINT32(1, timeSyncStarts); // No restart on every poll.
        WiFi.connected = false; fakeNow += 10000; manager.update();
        WiFi.connected = true; fakeNow += 10000; manager.update();
        TEST_ASSERT_EQUAL_UINT32(2, timeSyncStarts);
    }
}

void test_connection_closes_portal_only_if_still_active() {
    WifiManager manager;
    manager.begin();
    autoClosePortal = false;
    provisionOnProcess = true;
    manager.update();
    manager.update();
    TEST_ASSERT_TRUE(manager.isConnected());
    TEST_ASSERT_FALSE(manager.isAPMode());
    TEST_ASSERT_EQUAL_UINT32(1, portalStops);
    TEST_ASSERT_EQUAL_UINT32(0, duplicateStops);
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_first_boot_opens_portal_without_empty_ssid_attempts);
    RUN_TEST(test_successful_provisioning_does_not_close_destroyed_portal);
    RUN_TEST(test_connection_closes_portal_only_if_still_active);
    RUN_TEST(test_time_sync_on_saved_explicit_and_reconnected_networks);
    return UNITY_END();
}
