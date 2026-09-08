#pragma once
#include "Arduino.h"
constexpr int WIFI_STA = 1;
constexpr int WL_CONNECTED = 3;
struct FakeAddress {
    String toString() const { return "192.168.4.1"; }
};
struct FakeWiFi {
    bool saved = false;
    bool connected = false;
    unsigned beginCount = 0;
    void setHostname(const char*) {}
    void mode(int) {}
    void begin() { ++beginCount; }
    void begin(const char*, const char*) { ++beginCount; }
    int status() const { return connected ? WL_CONNECTED : 0; }
    void disconnect(bool = false) { connected = false; }
    void reconnect() {}
    FakeAddress localIP() const { return {}; }
    FakeAddress softAPIP() const { return {}; }
    String SSID() const { return "test-network"; }
    int RSSI() const { return -40; }
};
static FakeWiFi WiFi;
