#pragma once
#include "WiFi.h"
static bool portalActive;
static bool provisionOnProcess;
static bool autoClosePortal;
static unsigned portalStarts, portalStops, duplicateStops;
class WiFiManager {
public:
    void setConfigPortalTimeout(unsigned) {}
    void setConnectTimeout(unsigned) {}
    void setDebugOutput(bool) {}
    void setConfigPortalBlocking(bool) {}
    bool getWiFiIsSaved() const { return WiFi.saved; }
    bool getConfigPortalActive() const { return portalActive; }
    void startConfigPortal(const char*, const char*) {
        portalActive = true;
        ++portalStarts;
    }
    void process() {
        if (provisionOnProcess) {
            WiFi.connected = true;
            WiFi.saved = true;
            if (autoClosePortal) portalActive = false;
        }
    }
    void stopConfigPortal() {
        ++portalStops;
        if (!portalActive) ++duplicateStops;
        portalActive = false;
    }
};
