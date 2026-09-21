#include "ui_damper_setup.h"
#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)
#include <lvgl.h>
#include "ui_styles.h"

static UiDamperCommandCb command_cb = nullptr;
static UiDamperStatusCb status_cb = nullptr;
static lv_obj_t *panel, *position_text, *hint, *closed_button, *open_button, *save_button;
static lv_obj_t* test_buttons[3];
static lv_timer_t* poll_timer;
static bool save_error = false;

void ui_damper_setup_set_callbacks(UiDamperCommandCb command, UiDamperStatusCb status) {
    command_cb = command; status_cb = status;
}
bool ui_damper_setup_available() { return command_cb && status_cb; }
static void enabled(lv_obj_t* obj, bool yes) {
    if (yes) lv_obj_remove_state(obj, LV_STATE_DISABLED);
    else lv_obj_add_state(obj, LV_STATE_DISABLED);
}
static void refresh() {
    if (!status_cb) return;
    const auto state = status_cb();
    UiStyle::text_fmt(position_text, "Servo command: %u us", state.pulseUs);
    UiStyle::text_fmt(lv_obj_get_child(closed_button, 0), state.closedMarked ? "Closed: %u us" : "Set closed", state.endpoints.closedUs);
    UiStyle::text_fmt(lv_obj_get_child(open_button, 0), state.openMarked ? "Open: %u us" : "Set open", state.endpoints.openUs);
    UiStyle::selected(closed_button, state.closedMarked);
    UiStyle::selected(open_button, state.openMarked);
    enabled(closed_button, !state.stopped); enabled(open_button, !state.stopped);
    for (auto b : test_buttons) enabled(b, state.ready());
    enabled(save_button, state.ready());
    lv_label_set_text(hint, save_error ? "Could not save. Your old endpoints are unchanged." :
        state.stopped ? "Servo signal off. Tap an adjustment to move again." :
        state.closedMarked && state.openMarked && !state.ready() ? "Endpoints are too close. Adjust and mark one again." :
        "Move gently. Mark both ends, then test 0 / 50 / 100%.");
}
static void send(DamperSetupAction action, int value = 0) {
    if (!ui_damper_setup_available()) return;
    save_error = false;
    if (!command_cb(action, value)) {
        save_error = action == DamperSetupAction::Save;
        refresh(); return;
    }
    if (action == DamperSetupAction::Save || action == DamperSetupAction::Cancel) {
        lv_obj_add_flag(panel, LV_OBJ_FLAG_HIDDEN); lv_timer_pause(poll_timer);
        if (auto input = lv_indev_active()) lv_indev_wait_release(input);
    } else refresh();
}
static lv_obj_t* action_button(const char* text, int x, int y, int w, lv_event_cb_t cb,
                               void* data = nullptr, UiStyle::Button role = UiStyle::Button::Secondary) {
    auto b = UiStyle::button(panel, text, x, y, w, 44, role, &lv_font_montserrat_16);
    lv_obj_add_event_cb(b, cb, LV_EVENT_CLICKED, data); return b;
}
void ui_damper_setup_init() {
    panel = UiStyle::box(lv_layer_sys(), 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOR_BG, 0);
    lv_obj_add_flag(panel, LV_OBJ_FLAG_HIDDEN);
    UiStyle::label(panel, "Damper setup", 12, 6, &lv_font_montserrat_24);
    action_button("Stop signal", 344, 0, 128, [](lv_event_t*) { send(DamperSetupAction::Stop); }, nullptr, UiStyle::Button::Danger);
    UiStyle::label(panel, "Blower off. Exit returns to automatic control.", 12, 42, &lv_font_montserrat_14, COLOR_TEXT_DIM);
    position_text = UiStyle::label(panel, "", 12, 64, &lv_font_montserrat_18, COLOR_ORANGE, 456, LV_TEXT_ALIGN_CENTER);
    hint = UiStyle::label(panel, "", 12, 88, &lv_font_montserrat_14, COLOR_TEXT_DIM, 456, LV_TEXT_ALIGN_CENTER);
    const int deltas[] = {-50, -10, 10, 50};
    const char* labels[] = {"-50", "-10", "+10", "+50"};
    for (int i = 0; i < 4; ++i)
        action_button(labels[i], 8 + i * 118, 110, 110, [](lv_event_t* e) {
            send(DamperSetupAction::Jog, int(intptr_t(lv_event_get_user_data(e))));
        }, reinterpret_cast<void*>(intptr_t(deltas[i])));
    closed_button = action_button("Set closed", 8, 162, 228, [](lv_event_t*) { send(DamperSetupAction::MarkClosed); });
    open_button = action_button("Set open", 244, 162, 228, [](lv_event_t*) { send(DamperSetupAction::MarkOpen); });
    const char* positions[] = {"0% Closed", "50%", "100% Open"};
    for (int i = 0; i < 3; ++i)
        test_buttons[i] = action_button(positions[i], 8 + i * 157, 214, 150, [](lv_event_t* e) {
            send(DamperSetupAction::Test, int(intptr_t(lv_event_get_user_data(e))));
        }, reinterpret_cast<void*>(intptr_t(i * 50)));
    save_button = action_button("Save & exit", 8, 268, 228, [](lv_event_t*) { send(DamperSetupAction::Save); }, nullptr, UiStyle::Button::Primary);
    action_button("Cancel", 244, 268, 228, [](lv_event_t*) { send(DamperSetupAction::Cancel); });
    poll_timer = lv_timer_create([](lv_timer_t*) { refresh(); }, 250, nullptr);
    lv_timer_pause(poll_timer);
}
void ui_damper_setup_show() {
    if (!panel || !ui_damper_setup_available() || !command_cb(DamperSetupAction::Begin, 0)) return;
    save_error = false; refresh();
    lv_obj_remove_flag(panel, LV_OBJ_FLAG_HIDDEN); lv_obj_move_foreground(panel);
    lv_timer_reset(poll_timer); lv_timer_resume(poll_timer);
    if (auto input = lv_indev_active()) lv_indev_wait_release(input);
}
#else
void ui_damper_setup_set_callbacks(UiDamperCommandCb, UiDamperStatusCb) {}
bool ui_damper_setup_available() { return false; }
void ui_damper_setup_init() {}
void ui_damper_setup_show() {}
#endif
