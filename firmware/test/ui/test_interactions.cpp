// Real LVGL pointer events against production widgets. Optional RGB565 captures:
// PITCLAW_UI_CAPTURE_DIR=/absolute/directory /tmp/pitclaw_ui_interactions
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "../../src/display/ui_init.cpp"
#define cb_units wizard_units_callback
#include "../../src/display/ui_setup_wizard.cpp"
#undef cb_units
#include "../../src/display/graph_history.h"

static uint16_t draw_pixels[480 * 40];
static unsigned char frame_pixels[480 * 320 * 3];
static uint32_t time_ms = 1;
static bool pressed = false;
static lv_point_t pointer = {};
static float applied_setpoint = -1, applied_target = -1;
static uint8_t applied_probe = 0;
static unsigned acknowledgments = 0, hardware_tests = 0;
static void flush(lv_display_t* disp, const lv_area_t* area, uint8_t* data) {
    auto pixels = reinterpret_cast<uint16_t*>(data);
    for (int y = area->y1; y <= area->y2; ++y) for (int x = area->x1; x <= area->x2; ++x) {
        uint16_t v = *pixels++; size_t n = (y * 480 + x) * 3;
        frame_pixels[n] = ((v >> 11) & 31) * 255 / 31;
        frame_pixels[n + 1] = ((v >> 5) & 63) * 255 / 63;
        frame_pixels[n + 2] = (v & 31) * 255 / 31;
    }
    lv_display_flush_ready(disp);
}
static void touch(lv_indev_t*, lv_indev_data_t* data) {
    data->point = pointer; data->state = pressed ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
}
static void pump(unsigned duration = 100) {
    for (unsigned i = 0; i < duration; i += 10) { time_ms += 10; lv_timer_handler(); }
}
static void tap(lv_obj_t* obj, unsigned hold = 10) {
    assert(obj);
    lv_obj_update_layout(lv_screen_active()); lv_obj_update_layout(lv_layer_top());
    lv_area_t a; lv_obj_get_coords(obj, &a);
    pointer = {(a.x1 + a.x2) / 2, (a.y1 + a.y2) / 2};
    pressed = true; pump(hold); pressed = false; pump(10);
}
static lv_obj_t* button(lv_obj_t* parent, const char* label) {
    for (uint32_t i = 0; i < lv_obj_get_child_count(parent); ++i) {
        auto obj = lv_obj_get_child(parent, i);
        if (lv_obj_check_type(obj, &lv_label_class) && strcmp(lv_label_get_text(obj), label) == 0) return parent;
        if (auto found = button(obj, label)) return found;
    }
    return nullptr;
}
static void capture(const char* name) {
    const char* dir = getenv("PITCLAW_UI_CAPTURE_DIR"); if (!dir) return;
    lv_obj_invalidate(lv_screen_active()); pump();
    char path[512]; snprintf(path, sizeof(path), "%s/%s.ppm", dir, name);
    FILE* f = fopen(path, "wb"); assert(f);
    fprintf(f, "P6\n480 320\n255\n"); fwrite(frame_pixels, 1, sizeof(frame_pixels), f); fclose(f);
}
static bool overlap(lv_obj_t* first, lv_obj_t* second) {
    lv_area_t a, b; lv_obj_get_coords(first, &a); lv_obj_get_coords(second, &b);
    return a.x1 <= b.x2 && b.x1 <= a.x2 && a.y1 <= b.y2 && b.y1 <= a.y2;
}
int main() {
    lv_init(); lv_tick_set_cb([]() -> uint32_t { return time_ms; });
    auto display = lv_display_create(480, 320);
    lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(display, draw_pixels, nullptr, sizeof(draw_pixels), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(display, flush);
    auto input = lv_indev_create(); lv_indev_set_type(input, LV_INDEV_TYPE_POINTER);
    lv_indev_set_display(input, display); lv_indev_set_read_cb(input, touch);
    lv_timer_set_period(lv_indev_get_read_timer(input), 10);
    create_dashboard_screen(); create_graph_screen(); create_settings_screen();
    create_setpoint_modal(); create_meat_target_modal(); create_confirm_modal(); ui_graph_init();
    ui_set_callbacks([](float v) { applied_setpoint = v; }, [](uint8_t p, float v) { applied_probe = p; applied_target = v; }, []() { ++acknowledgments; });
    ui_switch_screen(Screen::DASHBOARD); ui_set_units(true);
    ui_update_temps(225, 200, 200, true, true, true); ui_update_setpoint(300);
    ui_update_meat1_target(203); ui_update_meat2_target(165);
    ui_update_output_bars(100, 100); ui_update_cook_timer(0, 19245, 0); pump();
    assert(!overlap(lbl_meat1_temp, lbl_meat1_target));
    assert(!overlap(lbl_damper_bar, bar_damper));
    capture("dashboard");

    // Opening/accepting reflects the current committed value. Cancel discards a draft.
    tap(pit_card); assert(modal_open(modal_setpoint));
    assert(strcmp(lv_label_get_text(lbl_modal_sp_value), "300\xC2\xB0" "F") == 0);
    tap(button(modal_setpoint, "Apply")); assert(applied_setpoint == 300);
    tap(pit_card); tap(button(modal_setpoint, "+1")); tap(button(modal_setpoint, "Cancel"));
    tap(pit_card); assert(modal_sp_value == 300); tap(button(modal_setpoint, "Cancel"));
    tap(pit_card); tap(button(modal_setpoint, "+1"), 1100);
    assert(modal_sp_value >= 310 && modal_sp_value <= 500);
    assert(applied_setpoint == 300); tap(button(modal_setpoint, "Cancel"));
    ui_update_setpoint(500); tap(pit_card); pump();
    tap(button(modal_setpoint, "+1")); assert(modal_sp_value == 500);
    assert(!overlap(lbl_modal_sp_value, button(modal_setpoint, "+1")));
    assert(!overlap(lbl_modal_sp_value, button(modal_setpoint, "-1")));
    capture("pit-editor"); tap(button(modal_setpoint, "Cancel"));

    // Probe targets are independent and arbitrary integer values remain reachable.
    tap(meat_cards[0]); assert(modal_meat_value == 203); tap(button(modal_meat, "Set"));
    assert(applied_probe == 1 && applied_target == 203);
    tap(meat_cards[1]); assert(modal_meat_value == 165); capture("meat-editor");
    tap(button(modal_meat, "+1")); tap(button(modal_meat, "Set"));
    assert(applied_probe == 2 && applied_target == 166);
    tap(meat_cards[0]); assert(modal_meat_value == 203); tap(button(modal_meat, "Clear"));
    assert(ui_state.targets[0] == 0 && applied_target == 0);
    tap(meat_cards[1]); assert(modal_meat_value == 166); tap(button(modal_meat, "Cancel"));

    // A unit change converts labels and increments, but preserves the canonical cook.
    ui_update_setpoint(212); ui_update_meat1_target(203); ui_set_units(false);
    assert(ui_state.setpoint == 212 && ui_state.targets[0] == 203);
    tap(pit_card); assert(strcmp(lv_label_get_text(lbl_modal_sp_value), "100\xC2\xB0" "C") == 0);
    tap(button(modal_setpoint, "Apply")); assert(applied_setpoint == 212);
    tap(pit_card); tap(button(modal_setpoint, "+1")); tap(button(modal_setpoint, "Apply"));
    assert(fabsf(applied_setpoint - 213.8f) < 0.01f);
    tap(pit_card); capture("celsius-editor"); tap(button(modal_setpoint, "Cancel"));
    ui_set_units(true);

    // History retains seconds through repeated condensing and re-renders old points in C.
    ui_graph_clear();
    for (int i = 0; i < 1000; ++i) ui_graph_add_point(212, 165, 170, 225, false, false, false, i * 10);
    ui_set_units(false);
    assert(lv_chart_get_series_y_array(chart_temps, ser_pit)[0] == 100);
    auto x = lv_chart_get_series_x_array(chart_temps, ser_pit);
    unsigned n = lv_chart_get_point_count(chart_temps);
    assert(x[n - 1] == 9990 && n <= GRAPH_HISTORY_SIZE);
    for (unsigned i = 1; i < n; ++i) assert(x[i] >= x[i - 1]);
    ui_set_units(true); assert(lv_chart_get_series_y_array(chart_temps, ser_pit)[0] == 212);
    ui_graph_clear();
    for (int i = 0; i <= 180; ++i) ui_graph_add_point(220 + 7 * sin(i / 12.), 95 + i * .4, 90 + i * .35, 225, false, false, false, i * 5);
    ui_switch_screen(Screen::GRAPH); capture("graph");
    pump();
    for (int i = 1; i < 5; ++i) assert(!overlap(graph_y_labels[i - 1], graph_y_labels[i]));
    assert(lv_obj_get_y(graph_y_labels[4]) == 199);
    ui_update_alerts(3, false, false, 0); pump();
    assert(lv_obj_is_visible(alert_banner)); assert(!overlap(chart_temps, alert_banner));
    assert(lv_obj_get_y(graph_y_labels[4]) == 143);
    for (auto label : graph_y_labels) assert(!overlap(label, alert_banner));
    capture("graph-alarm");
    ui_switch_screen(Screen::SETTINGS); pump();
    assert(lv_obj_is_visible(alert_banner)); assert(!overlap(settings_content, alert_banner));
    ui_switch_screen(Screen::DASHBOARD); pump();
    assert(!overlap(pit_card, alert_banner)); assert(!overlap(meat_cards[1], alert_banner));
    capture("alarm");
    tap(pit_card); pump(); assert(modal_open(modal_setpoint));
    assert(lv_obj_is_visible(alert_banner)); assert(!overlap(lv_obj_get_child(modal_setpoint, 0), alert_banner));
    capture("editor-alarm"); tap(btn_alert_ack); assert(acknowledgments == 1);
    tap(button(modal_setpoint, "Cancel")); ui_update_alerts(0, false, false, 0);
    ui_update_alerts(0, false, false, 7); capture("probe-errors"); ui_update_alerts(0, false, false, 0);

    ui_switch_screen(Screen::SETTINGS);
    ui_update_wifi_info({true, false, "Example-network-with-a-long-name", "192.168.100.100", -62});
    capture("settings");
    tap(btn_units_c); assert(!ui_state.fahrenheit && lv_obj_has_state(btn_units_c, LV_STATE_CHECKED));
    tap(btn_units_f); assert(ui_state.fahrenheit);
    // Dragging Settings scrolls content without changing a mode or losing navigation.
    pointer = {110, 234}; pressed = true; pump(10);
    for (int i = 0; i < 12; ++i) { pointer.y -= 10; pump(10); }
    pressed = false; pump(300);
    assert(lv_obj_get_scroll_y(settings_content) > 0);
    lv_obj_scroll_to_y(settings_content, 1000, LV_ANIM_OFF); capture("settings-more");
    tap(button(settings_content, "Factory reset")); capture("confirmation"); tap(button(modal_confirm, "Cancel"));

    ui_wizard_init(); go_to_step(1); capture("wizard-units");
    tap(wiz_units_buttons[1]); assert(wizard_step == 2 && !ui_state.fahrenheit);
    ui_wizard_update_wifi({false, true, AP_SSID, "192.168.4.1", 0}); capture("wizard-wifi");
    tap(button(wiz_screens[2], LV_SYMBOL_LEFT " Back")); assert(wizard_step == 1);
    assert(lv_obj_has_state(wiz_units_buttons[1], LV_STATE_CHECKED));
    go_to_step(3); ui_wizard_update_probes(212, 165, 170, true, true, true);
    assert(strcmp(lv_label_get_text(lbl_wiz_pit), "100\xC2\xB0" "C") == 0); capture("wizard-probes");
    go_to_step(4); ui_wizard_set_callbacks([]() { ++hardware_tests; }, nullptr, nullptr, nullptr, nullptr);
    tap(wiz_test_buttons[0]); assert(hardware_tests == 1); capture("wizard-test-running");
    assert(lv_obj_has_state(wiz_test_buttons[1], LV_STATE_DISABLED));
    pump(1300); assert(!lv_obj_has_state(wiz_test_buttons[1], LV_STATE_DISABLED)); capture("wizard-hardware");
    printf("Editor values, cancel, independent probes, units, graph history, shared alarms, settings scrolling and wizard navigation passed.\n");
}
