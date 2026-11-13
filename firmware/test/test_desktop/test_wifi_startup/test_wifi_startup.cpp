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
    LittleFS = FakeFS();
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

void test_manual_reconnect_restores_radio_after_disconnect() {
    WiFi.saved = WiFi.connectOnBegin = true;
    WifiManager manager;
    manager.begin();
    TEST_ASSERT_TRUE(manager.isConnected());
    manager.disconnect();
    TEST_ASSERT_FALSE(manager.isConnected());
    TEST_ASSERT_EQUAL(0, WiFi.currentMode);
    manager.reconnect();
    TEST_ASSERT_EQUAL(WIFI_STA, WiFi.currentMode);
    fakeNow += 10000;
    manager.update();
    TEST_ASSERT_TRUE(manager.isConnected());
    TEST_ASSERT_TRUE(WiFi.saved);
}

void test_disconnect_log_captures_stale_connected_flag_and_last_signal() {
    WiFi.saved = WiFi.connectOnBegin = true;
    WifiManager manager; manager.begin();
    WiFi.signal = -69; manager.getRSSI();
    // Reproduce the library's possible contradiction without changing recovery policy.
    WiFi.statusBits = 0;
    WiFi.emit(ARDUINO_EVENT_WIFI_STA_DISCONNECTED, 2);
    const auto image = manager.eventLogSnapshot();
    const auto& last = WifiEventLog::chronological(image, image.count - 1);
    TEST_ASSERT_EQUAL(WifiEventLog::Disconnected, last.kind);
    TEST_ASSERT_EQUAL(2, last.reason);
    TEST_ASSERT_EQUAL(WL_CONNECTED, last.status);
    TEST_ASSERT_EQUAL_UINT32(0, last.statusBits);
    TEST_ASSERT_EQUAL_INT8(-69, last.rssi);
}

void test_wifi_log_is_bounded_and_survives_reload() {
    WifiEventLog log; log.startBoot({});
    for (unsigned i = 1; i <= 80; ++i) {
        WifiEventLog::Event event; event.kind = WifiEventLog::Disconnected; event.uptimeMs = i;
        log.record(event);
    }
    auto image = log.snapshot();
    TEST_ASSERT_EQUAL_UINT32(32, image.count);
    TEST_ASSERT_EQUAL_UINT32(49, WifiEventLog::chronological(image, 0).uptimeMs);
    TEST_ASSERT_EQUAL_UINT32(80, WifiEventLog::chronological(image, 31).uptimeMs);
    log.persist(LittleFS, 1000);
    TEST_ASSERT_EQUAL_UINT32(1040, LittleFS.files[WifiEventLog::Path]->size());
    TEST_ASSERT_EQUAL_UINT32(1, LittleFS.files.size());
    WifiEventLog restored; TEST_ASSERT_TRUE(restored.load(LittleFS));
    restored.startBoot({}); image = restored.snapshot();
    TEST_ASSERT_EQUAL_UINT32(32, image.count);
    TEST_ASSERT_EQUAL_UINT32(2, WifiEventLog::chronological(image, 31).boot);
    TEST_ASSERT_EQUAL(WifiEventLog::Boot, WifiEventLog::chronological(image, 31).kind);
    TEST_ASSERT_EQUAL_UINT32(80, WifiEventLog::chronological(image, 30).uptimeMs);
}

void test_wifi_log_throttles_event_bursts_and_does_not_write_while_idle() {
    WifiEventLog log; log.startBoot({}); log.persist(LittleFS, 1000);
    for (unsigned i = 1; i <= 1000; ++i) {
        log.record({}); log.persist(LittleFS, 1000 + i);
    }
    TEST_ASSERT_EQUAL_UINT32(1, LittleFS.writeCount);
    log.persist(LittleFS, 61000);
    TEST_ASSERT_EQUAL_UINT32(2, LittleFS.writeCount);
    TEST_ASSERT_FALSE(log.pending());
    log.persist(LittleFS, 121000);
    TEST_ASSERT_EQUAL_UINT32(2, LittleFS.writeCount);
}

void test_wifi_log_failed_writes_keep_previous_snapshot_and_retry_later() {
    for (bool renameFailure : {false, true}) {
        LittleFS = FakeFS();
        WifiEventLog log; log.startBoot({}); log.persist(LittleFS, 1000);
        log.record({});
        LittleFS.failWrite = !renameFailure; LittleFS.failRename = renameFailure;
        log.persist(LittleFS, 61000);
        TEST_ASSERT_FALSE(log.lastSaveOK()); TEST_ASSERT_TRUE(log.pending());
        TEST_ASSERT_EQUAL_UINT32(1, LittleFS.files.size());
        WifiEventLog previous; TEST_ASSERT_TRUE(previous.load(LittleFS));
        TEST_ASSERT_EQUAL_UINT32(1, previous.snapshot().count);
        log.persist(LittleFS, 61001);
        TEST_ASSERT_EQUAL_UINT32(2, LittleFS.writeCount);
        LittleFS.failWrite = LittleFS.failRename = false;
        log.persist(LittleFS, 121000);
        TEST_ASSERT_TRUE(log.lastSaveOK()); TEST_ASSERT_FALSE(log.pending());
        WifiEventLog recovered; TEST_ASSERT_TRUE(recovered.load(LittleFS));
        TEST_ASSERT_EQUAL_UINT32(2, recovered.snapshot().count);
    }
}

void test_wifi_log_does_not_lose_event_arriving_during_save() {
    WifiEventLog log; log.startBoot({});
    LittleFS.onWrite = [&log]() { log.record({}); };
    log.persist(LittleFS, 1000);
    TEST_ASSERT_TRUE(log.pending());
    LittleFS.onWrite = {};
    log.persist(LittleFS, 61000);
    TEST_ASSERT_FALSE(log.pending());
    WifiEventLog recovered; TEST_ASSERT_TRUE(recovered.load(LittleFS));
    TEST_ASSERT_EQUAL_UINT32(2, recovered.snapshot().count);
}

void test_wifi_log_rejects_bad_files_and_handles_clock_wrap() {
    auto file = LittleFS.open(WifiEventLog::Path, "w");
    WifiEventLog::Image invalid; invalid.count = WifiEventLog::Capacity + 1;
    file.write(reinterpret_cast<const uint8_t*>(&invalid), sizeof(invalid));
    WifiEventLog log; TEST_ASSERT_FALSE(log.load(LittleFS));
    TEST_ASSERT_EQUAL_UINT32(0, log.snapshot().count);
    LittleFS = FakeFS();
    log.startBoot({}); const uint32_t start = UINT32_MAX - 30000;
    log.persist(LittleFS, start); log.record({});
    log.persist(LittleFS, start + WifiEventLog::SaveIntervalMs - 1);
    TEST_ASSERT_EQUAL_UINT32(1, LittleFS.writeCount);
    log.persist(LittleFS, start + WifiEventLog::SaveIntervalMs);
    TEST_ASSERT_EQUAL_UINT32(2, LittleFS.writeCount);
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_first_boot_opens_portal_without_empty_ssid_attempts);
    RUN_TEST(test_successful_provisioning_does_not_close_destroyed_portal);
    RUN_TEST(test_connection_closes_portal_only_if_still_active);
    RUN_TEST(test_time_sync_on_saved_explicit_and_reconnected_networks);
    RUN_TEST(test_manual_reconnect_restores_radio_after_disconnect);
    RUN_TEST(test_disconnect_log_captures_stale_connected_flag_and_last_signal);
    RUN_TEST(test_wifi_log_is_bounded_and_survives_reload);
    RUN_TEST(test_wifi_log_throttles_event_bursts_and_does_not_write_while_idle);
    RUN_TEST(test_wifi_log_failed_writes_keep_previous_snapshot_and_retry_later);
    RUN_TEST(test_wifi_log_does_not_lose_event_arriving_during_save);
    RUN_TEST(test_wifi_log_rejects_bad_files_and_handles_clock_wrap);
    return UNITY_END();
}
