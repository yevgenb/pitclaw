#pragma once
#include "../units.h"

// UI input values and action callbacks use Fahrenheit. Only presentation and
// editor increments use the selected unit, so changing units cannot change a cook.
struct UiState {
    bool fahrenheit = true;
    float temps[3] = {};
    bool connected[3] = {};
    float setpoint = 225;
    float targets[2] = {};
};
extern UiState ui_state;

inline float ui_display_temp(float f) {
    return ui_state.fahrenheit ? f : fahrenheitToCelsius(f);
}
inline const char* ui_unit_suffix() { return ui_state.fahrenheit ? "F" : "C"; }

void ui_refresh_editors();
void ui_refresh_temperature_layout();
void ui_refresh_alert_layout();
void ui_layout_alert(bool active);
void ui_graph_refresh_layout();
