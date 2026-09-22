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
static unsigned acknowledgments = 0, hardware_tests = 0, lid_resumes = 0, lid_opens = 0;
static bool requested_lid_enabled = true;
static unsigned timeout_calls = 0;
static uint16_t requested_timeout = 0;
static TouchCalibration persisted_touch;
static unsigned touch_saves = 0;
static bool touch_save_success = true;
static DamperSetup damper_fixture;
static DamperCalibration damper_saved;
static unsigned damper_moves = 0, damper_saves = 0;
static bool damper_save_success = true;
static bool damper_command(DamperSetupAction action, int value) {
    switch (action) {
        case DamperSetupAction::Begin: damper_fixture.begin(damper_saved,1472,time_ms); return true;
        case DamperSetupAction::Jog: ++damper_moves; return damper_fixture.jog(value,time_ms);
        case DamperSetupAction::MarkClosed: return damper_fixture.mark(true,time_ms);
        case DamperSetupAction::MarkOpen: return damper_fixture.mark(false,time_ms);
        case DamperSetupAction::Test: ++damper_moves; return damper_fixture.test(value,time_ms);
        case DamperSetupAction::Stop: damper_fixture.stop(); return true;
        case DamperSetupAction::Save:
            if (!damper_fixture.state().ready() || !damper_save_success) return false;
            damper_saved = damper_fixture.state().endpoints; ++damper_saves;
            damper_fixture.end(); return true;
        case DamperSetupAction::Cancel: damper_fixture.end(); return true;
        default: return false;
    }
}
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
    data->point.y = active_touch_calibration.mapY(pointer.y, DISPLAY_HEIGHT);
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
static void check_button_face(lv_obj_t* obj, unsigned& calls) {
    // Exercise real pointer dispatch, including text, selection underline,
    // corners and the outermost pixels. A center-only tap misses clipped edges.
    pump(); lv_obj_update_layout(obj);
    lv_area_t a; lv_obj_get_coords(obj, &a);
    const unsigned before = calls;
    unsigned taps = 0;
    for (int y : {a.y1, a.y1 + 4, (a.y1 + a.y2) / 2, a.y2 - 4, a.y2}) {
        for (int x : {a.x1, a.x1 + 4, (a.x1 + a.x2) / 2, a.x2 - 4, a.x2}) {
            pointer = {x, y};
            assert(lv_indev_search_obj(lv_layer_top(), &pointer) == nullptr);
            assert(lv_indev_search_obj(lv_screen_active(), &pointer) == obj);
            pressed = true; pump(10); pressed = false; pump(10);
            assert(calls == before + ++taps);
        }
    }
    // Nearby gaps must not become invisible parts of the button.
    for (auto point : {lv_point_t{a.x1 - 1, (a.y1 + a.y2) / 2},
                       lv_point_t{a.x2 + 1, (a.y1 + a.y2) / 2},
                       lv_point_t{(a.x1 + a.x2) / 2, a.y1 - 1},
                       lv_point_t{(a.x1 + a.x2) / 2, a.y2 + 1}}) {
        assert(lv_indev_search_obj(lv_screen_active(), &point) != obj);
    }
    calls = before;
}
static lv_obj_t* button(lv_obj_t* parent, const char* label) {
    for (uint32_t i = 0; i < lv_obj_get_child_count(parent); ++i) {
        auto obj = lv_obj_get_child(parent, i);
        if (lv_obj_check_type(obj, &lv_label_class) && strcmp(lv_label_get_text(obj), label) == 0) return parent;
        if (auto found = button(obj, label)) return found;
    }
    return nullptr;
}
static void tap_calibrated(lv_obj_t* obj) {
    lv_obj_update_layout(obj);
    lv_area_t a; lv_obj_get_coords(obj, &a);
    pointer = {(a.x1 + a.x2) / 2, (a.y1 + a.y2) / 2};
    if (active_touch_calibration.enabled)
        pointer.y = lroundf((pointer.y - active_touch_calibration.yOffset) / active_touch_calibration.yScale);
    pressed = true; pump(10); pressed = false; pump(20);
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
static void check_temperature_readings() {
    pump();
    lv_obj_t* values[] = {lbl_pit_temp, lbl_meat1_temp, lbl_meat2_temp};
    for (int i = 0; i < 3; ++i) {
        auto value = values[i];
        auto degree = temp_degrees[i];
        assert(lv_obj_is_visible(degree) == ui_state.connected[i]);
        lv_area_t number, suffix, card;
        lv_obj_get_coords(value, &number);
        lv_obj_get_coords(lv_obj_get_parent(value), &card);
        assert(number.x1 >= card.x1 && number.x2 <= card.x2);
        assert(number.y1 >= card.y1 && number.y2 <= card.y2);
        if (!ui_state.connected[i]) continue;
        lv_obj_get_coords(degree, &suffix);
        assert(suffix.x1 > number.x2 && suffix.x2 <= card.x2);
        assert(suffix.y1 <= number.y1 + (number.y2 - number.y1) / 4);
        assert(suffix.y1 >= card.y1 && suffix.y2 < number.y2);
        assert(!overlap(value, lv_obj_get_child(lv_obj_get_parent(value), 0)));
        if (i) assert(!overlap(degree, meat_target_captions[i - 1]));
    }
}
static void check_temperature_updates() {
    const UiState original = ui_state;
    ui_update_temps(212, 32, 14, true, true, true);
    ui_set_units(false);
    assert(strcmp(lv_label_get_text(lbl_pit_temp), "100") == 0);
    assert(strcmp(lv_label_get_text(lbl_meat1_temp), "0") == 0);
    assert(strcmp(lv_label_get_text(lbl_meat2_temp), "-10") == 0);
    check_temperature_readings();
    ui_update_alerts(3, false, false, 0); check_temperature_readings();
    ui_set_units(true); check_temperature_readings();
    ui_update_alerts(0, false, false, 0); check_temperature_readings();
    ui_update_temps(NAN, 200, 200, true, false, false);
    for (auto value : {lbl_pit_temp, lbl_meat1_temp, lbl_meat2_temp})
        assert(strcmp(lv_label_get_text(value), "---") == 0);
    check_temperature_readings();
    ui_update_temps(99, 99, 99, true, true, true); check_temperature_readings();
    const int degree_x = lv_obj_get_x(temp_degrees[1]);
    ui_update_temps(100, 100, 100, true, true, true); check_temperature_readings();
    assert(lv_obj_get_x(temp_degrees[1]) > degree_x);
    ui_set_units(original.fahrenheit);
    ui_update_temps(original.temps[0], original.temps[1], original.temps[2],
                    original.connected[0], original.connected[1], original.connected[2]);
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
    ui_damper_setup_set_callbacks(damper_command, []() { return damper_fixture.state(); });
    create_dashboard_screen(); create_graph_screen(); create_settings_screen();
    create_setpoint_modal(); create_meat_target_modal(); create_confirm_modal(); create_touch_test(input); ui_damper_setup_init(); ui_graph_init();
    ui_set_callbacks([](float v) { applied_setpoint = v; }, [](uint8_t p, float v) { applied_probe = p; applied_target = v; }, []() { ++acknowledgments; });
    ui_switch_screen(Screen::DASHBOARD); ui_set_units(true);
    ui_update_temps(225, 200, 200, true, true, true); ui_update_setpoint(300);
    ui_update_meat1_target(203); ui_update_meat2_target(165);
    ui_update_output_bars(100, 100); ui_update_cook_timer(0, 19245, 0); pump();
    assert(!overlap(lbl_meat1_temp, lbl_meat1_target));
    assert(!overlap(lbl_damper_bar, bar_damper));
    assert(!overlap(lbl_fan_bar, bar_fan));
    for (auto obj : {lbl_wifi_icon, lbl_elapsed, lbl_units, lbl_fan_bar, lbl_damper_bar, bar_fan, bar_damper, pit_card})
        assert(!overlap(btn_lid_action, obj));
    assert(lv_obj_get_height(btn_lid_action) >= 44);
    capture("dashboard");
    check_temperature_updates();

    ui_set_lid_callbacks([](bool enabled) { requested_lid_enabled=enabled; }, []() { ++lid_resumes; }, []() { ++lid_opens; });
    ui_set_lid_timeout_callback([](uint16_t seconds) { requested_timeout = seconds; ++timeout_calls; });
    ui_update_lid_detection(false,false,0);
    check_button_face(btn_lid_action, lid_opens);
    tap(btn_lid_action); assert(lid_opens==1); // Auto Off does not disable manual control.
    ui_update_output_bars(0,0);
    ui_update_lid_detection(false,true,120,true); ui_update_alerts(0,true,false,0); pump();
    assert(strcmp(lv_label_get_text(lv_obj_get_child(btn_lid_action,0)),"Close lid")==0);
    assert(!lv_obj_is_visible(alert_banner) && lv_obj_is_visible(lbl_lid_compact));
    assert(lv_obj_get_height(pit_card) == 190 && lv_obj_get_height(meat_cards[1]) == 91);
    for (auto obj : {btn_lid_action, lbl_elapsed, lbl_units, lbl_damper_bar}) assert(!overlap(lbl_lid_compact, obj));
    assert(!overlap(btn_lid_action,lbl_elapsed)); capture("manual-lid-open");
    check_button_face(btn_lid_action, lid_resumes);
    tap(btn_lid_action); assert(lid_resumes==1);
    ui_update_lid_detection(true,false,0); ui_update_alerts(0,false,false,0);
    ui_update_temps(225,NAN,NAN,true,false,false); ui_update_alerts(0,false,false,0);
    assert(!lv_obj_is_visible(alert_banner)); // Optional meat readings do not create a UI error.
    assert(strcmp(lv_label_get_text(lbl_meat1_temp),"---")==0);
    capture("optional-meat-probes");
    ui_update_temps(225,200,200,true,true,true);
    lid_resumes=0;
    ui_update_lid_detection(true,true,83); ui_update_alerts(0,true,false,0); pump();
    assert(!lv_obj_is_visible(alert_banner) && lv_obj_is_visible(lbl_lid_compact));
    assert(!button(lv_layer_top(), "Resume now"));
    capture("lid-open");
    ui_switch_screen(Screen::GRAPH); pump();
    assert(lv_obj_is_visible(lbl_lid_compact) && lv_obj_get_height(chart_temps) == 168);
    assert(!overlap(lbl_lid_compact, lbl_graph_title) && !overlap(lbl_lid_compact, lbl_graph_span));
    capture("lid-graph");
    ui_switch_screen(Screen::DASHBOARD);
    tap(btn_lid_action); assert(lid_resumes==1 && acknowledgments==0);
    ui_update_lid_detection(true,false,0); ui_update_alerts(0,false,false,0);
    assert(!lv_obj_is_visible(alert_banner));
    assert(!lv_obj_is_visible(lbl_lid_compact));
    ui_switch_screen(Screen::SETTINGS);
    lv_obj_scroll_to_view_recursive(btn_lid_toggle,LV_ANIM_OFF); pump();
    tap(btn_lid_toggle); assert(!requested_lid_enabled);
    ui_update_lid_detection(false,false,0);
    assert(strcmp(lv_label_get_text(lv_obj_get_child(btn_lid_toggle,0)),"Off")==0);
    tap(btn_lid_toggle); assert(requested_lid_enabled);
    ui_update_lid_detection(true,true,83); ui_update_alerts(3,true,false,0);
    assert(lv_obj_is_visible(btn_alert_ack));
    pump(); assert(lv_obj_get_height(settings_content) == 158);
    assert(!button(scr_settings, "Touch test") && !button(scr_settings, "Open lid") && !button(scr_settings, "Close lid"));
    pump(); lv_obj_scroll_to_view_recursive(btn_lid_timeout_plus,LV_ANIM_OFF); pump(); capture("lid-settings");
    check_button_face(btn_lid_timeout_plus, timeout_calls);
    check_button_face(btn_lid_timeout_minus, timeout_calls);
    tap(btn_lid_timeout_plus); assert(requested_timeout == 150);
    ui_update_lid_detection(true,true,113,false,150);
    assert(strcmp(lv_label_get_text(lbl_lid_timeout),"2:30")==0);
    tap(btn_lid_timeout_minus); assert(requested_timeout == 120);
    ui_update_lid_detection(false,true,80,true,30); ui_update_alerts(0,true,false,1); pump();
    assert(strstr(lv_label_get_text(lbl_alert_text),"Pit") && !lv_obj_is_visible(btn_alert_ack));
    assert(lv_obj_has_state(btn_lid_timeout_minus,LV_STATE_DISABLED));
    ui_update_lid_detection(false,false,0,false,600); ui_update_alerts(0,false,false,0); pump();
    assert(lv_obj_has_state(btn_lid_timeout_plus,LV_STATE_DISABLED));
    assert(strcmp(lv_label_get_text(lbl_lid_timeout),"10:00")==0);
    // Dashboard remains the sole manual lid action.
    ui_switch_screen(Screen::DASHBOARD); tap(btn_lid_action); assert(lid_opens==2);
    ui_update_lid_detection(true,false,0); ui_update_alerts(0,false,false,0);
    lv_obj_scroll_to_y(settings_content,0,LV_ANIM_OFF); ui_switch_screen(Screen::DASHBOARD);
    ui_update_output_bars(100,100);


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
    ui_update_temps(NAN, NAN, NAN, false, false, false);
    ui_update_alerts(0, false, false, 7); check_temperature_readings(); capture("probe-errors");
    ui_update_alerts(0, false, false, 0);
    ui_update_temps(225, 200, 200, true, true, true);

    ui_switch_screen(Screen::SETTINGS);
    ui_update_wifi_info({true, false, "Example-network-with-a-long-name", "192.168.100.100", -62});
    capture("settings");
    tap(btn_units_c); assert(!ui_state.fahrenheit && lv_obj_has_state(btn_units_c, LV_STATE_CHECKED));
    tap(btn_units_f); assert(ui_state.fahrenheit);
    // The physical touch diagnostic reports input coordinates unchanged, leaves
    // the last point visible, and intercepts all taps above the normal UI.
    const UiState before_touch_test = ui_state;
    show_touch_test(nullptr); pump();
    assert(lv_obj_is_visible(touch_test) && touch_test_taps == 0);
    for (auto point : {lv_point_t{48,100}, lv_point_t{432,100}, lv_point_t{240,184},
                       lv_point_t{48,236}, lv_point_t{432,236}}) {
        const auto taps = touch_test_taps;
        pointer = point; pressed = true; pump(10); pressed = false; pump(10);
        assert(touch_test_taps == taps + 1);
        lv_obj_update_layout(touch_test);
        assert(lv_obj_get_x(touch_dot) + 6 == point.x && lv_obj_get_y(touch_dot) + 6 == point.y);
        assert(lv_obj_is_visible(touch_dot));
        char expected[64]; snprintf(expected, sizeof(expected), "Touch %u:  X %ld  Y %ld", touch_test_taps, (long)point.x, (long)point.y);
        assert(strcmp(lv_label_get_text(touch_coordinates), expected) == 0);
        if (point.x == 240) capture("touch-test-offset");
    }
    assert(ui_state.setpoint == before_touch_test.setpoint && ui_state.fahrenheit == before_touch_test.fahrenheit);
    tap(button(touch_test, "Close test")); assert(!lv_obj_is_visible(touch_test)); pump();
    show_touch_test(nullptr); pump();
    assert(lv_obj_is_visible(touch_test) && !lv_obj_is_visible(touch_dot) && touch_test_taps == 0);
    // Timeout also works with a held finger and cannot click through to Settings.
    pointer = {420, 70}; pressed = true; pump(60010);
    assert(!lv_obj_is_visible(touch_test));
    pressed = false; pump(); assert(ui_state.fahrenheit == before_touch_test.fahrenheit);
    // A device-specific correction is tried without saving; Cancel and timeout
    // roll it back. Use unbounded sensor coordinates before the production map.
    TouchCalibration candidate; candidate.yScale = .85704777f; candidate.yOffset = 15.216774f;
    ui_set_touch_calibration(candidate);
    ui_set_touch_calibration_callback([](const TouchCalibration& c) {
        if (!touch_save_success) return false;
        persisted_touch = c; ++touch_saves; return true;
    });
    show_touch_test(nullptr); pump();
    tap(button(touch_test, "Try calibration")); pump();
    assert(touch_calibration_preview && active_touch_calibration.enabled && touch_saves == 0);
    for (auto pair : {lv_point_t{98,99}, lv_point_t{101,102}, lv_point_t{167,158},
                      lv_point_t{257,235}, lv_point_t{259,237}}) {
        pointer = {48,pair.x}; pressed = true; pump(10); pressed = false; pump(10);
        lv_obj_update_layout(touch_test);
        assert(lv_obj_get_x(touch_dot) + 6 == 48 && lv_obj_get_y(touch_dot) + 6 == pair.y);
    }
    capture("touch-calibration-preview");
    tap_calibrated(button(touch_test, "Cancel")); pump();
    assert(!active_touch_calibration.enabled && !lv_obj_is_visible(touch_test) && touch_saves == 0);
    show_touch_test(nullptr); pump(); tap(button(touch_test, "Try calibration")); pump(60010);
    assert(!active_touch_calibration.enabled && !lv_obj_is_visible(touch_test) && touch_saves == 0);
    show_touch_test(nullptr); pump(); tap(button(touch_test, "Try calibration")); pump();
    touch_save_success = false;
    tap_calibrated(button(touch_test, "Save calibration"));
    assert(touch_calibration_preview && touch_saves == 0 && !saved_touch_calibration.enabled);
    assert(strcmp(lv_label_get_text(touch_coordinates), "Could not save. Try again.") == 0);
    touch_save_success = true;
    tap_calibrated(button(touch_test, "Save calibration"));
    assert(!touch_calibration_preview && persisted_touch.enabled && touch_saves == 1);
    tap_calibrated(button(touch_test, "Close test")); pump();
    assert(active_touch_calibration.enabled);
    // A raw Y above 319 must still reach a bottom navigation button.
    tap_calibrated(nav_btns[2][0]); assert(ui_get_current_screen() == Screen::DASHBOARD);
    tap_calibrated(nav_btns[0][2]); assert(ui_get_current_screen() == Screen::SETTINGS);
    show_touch_test(nullptr); pump();
    tap_calibrated(button(touch_test, "Reset calibration"));
    assert(!active_touch_calibration.enabled && !persisted_touch.enabled && touch_saves == 2);
    tap(button(touch_test, "Close test")); pump();
    ui_set_touch_calibration({}); ui_set_touch_calibration_callback(nullptr);
    // Damper setup begins without moving, but the saved-position tests are usable
    // immediately. Only saving a new calibration requires both endpoints.
    auto damper_entry = button(scr_settings, "Damper setup");
    lv_obj_scroll_to_view_recursive(damper_entry,LV_ANIM_OFF); pump(); tap(damper_entry); pump();
    assert(damper_fixture.state().active && damper_moves == 0);
    auto damper_save = button(lv_layer_sys(), "Save & exit");
    assert(lv_obj_has_state(damper_save, LV_STATE_DISABLED));
    capture("damper-setup");
    for (const char* label : {"0% Closed", "50%", "100% Open"})
        assert(!lv_obj_has_state(button(lv_layer_sys(),label),LV_STATE_DISABLED));
    tap(button(lv_layer_sys(), "0% Closed")); assert(damper_fixture.state().pulseUs == 544);
    tap(button(lv_layer_sys(), "50%")); assert(damper_fixture.state().pulseUs == 1008);
    tap(button(lv_layer_sys(), "100% Open")); assert(damper_fixture.state().pulseUs == 1472);
    assert(!damper_fixture.state().closedMarked && !damper_fixture.state().openMarked && damper_saves == 0);
    tap(button(lv_layer_sys(), "Set closed")); tap(button(lv_layer_sys(), "Set open"));
    assert(!damper_fixture.state().ready() && lv_obj_has_state(damper_save, LV_STATE_DISABLED));
    tap(button(lv_layer_sys(), "100% Open")); assert(damper_fixture.state().pulseUs == 1472);
    for (int i=0; i<4; ++i) tap(button(lv_layer_sys(), "-50"));
    tap(button(lv_layer_sys(), "Open: 1472 us"));
    assert(damper_fixture.state().ready() && !lv_obj_has_state(damper_save, LV_STATE_DISABLED));
    tap(button(lv_layer_sys(), "0% Closed")); assert(damper_fixture.state().pulseUs == 1472);
    tap(button(lv_layer_sys(), "50%")); assert(damper_fixture.state().pulseUs == 1372);
    tap(button(lv_layer_sys(), "100% Open")); assert(damper_fixture.state().pulseUs == 1272);
    capture("damper-reversed");
    tap(button(lv_layer_sys(), "Stop signal")); assert(damper_fixture.state().stopped);
    tap(button(lv_layer_sys(), "50%")); assert(!damper_fixture.state().stopped && damper_fixture.state().pulseUs == 1372);
    assert(damper_fixture.timeout(time_ms + DamperSetup::IDLE_MS)); pump();
    assert(lv_obj_is_visible(damper_save) && damper_fixture.state().active);
    tap(button(lv_layer_sys(), "0% Closed")); assert(!damper_fixture.state().stopped && damper_fixture.state().pulseUs == 1472);
    damper_save_success = false; tap(damper_save);
    assert(damper_fixture.state().active && damper_saves == 0);
    damper_save_success = true; tap(damper_save);
    assert(!damper_fixture.state().active && !lv_obj_is_visible(damper_save) && damper_saves == 1);
    assert(damper_saved.closedUs == 1472 && damper_saved.openUs == 1272);
    pump(); tap(damper_entry); pump(); tap(button(lv_layer_sys(), "+50"));
    tap(button(lv_layer_sys(), "Cancel"));
    assert(!damper_fixture.state().active && damper_saves == 1 && damper_saved.closedUs == 1472);
    lv_obj_scroll_to_y(settings_content,0,LV_ANIM_OFF); pump();
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
