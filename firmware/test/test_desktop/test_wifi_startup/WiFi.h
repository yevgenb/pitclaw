#pragma once
#include "Arduino.h"
#include <cstdio>
#include <functional>
constexpr int WIFI_STA = 1;
constexpr int WL_CONNECTED = 3;
struct FakeAddress {
    uint8_t bytes[4] = {192,168,4,1};
    uint8_t operator[](unsigned i) const { return bytes[i]; }
    String toString() const { char text[16]; snprintf(text,sizeof(text),"%u.%u.%u.%u",bytes[0],bytes[1],bytes[2],bytes[3]); return text; }
};
enum WiFiEvent_t { ARDUINO_EVENT_WIFI_STA_START, ARDUINO_EVENT_WIFI_STA_STOP,
    ARDUINO_EVENT_WIFI_STA_CONNECTED, ARDUINO_EVENT_WIFI_STA_DISCONNECTED,
    ARDUINO_EVENT_WIFI_STA_GOT_IP, ARDUINO_EVENT_WIFI_STA_LOST_IP,
    ARDUINO_EVENT_WIFI_STA_AUTHMODE_CHANGE };
struct WiFiEventInfo_t { struct { uint8_t reason = 0; } wifi_sta_disconnected; };
struct FakeWiFi {
    bool saved = false;
    bool connected = false;
    bool connectOnBegin = false;
    unsigned beginCount = 0;
    int currentMode = 0;
    unsigned statusBits = 0;
    int8_t signal = -40;
    std::function<void(WiFiEvent_t, WiFiEventInfo_t)> callback;
    void onEvent(std::function<void(WiFiEvent_t, WiFiEventInfo_t)> handler) { callback = handler; }
    void emit(WiFiEvent_t event, uint8_t reason = 0) {
        WiFiEventInfo_t info; info.wifi_sta_disconnected.reason = reason;
        if (callback) callback(event, info);
    }
    unsigned getStatusBits() const { return statusBits; }
    void setHostname(const char*) {}
    void mode(int mode) { if (currentMode != mode) { currentMode = mode; emit(ARDUINO_EVENT_WIFI_STA_START); } }
    void begin() { ++beginCount; connected = connectOnBegin; statusBits = connected ? 48 : 0;
        if (connected) { emit(ARDUINO_EVENT_WIFI_STA_CONNECTED); emit(ARDUINO_EVENT_WIFI_STA_GOT_IP); } }
    void begin(const char*, const char*) { begin(); }
    int status() const { return connected ? WL_CONNECTED : 0; }
    void disconnect(bool radioOff = false) { const bool wasConnected = connected; connected = false; statusBits = 0;
        if (wasConnected) emit(ARDUINO_EVENT_WIFI_STA_DISCONNECTED,8);
        if (radioOff) { currentMode = 0; emit(ARDUINO_EVENT_WIFI_STA_STOP); } }
    void reconnect() { if (currentMode & WIFI_STA) begin(); }
    FakeAddress localIP() const { return {}; }
    FakeAddress softAPIP() const { return {}; }
    FakeAddress gatewayIP() const { return {}; }
    String SSID() const { return "test-network"; }
    int RSSI() const { return connected ? signal : 0; }
};
static FakeWiFi WiFi;
