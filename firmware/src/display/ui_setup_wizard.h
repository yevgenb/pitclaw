#pragma once

#include "../config.h"
#include "ui_update.h"
#include <stdint.h>

// Callback types for hardware test actions during setup wizard
typedef void (*WizardFanTestCb)();       // Spin fan briefly
typedef void (*WizardServoTestCb)();     // Sweep servo
typedef void (*WizardBuzzerTestCb)();    // Beep buzzer
typedef void (*WizardUnitsCb)(bool isFahrenheit);  // Save units preference
typedef void (*WizardCompleteCb)();      // Setup complete — save config and go to dashboard

// Initialize and show the setup wizard screens.
// Call this instead of loading the dashboard when configManager.isSetupComplete() == false.
void ui_wizard_init();

// Check if the wizard is still active (user hasn't finished all steps yet).
bool ui_wizard_is_active();

// Keep setup instructions and QR code in sync with the actual Wi-Fi state.
void ui_wizard_update_wifi(const WifiInfo& info);

// Set callbacks for wizard hardware test actions
void ui_wizard_set_callbacks(WizardFanTestCb fanCb,
                              WizardServoTestCb servoCb,
                              WizardBuzzerTestCb buzzerCb,
                              WizardUnitsCb unitsCb,
                              WizardCompleteCb completeCb);

// Update live probe readings on the probe check screen.
// Call from the main loop while wizard is active.
void ui_wizard_update_probes(float pit, float meat1, float meat2,
                              bool pitConn, bool meat1Conn, bool meat2Conn);
