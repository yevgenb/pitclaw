#pragma once
#include "../damper_setup.h"
using UiDamperCommandCb = bool (*)(DamperSetupAction action, int value);
using UiDamperStatusCb = DamperSetupState (*)();
void ui_damper_setup_set_callbacks(UiDamperCommandCb command, UiDamperStatusCb status);
bool ui_damper_setup_available();
void ui_damper_setup_init();
void ui_damper_setup_show();
