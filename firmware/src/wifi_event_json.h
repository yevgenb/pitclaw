#pragma once
#include "wifi_event_log.h"
#include <ArduinoJson.h>
#include <cstdio>

inline void wifiEventLogToJson(JsonDocument& doc, const WifiEventLog::Image& image,
                              bool pending, bool saved, bool storageAvailable) {
    doc["schema"] = 1;
    doc["capacity"] = WifiEventLog::Capacity;
    doc["recordBytes"] = sizeof(WifiEventLog::Event);
    doc["snapshotBytes"] = sizeof(WifiEventLog::Image);
    doc["minSaveIntervalSeconds"] = WifiEventLog::SaveIntervalMs / 1000;
    doc["pendingSave"] = pending;
    doc["lastSaveOK"] = saved;
    doc["storageAvailable"] = storageAvailable;
    auto events = doc["events"].to<JsonArray>();
    for (unsigned i = 0; i < image.count; ++i) {
        const auto& event = WifiEventLog::chronological(image, i);
        auto row = events.add<JsonObject>();
        row["event"] = WifiEventLog::name(event.kind);
        row["boot"] = event.boot;
        row["timestamp"] = event.timestamp; // UTC epoch; zero before the clock is synchronized.
        row["uptimeMs"] = event.uptimeMs;
        row["status"] = event.status;
        row["statusBits"] = event.statusBits;
        if (event.rssi) row["rssiDbm"] = event.rssi;
        else row["rssiDbm"] = nullptr;
        row["freeHeap"] = event.freeHeap;
        if (event.kind == WifiEventLog::Disconnected) row["disconnectReason"] = event.reason;
        if (event.kind == WifiEventLog::Boot) row["resetReason"] = event.reason;
        char ip[16], gateway[16];
        snprintf(ip, sizeof(ip), "%u.%u.%u.%u", event.ip[0], event.ip[1], event.ip[2], event.ip[3]);
        snprintf(gateway, sizeof(gateway), "%u.%u.%u.%u", event.gateway[0], event.gateway[1], event.gateway[2], event.gateway[3]);
        row["ip"] = ip;
        row["gateway"] = gateway;
    }
}
