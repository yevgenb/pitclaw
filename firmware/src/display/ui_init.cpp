#include "ui_init.h"
#include "ui_update.h"
#include "ui_setup_wizard.h"
#include "ui_colors.h"

#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)

#include <lvgl.h>
#include <stdio.h>
#include <string.h>
#include <cstring>

#ifndef SIMULATOR_BUILD
#include <PanelLan.h>

// --------------------------------------------------------------------------
// Display driver (hardware)
// --------------------------------------------------------------------------

static PanelLan tft(BOARD_SC01_PLUS);

// LVGL 9's lv_color_t is RGB888 regardless of the display's pixel format.
static uint16_t draw_buf1[DISPLAY_WIDTH * 40];
static uint16_t draw_buf2[DISPLAY_WIDTH * 40];

static void disp_flush_cb(lv_display_t* disp, const lv_area_t* area, uint8_t* px_map) {
    uint32_t w = area->x2 - area->x1 + 1;
    uint32_t h = area->y2 - area->y1 + 1;

    tft.startWrite();
    tft.pushImage(area->x1, area->y1, w, h,
                  reinterpret_cast<lgfx::rgb565_t*>(px_map));
    tft.waitDMA();
    tft.endWrite();

    lv_display_flush_ready(disp);
}

static void touchpad_read_cb(lv_indev_t* indev, lv_indev_data_t* data) {
    uint16_t touchX, touchY;
    bool touched = tft.getTouch(&touchX, &touchY);

    if (touched) {
        data->state = LV_INDEV_STATE_PRESSED;
        data->point.x = touchX;
        data->point.y = touchY;
    } else {
        data->state = LV_INDEV_STATE_RELEASED;
    }
}
#endif // !SIMULATOR_BUILD

#include "ui_styles.h"
#include "ui_state.h"
#include <math.h>
#include <initializer_list>
using UiStyle::Button;

static lv_obj_t* scr_dashboard = nullptr;
static lv_obj_t* scr_graph = nullptr;
static lv_obj_t* scr_settings = nullptr;
static Screen current_screen = Screen::DASHBOARD;
static lv_obj_t* nav_btns[3][3] = {};
static lv_obj_t* pit_card = nullptr;
static lv_obj_t* meat_cards[2] = {};
static lv_obj_t* settings_content = nullptr;
static lv_obj_t* graph_legend = nullptr;
static bool alert_active = false;

lv_obj_t *lbl_wifi_icon = nullptr, *lbl_elapsed = nullptr, *lbl_units = nullptr;
lv_obj_t *lbl_pit_temp = nullptr, *lbl_setpoint = nullptr;
lv_obj_t *lbl_meat1_temp = nullptr, *lbl_meat2_temp = nullptr;
lv_obj_t *lbl_meat1_target = nullptr, *lbl_meat2_target = nullptr;
lv_obj_t *lbl_meat1_est = nullptr, *lbl_meat2_est = nullptr;
lv_obj_t *meat_edit_icons[2] = {}, *meat_target_captions[2] = {};
lv_obj_t *bar_fan = nullptr, *bar_damper = nullptr, *lbl_fan_bar = nullptr, *lbl_damper_bar = nullptr;
lv_obj_t *alert_banner = nullptr, *lbl_alert_text = nullptr, *btn_alert_ack = nullptr;
lv_obj_t *chart_temps = nullptr, *lbl_graph_title = nullptr, *lbl_graph_span = nullptr;
lv_chart_series_t *ser_pit = nullptr, *ser_meat1 = nullptr, *ser_meat2 = nullptr, *ser_setpoint = nullptr;
lv_obj_t* graph_y_labels[5] = {};
lv_obj_t* graph_x_labels[3] = {};
lv_obj_t *btn_units_f = nullptr, *btn_units_c = nullptr;
lv_obj_t *btn_fan_only = nullptr, *btn_fan_damper = nullptr, *btn_damper_pri = nullptr;
lv_obj_t *lbl_wifi_status = nullptr, *lbl_wifi_ssid = nullptr, *lbl_wifi_ip = nullptr, *lbl_wifi_signal = nullptr;
lv_obj_t *btn_wifi_action = nullptr, *lbl_wifi_action = nullptr;

static lv_obj_t *modal_setpoint = nullptr, *modal_meat = nullptr, *modal_confirm = nullptr;
static lv_obj_t *lbl_modal_sp_value = nullptr, *lbl_modal_meat_value = nullptr;
static lv_obj_t *lbl_modal_meat_title = nullptr, *lbl_sp_range = nullptr, *lbl_meat_range = nullptr;
static lv_obj_t *lbl_confirm_title = nullptr, *lbl_confirm_msg = nullptr;
static float modal_sp_value = 225, modal_meat_value = 195;
static uint8_t modal_meat_probe = 1;
static void (*confirm_action_cb)() = nullptr;
static UiSetpointCb cb_setpoint = nullptr;
static UiMeatTargetCb cb_meat_target = nullptr;
static UiAlarmAckCb cb_alarm_ack = nullptr;
static UiUnitsCb cb_units = nullptr;
static UiFanModeCb cb_fan_mode = nullptr;
static UiNewSessionCb cb_new_session = nullptr;
static UiFactoryResetCb cb_factory_reset = nullptr;
static UiWifiActionCb cb_wifi_action = nullptr;

void ui_set_callbacks(UiSetpointCb sp, UiMeatTargetCb meat, UiAlarmAckCb ack) {
    cb_setpoint = sp; cb_meat_target = meat; cb_alarm_ack = ack;
}
void ui_set_settings_callbacks(UiUnitsCb units, UiFanModeCb fan, UiNewSessionCb session, UiFactoryResetCb reset) {
    cb_units = units; cb_fan_mode = fan; cb_new_session = session; cb_factory_reset = reset;
}
void ui_set_wifi_callback(UiWifiActionCb cb) { cb_wifi_action = cb; }

static lv_obj_t* new_screen() { return UiStyle::box(nullptr, 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOR_BG, 0); }
static void nav_event_cb(lv_event_t* e) { ui_switch_screen((Screen)(uintptr_t)lv_event_get_user_data(e)); }
static void create_nav_bar(lv_obj_t* parent, uint8_t index) {
    // Separate rounded controls share the cards' outer margins and gutter.
    constexpr int nav_width = DISPLAY_WIDTH - 2 * UiStyle::SPACE;
    constexpr int button_space = nav_width - 2 * UiStyle::SPACE;
    auto nav = UiStyle::box(parent, UiStyle::SPACE, UiStyle::NAV_TOP, nav_width, UiStyle::NAV_HEIGHT, COLOR_BG, 0);
    const char* labels[] = {LV_SYMBOL_HOME " Home", LV_SYMBOL_IMAGE " Graph", LV_SYMBOL_SETTINGS " Settings"};
    for (int i = 0; i < 3; ++i) {
        const int left = i * button_space / 3;
        const int right = (i + 1) * button_space / 3;
        auto btn = UiStyle::button(nav, labels[i], left + i * UiStyle::SPACE, 0, right - left, UiStyle::NAV_HEIGHT);
        lv_obj_set_style_bg_color(btn, COLOR_CARD_BG, 0);
        lv_obj_add_event_cb(btn, nav_event_cb, LV_EVENT_CLICKED, (void*)(uintptr_t)i);
        nav_btns[index][i] = btn;
        UiStyle::selected(btn, i == index);
    }
}
static void update_nav_highlight(Screen screen) {
    for (auto& row : nav_btns) for (int i = 0; i < 3; ++i) UiStyle::selected(row[i], i == (int)screen);
}

static bool modal_open(lv_obj_t* obj) { return obj && !lv_obj_has_flag(obj, LV_OBJ_FLAG_HIDDEN); }
void ui_refresh_alert_layout() {
    if (!alert_banner) return;
    auto active = lv_screen_active();
    bool main = active == scr_dashboard || active == scr_graph || active == scr_settings;
    if (!alert_active || !main) lv_obj_add_flag(alert_banner, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_remove_flag(alert_banner, LV_OBJ_FLAG_HIDDEN);
    bool editing = modal_open(modal_setpoint) || modal_open(modal_meat) || modal_open(modal_confirm);
    // A modal leaves a full-width alarm row above it. Silence stays accessible.
    lv_obj_set_y(alert_banner, editing ? 4 : 208);
    for (auto m : {modal_setpoint, modal_meat, modal_confirm}) {
        if (!m) continue;
        auto card = lv_obj_get_child(m, 0);
        lv_obj_set_pos(card, 32, alert_active ? 64 : 32);
        lv_obj_set_height(card, alert_active ? 248 : 256);
    }
    if (alert_active && main) lv_obj_move_foreground(alert_banner);
}
void ui_layout_alert(bool active) {
    if (alert_active != active) {
        alert_active = active;
        lv_obj_set_height(pit_card, active ? 136 : 190);
        // Pit title is child 0, edit icon 1, value 2, target 3.
        lv_obj_set_y(lv_obj_get_child(pit_card, 0), active ? 10 : 18);
        lv_obj_set_y(lbl_pit_temp, active ? 36 : 69);
        lv_obj_set_y(lbl_setpoint, active ? 102 : 156);
        lv_obj_t* values[] = {lbl_meat1_temp, lbl_meat2_temp};
        lv_obj_t* targets[] = {lbl_meat1_target, lbl_meat2_target};
        for (int i = 0; i < 2; ++i) {
            lv_obj_set_height(meat_cards[i], active ? 64 : 91);
            lv_obj_set_y(meat_cards[i], 64 + i * (active ? 72 : 99));
            lv_obj_set_style_text_font(values[i], active ? &lv_font_montserrat_24 : &lv_font_montserrat_36, 0);
            lv_obj_set_y(values[i], active ? 29 : 36);
            lv_obj_set_y(meat_target_captions[i], active ? 23 : 32);
            lv_obj_set_y(targets[i], active ? 42 : 54);
        }
        if (settings_content) lv_obj_set_height(settings_content, active ? 158 : 214);
        if (chart_temps) {
            lv_obj_set_height(chart_temps, active ? 112 : 168);
            for (auto x : graph_x_labels) lv_obj_set_y(x, active ? 156 : 212);
            lv_obj_set_y(graph_legend, active ? 180 : 236);
            ui_graph_refresh_layout();
        }
    }
    ui_refresh_alert_layout();
}
static lv_obj_t* create_modal_overlay() {
    auto obj = UiStyle::box(lv_layer_top(), 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(obj, LV_OPA_60, 0);
    lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    return obj;
}
static void show_modal(lv_obj_t* obj) {
    lv_obj_remove_flag(obj, LV_OBJ_FLAG_HIDDEN);
    lv_obj_move_foreground(obj);
    ui_refresh_alert_layout();
}
static void hide_modal(lv_obj_t* obj) {
    if (obj) lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    ui_refresh_alert_layout();
}

static void update_sp_modal_display() {
    if (lbl_modal_sp_value) UiStyle::text_fmt(lbl_modal_sp_value, "%.0f\xC2\xB0%s", ui_display_temp(modal_sp_value), ui_unit_suffix());
    if (lbl_sp_range) UiStyle::text_fmt(lbl_sp_range, "%.0f - %.0f\xC2\xB0%s  |  Hold for 5\xC2\xB0 steps", ui_display_temp(100), ui_display_temp(500), ui_unit_suffix());
}
static void update_meat_modal_display() {
    if (lbl_modal_meat_value) {
        UiStyle::text_fmt(lbl_modal_meat_value, "%.0f\xC2\xB0%s", ui_display_temp(modal_meat_value), ui_unit_suffix());
        lv_obj_set_style_text_color(lbl_modal_meat_value, modal_meat_probe == 1 ? COLOR_RED : COLOR_BLUE, 0);
    }
    if (lbl_modal_meat_title) UiStyle::text_fmt(lbl_modal_meat_title, "Meat %u target", modal_meat_probe);
    if (lbl_meat_range) UiStyle::text_fmt(lbl_meat_range, "%.0f - %.0f\xC2\xB0%s  |  Hold for 5\xC2\xB0 steps", ui_display_temp(100), ui_display_temp(212), ui_unit_suffix());
}
void ui_refresh_editors() { update_sp_modal_display(); update_meat_modal_display(); }
static float adjusted_value(float original, int direction, lv_event_t* e, float maximum) {
    float step = e && lv_event_get_code(e) == LV_EVENT_LONG_PRESSED_REPEAT ? 5 : 1;
    float value = roundf(ui_display_temp(original)) + direction * step;
    if (!ui_state.fahrenheit) value = celsiusToFahrenheit(value);
    return fminf(maximum, fmaxf(100, value));
}
static void sp_minus_cb(lv_event_t* e) { modal_sp_value = adjusted_value(modal_sp_value, -1, e, 500); update_sp_modal_display(); }
static void sp_plus_cb(lv_event_t* e) { modal_sp_value = adjusted_value(modal_sp_value, 1, e, 500); update_sp_modal_display(); }
static void meat_minus_cb(lv_event_t* e) { modal_meat_value = adjusted_value(modal_meat_value, -1, e, 212); update_meat_modal_display(); }
static void meat_plus_cb(lv_event_t* e) { modal_meat_value = adjusted_value(modal_meat_value, 1, e, 212); update_meat_modal_display(); }
static void sp_cancel_cb(lv_event_t*) { hide_modal(modal_setpoint); }
static void meat_cancel_cb(lv_event_t*) { hide_modal(modal_meat); }
static void sp_apply_cb(lv_event_t*) {
    ui_update_setpoint(modal_sp_value);
    hide_modal(modal_setpoint);
    if (cb_setpoint) cb_setpoint(modal_sp_value);
}
static void meat_set_cb(lv_event_t*) {
    if (modal_meat_probe == 1) ui_update_meat1_target(modal_meat_value);
    else ui_update_meat2_target(modal_meat_value);
    hide_modal(modal_meat);
    if (cb_meat_target) cb_meat_target(modal_meat_probe, modal_meat_value);
}
static void meat_clear_cb(lv_event_t*) {
    if (modal_meat_probe == 1) ui_update_meat1_target(0);
    else ui_update_meat2_target(0);
    hide_modal(modal_meat);
    if (cb_meat_target) cb_meat_target(modal_meat_probe, 0);
}
static void pit_card_click_cb(lv_event_t*) {
    modal_sp_value = ui_state.setpoint; update_sp_modal_display(); show_modal(modal_setpoint);
}
static void open_meat(uint8_t probe) {
    modal_meat_probe = probe;
    modal_meat_value = ui_state.targets[probe - 1] > 0 ? ui_state.targets[probe - 1] : 195;
    update_meat_modal_display(); show_modal(modal_meat);
}
static void meat1_card_click_cb(lv_event_t*) { open_meat(1); }
static void meat2_card_click_cb(lv_event_t*) { open_meat(2); }
static lv_obj_t* modal_action(lv_obj_t* card, const char* text, int x, int w, Button role, lv_event_cb_t cb) {
    auto btn = UiStyle::button(card, text, x, 188, w, 52, role);
    lv_obj_align(btn, LV_ALIGN_BOTTOM_LEFT, x, -16);
    lv_obj_add_event_cb(btn, cb, LV_EVENT_CLICKED, nullptr);
    return btn;
}
static void create_temperature_modal(bool meat) {
    auto overlay = create_modal_overlay();
    auto card = UiStyle::box(overlay, 32, 32, 416, 256, COLOR_CARD_BG, UiStyle::DIALOG_RADIUS);
    auto title = UiStyle::label(card, meat ? "Meat 1 target" : "Pit setpoint", 16, 18, &lv_font_montserrat_24, COLOR_TEXT, 384, LV_TEXT_ALIGN_CENTER);
    auto minus = UiStyle::button(card, "-1", 20, 70, 76, 64, Button::Secondary, &lv_font_montserrat_24);
    auto value = UiStyle::label(card, "", 108, 81, &lv_font_montserrat_36, COLOR_ORANGE, 200, LV_TEXT_ALIGN_CENTER);
    auto plus = UiStyle::button(card, "+1", 320, 70, 76, 64, Button::Secondary, &lv_font_montserrat_24);
    for (auto code : {LV_EVENT_SHORT_CLICKED, LV_EVENT_LONG_PRESSED_REPEAT}) {
        lv_obj_add_event_cb(minus, meat ? meat_minus_cb : sp_minus_cb, code, nullptr);
        lv_obj_add_event_cb(plus, meat ? meat_plus_cb : sp_plus_cb, code, nullptr);
    }
    auto range = UiStyle::label(card, "", 16, 146, &lv_font_montserrat_16, COLOR_TEXT_DIM, 384, LV_TEXT_ALIGN_CENTER);
    if (meat) {
        modal_meat = overlay; lbl_modal_meat_title = title; lbl_modal_meat_value = value; lbl_meat_range = range;
        modal_action(card, "Clear", 16, 120, Button::Secondary, meat_clear_cb);
        modal_action(card, "Cancel", 148, 120, Button::Secondary, meat_cancel_cb);
        modal_action(card, "Set", 280, 120, Button::Primary, meat_set_cb);
    } else {
        modal_setpoint = overlay; lbl_modal_sp_value = value; lbl_sp_range = range;
        modal_action(card, "Cancel", 16, 186, Button::Secondary, sp_cancel_cb);
        modal_action(card, "Apply", 214, 186, Button::Primary, sp_apply_cb);
    }
    ui_refresh_editors();
}
static void create_setpoint_modal() { create_temperature_modal(false); }
static void create_meat_target_modal() { create_temperature_modal(true); }
static void confirm_cancel_cb(lv_event_t*) { hide_modal(modal_confirm); }
static void confirm_ok_cb(lv_event_t*) { hide_modal(modal_confirm); if (confirm_action_cb) confirm_action_cb(); }
static void show_confirm(const char* title, const char* message, void (*action)()) {
    confirm_action_cb = action;
    lv_label_set_text(lbl_confirm_title, title); lv_label_set_text(lbl_confirm_msg, message);
    show_modal(modal_confirm);
}
static void create_confirm_modal() {
    modal_confirm = create_modal_overlay();
    auto card = UiStyle::box(modal_confirm, 32, 32, 416, 256, COLOR_CARD_BG, UiStyle::DIALOG_RADIUS);
    lbl_confirm_title = UiStyle::label(card, "Confirm", 16, 18, &lv_font_montserrat_24, COLOR_TEXT, 384, LV_TEXT_ALIGN_CENTER);
    lbl_confirm_msg = UiStyle::label(card, "", 24, 80, &lv_font_montserrat_18, COLOR_TEXT_DIM, 368, LV_TEXT_ALIGN_CENTER);
    modal_action(card, "Cancel", 16, 186, Button::Secondary, confirm_cancel_cb);
    modal_action(card, "Confirm", 214, 186, Button::Danger, confirm_ok_cb);
}

static void alert_tap_cb(lv_event_t*) { if (cb_alarm_ack) cb_alarm_ack(); }
static lv_obj_t* output_bar(lv_obj_t* parent, int x, int width, lv_color_t color) {
    auto bar = lv_bar_create(parent); lv_obj_remove_style_all(bar);
    lv_obj_set_pos(bar, x, 45); lv_obj_set_size(bar, width, 6);
    lv_obj_set_style_bg_color(bar, COLOR_BAR_BG, LV_PART_MAIN); lv_obj_set_style_bg_opa(bar, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_bg_color(bar, color, LV_PART_INDICATOR); lv_obj_set_style_bg_opa(bar, LV_OPA_COVER, LV_PART_INDICATOR);
    lv_obj_set_style_radius(bar, 3, LV_PART_MAIN); lv_obj_set_style_radius(bar, 3, LV_PART_INDICATOR);
    return bar;
}
static void create_dashboard_screen() {
    scr_dashboard = new_screen();
    auto header = UiStyle::box(scr_dashboard, 0, 0, 480, 32, COLOR_NAV_BG, 0);
    lbl_wifi_icon = UiStyle::label(header, LV_SYMBOL_WIFI, 12, 8, &lv_font_montserrat_16, COLOR_GREEN);
    UiStyle::label(header, "Cook", 40, 7, &lv_font_montserrat_16, COLOR_TEXT_DIM);
    lbl_elapsed = UiStyle::label(header, "00:00:00", 142, 2, &lv_font_montserrat_24, COLOR_TEXT, 196, LV_TEXT_ALIGN_CENTER);
    lbl_units = UiStyle::label(header, "\xC2\xB0" "F", 428, 5, &lv_font_montserrat_18, COLOR_TEXT_DIM, 40, LV_TEXT_ALIGN_RIGHT);
    lbl_fan_bar = UiStyle::label(scr_dashboard, "FAN 0%", 12, 38, &lv_font_montserrat_16, COLOR_GREEN);
    bar_fan = output_bar(scr_dashboard, 105, 111, COLOR_GREEN);
    lbl_damper_bar = UiStyle::label(scr_dashboard, "DAMPER 0%", 246, 38, &lv_font_montserrat_16, COLOR_PURPLE);
    bar_damper = output_bar(scr_dashboard, 373, 95, COLOR_PURPLE);
    pit_card = UiStyle::card(scr_dashboard, 8, 64, 228, 190, COLOR_ORANGE);
    lv_obj_add_event_cb(pit_card, pit_card_click_cb, LV_EVENT_CLICKED, nullptr);
    UiStyle::label(pit_card, "PIT", 16, 18, &lv_font_montserrat_18, COLOR_ORANGE, 190, LV_TEXT_ALIGN_CENTER);
    UiStyle::label(pit_card, LV_SYMBOL_EDIT, 190, 12, &lv_font_montserrat_14, COLOR_TEXT_DIM);
    lbl_pit_temp = UiStyle::label(pit_card, "---", 12, 69, &lv_font_montserrat_48, COLOR_ORANGE, 198, LV_TEXT_ALIGN_CENTER);
    lbl_setpoint = UiStyle::label(pit_card, "", 12, 156, &lv_font_montserrat_18, COLOR_TEXT_DIM, 198, LV_TEXT_ALIGN_CENTER);
    for (int i = 0; i < 2; ++i) {
        auto card = UiStyle::card(scr_dashboard, 244, 64 + i * 99, 228, 91, i == 0 ? COLOR_RED : COLOR_BLUE);
        meat_cards[i] = card;
        lv_obj_add_event_cb(card, i == 0 ? meat1_card_click_cb : meat2_card_click_cb, LV_EVENT_CLICKED, nullptr);
        UiStyle::label(card, i == 0 ? "MEAT 1" : "MEAT 2", 14, 9, &lv_font_montserrat_16, COLOR_TEXT_DIM);
        meat_edit_icons[i] = UiStyle::label(card, LV_SYMBOL_EDIT, 196, 9, &lv_font_montserrat_14, COLOR_TEXT_DIM);
        auto temp = UiStyle::label(card, "---", 14, 36, &lv_font_montserrat_36, i == 0 ? COLOR_RED : COLOR_BLUE);
        meat_target_captions[i] = UiStyle::label(card, "Target", 128, 32, &lv_font_montserrat_16, COLOR_TEXT_DIM);
        auto target = UiStyle::label(card, "---", 128, 54, &lv_font_montserrat_16);
        auto est = UiStyle::label(card, "", 118, 9, &lv_font_montserrat_14, COLOR_TEXT_DIM, 94, LV_TEXT_ALIGN_RIGHT);
        if (i == 0) { lbl_meat1_temp = temp; lbl_meat1_target = target; lbl_meat1_est = est; }
        else { lbl_meat2_temp = temp; lbl_meat2_target = target; lbl_meat2_est = est; }
    }
    create_nav_bar(scr_dashboard, 0);
    alert_banner = UiStyle::box(lv_layer_top(), 8, 208, 464, 52, COLOR_DANGER);
    lv_obj_add_flag(alert_banner, LV_OBJ_FLAG_HIDDEN);
    lbl_alert_text = UiStyle::label(alert_banner, "", 12, 0, &lv_font_montserrat_18, COLOR_TEXT, 314);
    lv_obj_align(lbl_alert_text, LV_ALIGN_LEFT_MID, 12, 0);
    btn_alert_ack = UiStyle::button(alert_banner, "Silence", 338, 0, 126, 52, Button::Danger);
    lv_obj_set_style_bg_color(btn_alert_ack, lv_color_hex(0x801A15), 0);
    lv_obj_add_event_cb(btn_alert_ack, alert_tap_cb, LV_EVENT_CLICKED, nullptr);
}

static void graph_draw_cb(lv_event_t* e) {
    auto task = (lv_draw_task_t*)lv_event_get_param(e);
    auto line = lv_draw_task_get_line_dsc(task);
    // Scatter draws the most recently added series first: target is index 0.
    if (line && line->base.part == LV_PART_ITEMS && line->base.id1 == 0) {
        line->dash_width = 8; line->dash_gap = 6;
    }
}
static void create_graph_screen() {
    scr_graph = new_screen();
    lbl_graph_title = UiStyle::label(scr_graph, "Temperature history (\xC2\xB0" "F)", 12, 8, &lv_font_montserrat_18);
    lbl_graph_span = UiStyle::label(scr_graph, "", 374, 10, &lv_font_montserrat_16, COLOR_TEXT_DIM, 94, LV_TEXT_ALIGN_RIGHT);
    chart_temps = lv_chart_create(scr_graph); lv_obj_remove_style_all(chart_temps);
    lv_obj_remove_flag(chart_temps, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_pos(chart_temps, 50, 40); lv_obj_set_size(chart_temps, 422, 168);
    lv_obj_set_style_bg_color(chart_temps, COLOR_CARD_BG, 0); lv_obj_set_style_bg_opa(chart_temps, LV_OPA_COVER, 0);
    lv_obj_set_style_line_color(chart_temps, lv_color_hex(0x474747), LV_PART_MAIN);
    lv_obj_set_style_line_width(chart_temps, 1, LV_PART_MAIN);
    lv_obj_set_style_line_width(chart_temps, 2, LV_PART_ITEMS);
    lv_obj_set_style_size(chart_temps, 0, 0, LV_PART_INDICATOR);
    // Scatter lines use elapsed seconds for X, including unevenly condensed history.
    lv_chart_set_type(chart_temps, LV_CHART_TYPE_SCATTER);
    lv_chart_set_point_count(chart_temps, 2);
    lv_chart_set_range(chart_temps, LV_CHART_AXIS_PRIMARY_Y, 50, 250);
    lv_chart_set_div_line_count(chart_temps, 5, 3);
    lv_obj_add_flag(chart_temps, LV_OBJ_FLAG_SEND_DRAW_TASK_EVENTS);
    lv_obj_add_event_cb(chart_temps, graph_draw_cb, LV_EVENT_DRAW_TASK_ADDED, nullptr);
    ser_pit = lv_chart_add_series(chart_temps, COLOR_ORANGE, LV_CHART_AXIS_PRIMARY_Y);
    ser_meat1 = lv_chart_add_series(chart_temps, COLOR_RED, LV_CHART_AXIS_PRIMARY_Y);
    ser_meat2 = lv_chart_add_series(chart_temps, COLOR_BLUE, LV_CHART_AXIS_PRIMARY_Y);
    ser_setpoint = lv_chart_add_series(chart_temps, COLOR_TEXT_DIM, LV_CHART_AXIS_PRIMARY_Y);
    for (int i = 0; i < 5; ++i) graph_y_labels[i] = UiStyle::label(scr_graph, "", 0, 32 + i * 42, &lv_font_montserrat_14, COLOR_TEXT_DIM, 42, LV_TEXT_ALIGN_RIGHT);
    graph_x_labels[0] = UiStyle::label(scr_graph, "", 50, 212, &lv_font_montserrat_14, COLOR_TEXT_DIM, 110);
    graph_x_labels[1] = UiStyle::label(scr_graph, "", 200, 212, &lv_font_montserrat_14, COLOR_TEXT_DIM, 120, LV_TEXT_ALIGN_CENTER);
    graph_x_labels[2] = UiStyle::label(scr_graph, "", 362, 212, &lv_font_montserrat_14, COLOR_TEXT_DIM, 110, LV_TEXT_ALIGN_RIGHT);
    graph_legend = UiStyle::box(scr_graph, 50, 236, 422, 24, COLOR_BG, 0);
    UiStyle::label(graph_legend, "Pit", 30, 3, &lv_font_montserrat_16, COLOR_ORANGE);
    UiStyle::label(graph_legend, "Meat 1", 100, 3, &lv_font_montserrat_16, COLOR_RED);
    UiStyle::label(graph_legend, "Meat 2", 196, 3, &lv_font_montserrat_16, COLOR_BLUE);
    UiStyle::label(graph_legend, "-- Target", 292, 3, &lv_font_montserrat_16, COLOR_TEXT_DIM);
    create_nav_bar(scr_graph, 1);
}

static void units_f_click(lv_event_t*) { ui_set_units(true); if (cb_units) cb_units(true); }
static void units_c_click(lv_event_t*) { ui_set_units(false); if (cb_units) cb_units(false); }
static void select_fan(const char* mode) { ui_update_settings_state(ui_state.fahrenheit, mode); if (cb_fan_mode) cb_fan_mode(mode); }
static void fan_only_click(lv_event_t*) { select_fan("fan_only"); }
static void fan_damper_click(lv_event_t*) { select_fan("fan_and_damper"); }
static void damper_pri_click(lv_event_t*) { select_fan("damper_primary"); }
static void new_session_click(lv_event_t*) { show_confirm("New session", "Start a new cook session?\nCurrent data will be lost.", []() { if (cb_new_session) cb_new_session(); }); }
static void factory_reset_click(lv_event_t*) { show_confirm("Factory reset", "Erase all settings and data?\nDevice will restart.", []() { if (cb_factory_reset) cb_factory_reset(); }); }
static void wifi_action_click(lv_event_t*) {
    if (strcmp(lv_label_get_text(lbl_wifi_action), "Disconnect") == 0)
        show_confirm("Disconnect Wi-Fi", "Web clients will lose connection.\nDisconnect?", []() { if (cb_wifi_action) cb_wifi_action("disconnect"); });
    else if (cb_wifi_action) cb_wifi_action("reconnect");
}
static void wifi_setup_click(lv_event_t*) { show_confirm("Setup mode", "Start Wi-Fi setup AP?\nCurrent connection will drop.", []() { if (cb_wifi_action) cb_wifi_action("setup_ap"); }); }
static void create_settings_screen() {
    scr_settings = new_screen();
    UiStyle::label(scr_settings, "Settings", 8, 8, &lv_font_montserrat_24, COLOR_TEXT, 464, LV_TEXT_ALIGN_CENTER);
    settings_content = UiStyle::box(scr_settings, 8, 46, 464, 214, COLOR_BG, 0);
    lv_obj_add_flag(settings_content, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scroll_dir(settings_content, LV_DIR_VER);
    lv_obj_set_scrollbar_mode(settings_content, LV_SCROLLBAR_MODE_AUTO);
    lv_obj_set_style_bg_color(settings_content, COLOR_TEXT_DIM, LV_PART_SCROLLBAR);
    lv_obj_set_style_bg_opa(settings_content, LV_OPA_COVER, LV_PART_SCROLLBAR);
    lv_obj_set_style_width(settings_content, 3, LV_PART_SCROLLBAR);
    auto row = UiStyle::box(settings_content, 0, 0, 464, 56, COLOR_CARD_BG);
    UiStyle::label(row, "Units", 16, 18, &lv_font_montserrat_18);
    btn_units_f = UiStyle::button(row, "\xC2\xB0" "F", 272, 2, 88);
    btn_units_c = UiStyle::button(row, "\xC2\xB0" "C", 368, 2, 88);
    lv_obj_add_event_cb(btn_units_f, units_f_click, LV_EVENT_CLICKED, nullptr);
    lv_obj_add_event_cb(btn_units_c, units_c_click, LV_EVENT_CLICKED, nullptr);
    UiStyle::selected(btn_units_f, true);
    row = UiStyle::box(settings_content, 0, 64, 464, 64, COLOR_CARD_BG);
    UiStyle::label(row, "Fan", 16, 22, &lv_font_montserrat_18);
    btn_fan_only = UiStyle::button(row, "Fan only", 116, 6, 108, 52, Button::Secondary, &lv_font_montserrat_16);
    btn_fan_damper = UiStyle::button(row, "Fan +\ndamper", 232, 6, 108, 52, Button::Secondary, &lv_font_montserrat_16);
    btn_damper_pri = UiStyle::button(row, "Damper\npriority", 348, 6, 108, 52, Button::Secondary, &lv_font_montserrat_16);
    lv_obj_add_event_cb(btn_fan_only, fan_only_click, LV_EVENT_CLICKED, nullptr);
    lv_obj_add_event_cb(btn_fan_damper, fan_damper_click, LV_EVENT_CLICKED, nullptr);
    lv_obj_add_event_cb(btn_damper_pri, damper_pri_click, LV_EVENT_CLICKED, nullptr);
    UiStyle::selected(btn_fan_damper, true);
    auto session = UiStyle::button(settings_content, "New session", 0, 136, 464, 56);
    lv_obj_add_event_cb(session, new_session_click, LV_EVENT_CLICKED, nullptr);
    UiStyle::label(settings_content, "Wi-Fi and device settings " LV_SYMBOL_DOWN, 8, 197, &lv_font_montserrat_14, COLOR_TEXT_DIM, 448, LV_TEXT_ALIGN_CENTER);
    row = UiStyle::box(settings_content, 0, 226, 464, 104, COLOR_CARD_BG);
    lbl_wifi_status = UiStyle::label(row, "Disconnected", 14, 5, &lv_font_montserrat_16, COLOR_RED, 430);
    lbl_wifi_ssid = UiStyle::label(row, "SSID: ---", 14, 29, &lv_font_montserrat_16, COLOR_TEXT_DIM, 430);
    lv_label_set_long_mode(lbl_wifi_ssid, LV_LABEL_LONG_DOT);
    lbl_wifi_ip = UiStyle::label(row, "IP: ---", 14, 53, &lv_font_montserrat_16, COLOR_TEXT_DIM, 430);
    lv_label_set_long_mode(lbl_wifi_ip, LV_LABEL_LONG_DOT);
    lbl_wifi_signal = UiStyle::label(row, "Signal: ---", 14, 77, &lv_font_montserrat_16, COLOR_TEXT_DIM);
    btn_wifi_action = UiStyle::button(settings_content, "Reconnect", 0, 338, 228);
    lbl_wifi_action = lv_obj_get_child(btn_wifi_action, 0);
    lv_obj_add_event_cb(btn_wifi_action, wifi_action_click, LV_EVENT_CLICKED, nullptr);
    auto setup = UiStyle::button(settings_content, "Setup mode", 236, 338, 228);
    lv_obj_add_event_cb(setup, wifi_setup_click, LV_EVENT_CLICKED, nullptr);
    UiStyle::label(settings_content, "Firmware v" FIRMWARE_VERSION, 8, 398, &lv_font_montserrat_14, COLOR_TEXT_DIM);
    auto reset = UiStyle::button(settings_content, "Factory reset", 0, 424, 464, 52, Button::Danger);
    lv_obj_add_event_cb(reset, factory_reset_click, LV_EVENT_CLICKED, nullptr);
    create_nav_bar(scr_settings, 2);
}

void ui_init() {
    lv_init();

#ifdef SIMULATOR_BUILD
    lv_display_t* disp = lv_sdl_window_create(DISPLAY_WIDTH, DISPLAY_HEIGHT);
    lv_indev_t* indev = lv_sdl_mouse_create();
    (void)disp;
#else
    // Include rendering and other loop work in LVGL's elapsed time.
    lv_tick_set_cb([]() -> uint32_t { return millis(); });
    Serial.println("[DISPLAY] Initializing WT32-SC01 Plus i8080 LCD and FT6336U touch...");
    // LCD and touch share RESET. Pulse it once before either driver starts.
    pinMode(4, OUTPUT);
    digitalWrite(4, LOW);
    delay(20);
    digitalWrite(4, HIGH);
    delay(150);
    if (!tft.begin()) {
        Serial.println("[DISPLAY] Driver initialization reported a failure.");
    }
    tft.setColorDepth(16);
    tft.setRotation(1);
    tft.fillScreen(TFT_BLACK);
    tft.setBrightness(255);

    lv_display_t* disp = lv_display_create(DISPLAY_WIDTH, DISPLAY_HEIGHT);
    lv_display_set_color_format(disp, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(disp, draw_buf1, draw_buf2, sizeof(draw_buf1), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(disp, disp_flush_cb);

    lv_indev_t* indev = lv_indev_create();
    lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
    lv_indev_set_display(indev, disp);
    lv_indev_set_read_cb(indev, touchpad_read_cb);
    Serial.printf("[DISPLAY] %dx%d RGB565, backlight GPIO45, touch I2C1 GPIO6/5\n",
                  tft.width(), tft.height());
#endif

    // Poll touch independently of the display's default 33 ms refresh period.
    lv_timer_set_period(lv_indev_get_read_timer(indev), 10);

    create_dashboard_screen();
    create_graph_screen();
    create_settings_screen();

    create_setpoint_modal();
    create_meat_target_modal();
    create_confirm_modal();

    // Bind external arrays to chart series for adaptive condensing
    ui_graph_init();

    lv_screen_load(scr_dashboard);
    current_screen = Screen::DASHBOARD;

    ui_set_units(ui_state.fahrenheit);
    lv_timer_handler();
}

void ui_switch_screen(Screen screen) {
    lv_obj_t* target = screen == Screen::DASHBOARD ? scr_dashboard : screen == Screen::GRAPH ? scr_graph : scr_settings;
    if (!target) return;
    lv_screen_load(target);
    current_screen = screen;
    update_nav_highlight(screen);
    ui_refresh_alert_layout();
}
Screen ui_get_current_screen() { return current_screen; }
void ui_handler() { lv_timer_handler(); }

#else // NATIVE_BUILD && !SIMULATOR_BUILD
// Native test stubs
void ui_init() {}
void ui_switch_screen(Screen) {}
Screen ui_get_current_screen() { return Screen::DASHBOARD; }
void ui_handler() {}
void ui_set_callbacks(UiSetpointCb, UiMeatTargetCb, UiAlarmAckCb) {}
void ui_set_settings_callbacks(UiUnitsCb, UiFanModeCb, UiNewSessionCb, UiFactoryResetCb) {}
void ui_set_wifi_callback(UiWifiActionCb) {}
#endif
