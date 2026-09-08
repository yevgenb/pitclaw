#include "ui_update.h"
#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)
#include "ui_styles.h"
#include "ui_state.h"
#include "graph_history.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <math.h>

extern lv_obj_t *lbl_wifi_icon, *lbl_elapsed, *lbl_units;
extern lv_obj_t *lbl_pit_temp, *lbl_setpoint;
extern lv_obj_t *lbl_meat1_temp, *lbl_meat2_temp, *lbl_meat1_target, *lbl_meat2_target, *lbl_meat1_est, *lbl_meat2_est;
extern lv_obj_t *meat_edit_icons[2];
extern lv_obj_t *bar_fan, *bar_damper, *lbl_fan_bar, *lbl_damper_bar;
extern lv_obj_t *alert_banner, *lbl_alert_text, *btn_alert_ack;
extern lv_obj_t *chart_temps, *lbl_graph_title, *lbl_graph_span;
extern lv_chart_series_t *ser_pit, *ser_meat1, *ser_meat2, *ser_setpoint;
extern lv_obj_t *graph_y_labels[5], *graph_x_labels[3];
extern lv_obj_t *btn_units_f, *btn_units_c, *btn_fan_only, *btn_fan_damper, *btn_damper_pri;
extern lv_obj_t *lbl_wifi_status, *lbl_wifi_ssid, *lbl_wifi_ip, *lbl_wifi_signal, *btn_wifi_action, *lbl_wifi_action;

UiState ui_state;
static GraphHistory s_history;
static int32_t s_values[4][GRAPH_HISTORY_SIZE];
static int32_t s_times[GRAPH_HISTORY_SIZE];
static void sync_graph_arrays();

void ui_update_temps(float pit, float m1, float m2, bool pc, bool m1c, bool m2c) {
    float values[] = {pit, m1, m2}; bool connected[] = {pc, m1c, m2c};
    lv_obj_t* labels[] = {lbl_pit_temp, lbl_meat1_temp, lbl_meat2_temp};
    lv_color_t colors[] = {COLOR_ORANGE, COLOR_RED, COLOR_BLUE};
    for (int i = 0; i < 3; ++i) {
        ui_state.temps[i] = values[i]; ui_state.connected[i] = connected[i] && isfinite(values[i]);
        if (!labels[i]) continue;
        if (ui_state.connected[i]) UiStyle::text_fmt(labels[i], "%.0f\xC2\xB0", ui_display_temp(values[i]));
        else lv_label_set_text(labels[i], "---");
        lv_obj_set_style_text_color(labels[i], ui_state.connected[i] ? colors[i] : COLOR_TEXT_DIM, 0);
    }
}
void ui_update_setpoint(float sp) {
    if (!isfinite(sp)) return;
    ui_state.setpoint = sp;
    if (lbl_setpoint) UiStyle::text_fmt(lbl_setpoint, "Target %.0f\xC2\xB0%s", ui_display_temp(sp), ui_unit_suffix());
}
static void update_target(int probe, float target) {
    if (!isfinite(target)) return;
    ui_state.targets[probe] = target;
    auto lbl = probe == 0 ? lbl_meat1_target : lbl_meat2_target;
    if (!lbl) return;
    if (target > 0) UiStyle::text_fmt(lbl, "%.0f\xC2\xB0%s", ui_display_temp(target), ui_unit_suffix());
    else lv_label_set_text(lbl, "---");
}
void ui_update_meat1_target(float target) { update_target(0, target); }
void ui_update_meat2_target(float target) { update_target(1, target); }
void ui_set_units(bool fahrenheit) {
    ui_state.fahrenheit = fahrenheit;
    UiStyle::selected(btn_units_f, fahrenheit); UiStyle::selected(btn_units_c, !fahrenheit);
    if (lbl_units) UiStyle::text_fmt(lbl_units, "\xC2\xB0%s", ui_unit_suffix());
    ui_update_temps(ui_state.temps[0], ui_state.temps[1], ui_state.temps[2], ui_state.connected[0], ui_state.connected[1], ui_state.connected[2]);
    ui_update_setpoint(ui_state.setpoint);
    update_target(0, ui_state.targets[0]); update_target(1, ui_state.targets[1]);
    ui_refresh_editors(); sync_graph_arrays();
}
void ui_update_cook_timer(uint32_t, uint32_t elapsed, uint32_t) {
    if (lbl_elapsed) UiStyle::text_fmt(lbl_elapsed, "%02lu:%02lu:%02lu", (unsigned long)(elapsed / 3600), (unsigned long)(elapsed / 60 % 60), (unsigned long)(elapsed % 60));
}
static void estimate(int probe, uint32_t epoch) {
    auto label = probe == 0 ? lbl_meat1_est : lbl_meat2_est;
    if (!label) return;
    if (epoch) {
        time_t t = epoch; struct tm* tm = localtime(&t);
        if (tm) UiStyle::text_fmt(label, "~%02d:%02d", tm->tm_hour, tm->tm_min);
        lv_obj_add_flag(meat_edit_icons[probe], LV_OBJ_FLAG_HIDDEN);
    } else {
        lv_label_set_text(label, ""); lv_obj_remove_flag(meat_edit_icons[probe], LV_OBJ_FLAG_HIDDEN);
    }
}
void ui_update_meat1_estimate(uint32_t epoch) { estimate(0, epoch); }
void ui_update_meat2_estimate(uint32_t epoch) { estimate(1, epoch); }

void ui_update_alerts(uint8_t alarm, bool lidOpen, bool fireOut, uint8_t errors) {
    if (!alert_banner) return;
    const char* text = nullptr; bool acknowledge = alarm >= 1 && alarm <= 4;
    switch (alarm) {
        case 1: text = LV_SYMBOL_WARNING " PIT HIGH"; break;
        case 2: text = LV_SYMBOL_WARNING " PIT LOW"; break;
        case 3: text = LV_SYMBOL_WARNING " MEAT 1 DONE"; break;
        case 4: text = LV_SYMBOL_WARNING " MEAT 2 DONE"; break;
    }
    bool warning = false;
    char message[64];
    if (!text && fireOut) text = LV_SYMBOL_WARNING " FIRE MAY BE OUT";
    if (!text && lidOpen) { text = "LID OPEN"; warning = true; }
    if (!text && errors) {
        snprintf(message, sizeof(message), "Probe error:%s%s%s", errors & 1 ? " Pit" : "", errors & 2 ? " Meat 1" : "", errors & 4 ? " Meat 2" : "");
        text = message; warning = true;
    }
    if (text) {
        lv_label_set_text(lbl_alert_text, text);
        lv_obj_set_width(lbl_alert_text, acknowledge ? 314 : 440);
        lv_obj_align(lbl_alert_text, LV_ALIGN_LEFT_MID, 12, 0);
        lv_obj_set_style_bg_color(alert_banner, warning ? COLOR_ORANGE : COLOR_DANGER, 0);
        lv_obj_set_style_text_color(lbl_alert_text, warning ? COLOR_BG : COLOR_TEXT, 0);
    }
    if (acknowledge) lv_obj_remove_flag(btn_alert_ack, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_add_flag(btn_alert_ack, LV_OBJ_FLAG_HIDDEN);
    ui_layout_alert(text != nullptr);
}
void ui_update_output_bars(float fan, float damper) {
    if (!isfinite(fan)) fan = 0;
    if (!isfinite(damper)) damper = 0;
    fan = fminf(100, fmaxf(0, fan)); damper = fminf(100, fmaxf(0, damper));
    if (lbl_fan_bar) UiStyle::text_fmt(lbl_fan_bar, "FAN %.0f%%", fan);
    if (lbl_damper_bar) UiStyle::text_fmt(lbl_damper_bar, "DAMPER %.0f%%", damper);
    if (bar_fan) lv_bar_set_value(bar_fan, lroundf(fan), LV_ANIM_OFF);
    if (bar_damper) lv_bar_set_value(bar_damper, lroundf(damper), LV_ANIM_OFF);
}
void ui_update_wifi(bool connected) {
    if (!lbl_wifi_icon) return;
    lv_label_set_text(lbl_wifi_icon, connected ? LV_SYMBOL_WIFI : LV_SYMBOL_CLOSE);
    lv_obj_set_style_text_color(lbl_wifi_icon, connected ? COLOR_GREEN : COLOR_RED, 0);
}

static int32_t graph_min = 50, graph_max = 250;
void ui_graph_refresh_layout() {
    if (!chart_temps) return;
    // Styles are lazy in LVGL, including on an inactive screen. Resolve a
    // height change before positioning the external labels beside the grid.
    lv_obj_update_layout(chart_temps);
    int height = lv_obj_get_height(chart_temps);
    for (int i = 0; i < 5; ++i) {
        UiStyle::text_fmt(graph_y_labels[i], "%ld", (long)(graph_max - (graph_max - graph_min) * i / 4));
        lv_obj_set_y(graph_y_labels[i], 32 + (height - 1) * i / 4);
    }
}
static void format_elapsed(char* text, size_t size, uint32_t seconds) {
    if (seconds >= 3600) snprintf(text, size, "%luh %02lum", (unsigned long)(seconds / 3600), (unsigned long)(seconds / 60 % 60));
    else if (seconds >= 60) snprintf(text, size, "%.1f min", seconds / 60.0f);
    else snprintf(text, size, "%lu s", (unsigned long)seconds);
}
static void sync_graph_arrays() {
    if (!chart_temps) return;
    uint16_t count = s_history.getCount();
    lv_chart_set_point_count(chart_temps, count < 2 ? 2 : count);
    float lo = INFINITY, hi = -INFINITY;
    for (uint16_t i = 0; i < (count < 2 ? 2 : count); ++i) {
        s_times[i] = 0;
        for (auto& values : s_values) values[i] = LV_CHART_POINT_NONE;
        if (i >= count) continue;
        const auto& slot = s_history.getSlot(i);
        s_times[i] = slot.elapsedSec - s_history.getStartSec();
        float f[] = {slot.pit, slot.meat1, slot.meat2, slot.setpoint};
        bool valid[] = {slot.pitValid, slot.meat1Valid, slot.meat2Valid, true};
        for (int j = 0; j < 4; ++j) if (valid[j] && isfinite(f[j])) {
            float value = ui_display_temp(f[j]);
            s_values[j][i] = lroundf(value);
            lo = fminf(lo, value); hi = fmaxf(hi, value);
        }
    }
    if (isfinite(lo)) {
        float step = ui_state.fahrenheit ? 25 : 10;
        float padding = ui_state.fahrenheit ? 15 : 8;
        graph_min = floorf((lo - padding) / step) * step;
        int range = (int)(ceilf((hi + padding - graph_min) / (4 * step)) * (4 * step));
        graph_max = graph_min + (range > 0 ? range : (int)(4 * step));
    } else { graph_min = ui_state.fahrenheit ? 50 : 0; graph_max = ui_state.fahrenheit ? 250 : 120; }
    lv_chart_set_range(chart_temps, LV_CHART_AXIS_PRIMARY_Y, graph_min, graph_max);
    uint32_t duration = count ? s_history.getEndSec() - s_history.getStartSec() : 0;
    lv_chart_set_range(chart_temps, LV_CHART_AXIS_PRIMARY_X, 0, duration ? duration : 60);
    for (int i = 0; i < 3; ++i) {
        char label[32]; format_elapsed(label, sizeof(label), duration * (uint64_t)i / 2);
        lv_label_set_text(graph_x_labels[i], label);
    }
    char span[32]; format_elapsed(span, sizeof(span), duration);
    lv_label_set_text(lbl_graph_span, count ? span : "No data");
    UiStyle::text_fmt(lbl_graph_title, "Temperature history (\xC2\xB0%s)", ui_unit_suffix());
    ui_graph_refresh_layout(); lv_chart_refresh(chart_temps);
}
void ui_graph_init() {
    lv_chart_series_t* series[] = {ser_pit, ser_meat1, ser_meat2, ser_setpoint};
    for (int i = 0; i < 4; ++i) {
        for (auto& value : s_values[i]) value = LV_CHART_POINT_NONE;
        lv_chart_set_ext_y_array(chart_temps, series[i], s_values[i]);
        lv_chart_set_ext_x_array(chart_temps, series[i], s_times);
    }
    sync_graph_arrays();
}
void ui_graph_add_point(float pit, float meat1, float meat2, float sp, bool pd, bool m1d, bool m2d, uint32_t elapsed) {
    s_history.addPoint(pit, meat1, meat2, sp, pd, m1d, m2d, elapsed); sync_graph_arrays();
}
void ui_graph_clear() { s_history.clear(); sync_graph_arrays(); }
static const char* rssi_quality(int rssi) {
    if (rssi == 0)    return "N/A";
    if (rssi >= -50)  return "Excellent";
    if (rssi >= -60)  return "Good";
    if (rssi >= -70)  return "Fair";
    return "Weak";
}

void ui_update_wifi_info(const WifiInfo& info) {
    if (lbl_wifi_status) {
        if (info.connected) {
            lv_label_set_text(lbl_wifi_status, "Connected");
            lv_obj_set_style_text_color(lbl_wifi_status, COLOR_GREEN, 0);
        } else if (info.apMode) {
            lv_label_set_text(lbl_wifi_status, "AP Mode");
            lv_obj_set_style_text_color(lbl_wifi_status, COLOR_ORANGE, 0);
        } else {
            lv_label_set_text(lbl_wifi_status, "Disconnected");
            lv_obj_set_style_text_color(lbl_wifi_status, COLOR_RED, 0);
        }
    }

    if (lbl_wifi_ssid) {
        char buf[48];
        if (info.ssid && info.ssid[0]) {
            snprintf(buf, sizeof(buf), "SSID: %s", info.ssid);
        } else {
            snprintf(buf, sizeof(buf), "SSID: ---");
        }
        lv_label_set_text(lbl_wifi_ssid, buf);
    }

    if (lbl_wifi_ip) {
        char buf[64];
        if (info.connected && !info.apMode) {
            snprintf(buf, sizeof(buf), "IP: %s  (bbq.local)", info.ip ? info.ip : "---");
        } else if (info.ip && info.ip[0]) {
            snprintf(buf, sizeof(buf), "IP: %s", info.ip);
        } else {
            snprintf(buf, sizeof(buf), "IP: ---");
        }
        lv_label_set_text(lbl_wifi_ip, buf);
    }

    if (lbl_wifi_signal) {
        char buf[32];
        if (info.connected && !info.apMode && info.rssi != 0) {
            snprintf(buf, sizeof(buf), "Signal: %d dBm (%s)", info.rssi, rssi_quality(info.rssi));
        } else {
            snprintf(buf, sizeof(buf), "Signal: ---");
        }
        lv_label_set_text(lbl_wifi_signal, buf);
    }

    // Toggle button label between Disconnect and Reconnect
    if (lbl_wifi_action) {
        if (info.connected || info.apMode) {
            lv_label_set_text(lbl_wifi_action, "Disconnect");
        } else {
            lv_label_set_text(lbl_wifi_action, "Reconnect");
        }
    }
}

void ui_update_settings_state(bool fahrenheit, const char* mode) {
    ui_set_units(fahrenheit);
    UiStyle::selected(btn_fan_only, mode && strcmp(mode, "fan_only") == 0);
    UiStyle::selected(btn_fan_damper, mode && strcmp(mode, "fan_and_damper") == 0);
    UiStyle::selected(btn_damper_pri, mode && strcmp(mode, "damper_primary") == 0);
}
#else // NATIVE_BUILD && !SIMULATOR_BUILD
// Native test stubs
void ui_update_temps(float, float, float, bool, bool, bool) {}
void ui_update_setpoint(float) {}
void ui_update_cook_timer(uint32_t, uint32_t, uint32_t) {}
void ui_update_meat1_target(float) {}
void ui_update_meat2_target(float) {}
void ui_update_meat1_estimate(uint32_t) {}
void ui_update_meat2_estimate(uint32_t) {}
void ui_update_alerts(uint8_t, bool, bool, uint8_t) {}
void ui_update_output_bars(float, float) {}
void ui_update_wifi(bool) {}
void ui_update_wifi_info(const WifiInfo&) {}
void ui_graph_init() {}
void ui_graph_add_point(float, float, float, float, bool, bool, bool, uint32_t) {}
void ui_graph_clear() {}
void ui_update_settings_state(bool, const char*) {}
void ui_set_units(bool) {}
#endif
