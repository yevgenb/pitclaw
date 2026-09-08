#include "ui_setup_wizard.h"

#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)

#include <lvgl.h>
#include <stdio.h>
#include <cstring>

#include "ui_colors.h"
#include "ui_styles.h"
#include "ui_state.h"

// --------------------------------------------------------------------------
// State
// --------------------------------------------------------------------------

static bool wizard_active = false;
static uint8_t wizard_step = 0;  // 0=welcome, 1=units, 2=wifi, 3=probes, 4=hwtest, 5=done

// Wizard screens (one per step)
static lv_obj_t* wiz_screens[6] = { nullptr };
static lv_obj_t* wiz_units_buttons[2] = {};
static lv_obj_t* wiz_test_buttons[3] = {};
static lv_obj_t* lbl_test_status = nullptr;
static lv_timer_t* test_timer = nullptr;

static lv_obj_t* lbl_wiz_wifi_title = nullptr;
static lv_obj_t* lbl_wiz_wifi_instructions = nullptr;
static lv_obj_t* wiz_wifi_qr = nullptr;
static lv_obj_t* wiz_wifi_qr_frame = nullptr;
static char wiz_wifi_qr_data[128] = {};

// Probe check labels (step 3)
static lv_obj_t* lbl_wiz_pit   = nullptr;
static lv_obj_t* lbl_wiz_meat1 = nullptr;
static lv_obj_t* lbl_wiz_meat2 = nullptr;

// Callbacks
static WizardFanTestCb    cb_fan_test    = nullptr;
static WizardServoTestCb  cb_servo_test  = nullptr;
static WizardBuzzerTestCb cb_buzzer_test = nullptr;
static WizardUnitsCb      cb_units       = nullptr;
static WizardCompleteCb   cb_complete    = nullptr;

// --------------------------------------------------------------------------
// Forward declarations
// --------------------------------------------------------------------------

static void create_step_welcome();
static void create_step_units();
static void create_step_wifi();
static void create_step_probes();
static void create_step_hwtest();
static void create_step_done();
static void go_to_step(uint8_t step);

// --------------------------------------------------------------------------
// Navigation helpers
// --------------------------------------------------------------------------

static void next_btn_cb(lv_event_t* e) {
    (void)e;
    if (wizard_step < 5) {
        go_to_step(wizard_step + 1);
    }
}

static void go_to_step(uint8_t step) {
    if (step > 5) step = 5;
    wizard_step = step;

    if (step == 5) {
        // Done step — mark wizard complete
        wizard_active = false;
        if (cb_complete) cb_complete();
    }

    if (step == 1) {
        UiStyle::selected(wiz_units_buttons[0], ui_state.fahrenheit);
        UiStyle::selected(wiz_units_buttons[1], !ui_state.fahrenheit);
    }
    if (wiz_screens[step]) {
        lv_screen_load(wiz_screens[step]);
        ui_refresh_alert_layout();
    }
}

// --------------------------------------------------------------------------
// Helper: create a "Next" button at the bottom of a screen
// --------------------------------------------------------------------------

static void back_btn_cb(lv_event_t*) {
    if (wizard_step > 0) go_to_step(wizard_step - 1);
}
static void add_back_button(lv_obj_t* parent) {
    auto back = UiStyle::button(parent, LV_SYMBOL_LEFT " Back", 16, 256, 212, 56);
    lv_obj_add_event_cb(back, back_btn_cb, LV_EVENT_CLICKED, nullptr);
}
static lv_obj_t* add_next_button(lv_obj_t* parent, const char* text) {
    bool welcome = parent == wiz_screens[0];
    if (!welcome) add_back_button(parent);
    auto btn = UiStyle::button(parent, text, welcome ? 134 : 252, 256, 212, 56, UiStyle::Button::Primary);
    lv_obj_add_event_cb(btn, next_btn_cb, LV_EVENT_CLICKED, nullptr);
    return btn;
}

// --------------------------------------------------------------------------
// Step 0: Welcome
// --------------------------------------------------------------------------

static void create_step_welcome() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[0] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Pit Claw");
    lv_obj_set_style_text_color(lbl, COLOR_ORANGE, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_36, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, -40);

    lbl = lv_label_create(scr);
    lv_label_set_text_fmt(lbl, "v%s", FIRMWARE_VERSION);
    lv_obj_set_style_text_color(lbl, COLOR_TEXT_DIM, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_18, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, 10);

    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Let's get set up!");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_16, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, 50);

    add_next_button(scr, "Start");
}

// --------------------------------------------------------------------------
// Step 1: Units
// --------------------------------------------------------------------------

static void units_f_cb(lv_event_t* e) {
    (void)e;
    ui_set_units(true);
    if (cb_units) cb_units(true);
    go_to_step(2);
}

static void units_c_cb(lv_event_t* e) {
    (void)e;
    ui_set_units(false);
    if (cb_units) cb_units(false);
    go_to_step(2);
}

static void create_step_units() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[1] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Temperature Units");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 30);

    wiz_units_buttons[0] = UiStyle::button(scr, "\xC2\xB0" "F", 50, 140, 180, 80, UiStyle::Button::Secondary, &lv_font_montserrat_36);
    wiz_units_buttons[1] = UiStyle::button(scr, "\xC2\xB0" "C", 250, 140, 180, 80, UiStyle::Button::Secondary, &lv_font_montserrat_36);
    lv_obj_add_event_cb(wiz_units_buttons[0], units_f_cb, LV_EVENT_CLICKED, nullptr);
    lv_obj_add_event_cb(wiz_units_buttons[1], units_c_cb, LV_EVENT_CLICKED, nullptr);
    add_back_button(scr);
}

// --------------------------------------------------------------------------
// Step 2: Wi-Fi (live connection state, QR code + instructions)
// --------------------------------------------------------------------------

static void create_step_wifi() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[2] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Wi-Fi Setup");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 10);
    lbl_wiz_wifi_title = lbl;

    // Use a white quiet zone and dark modules for reliable phone scanning.
    // The caller supplies the live state before any join code is displayed.
    wiz_wifi_qr_frame = lv_obj_create(scr);
    lv_obj_set_size(wiz_wifi_qr_frame, 156, 156);
    lv_obj_align(wiz_wifi_qr_frame, LV_ALIGN_LEFT_MID, 16, -8);
    lv_obj_set_style_bg_color(wiz_wifi_qr_frame, lv_color_white(), 0);
    lv_obj_set_style_border_width(wiz_wifi_qr_frame, 0, 0);
    lv_obj_set_style_radius(wiz_wifi_qr_frame, 0, 0);
    lv_obj_set_style_pad_all(wiz_wifi_qr_frame, 0, 0);
    lv_obj_remove_flag(wiz_wifi_qr_frame, LV_OBJ_FLAG_SCROLLABLE);
    wiz_wifi_qr = lv_qrcode_create(wiz_wifi_qr_frame);
    lv_qrcode_set_size(wiz_wifi_qr, 140);
    lv_qrcode_set_dark_color(wiz_wifi_qr, lv_color_black());
    lv_qrcode_set_light_color(wiz_wifi_qr, lv_color_white());
    lv_qrcode_set_quiet_zone(wiz_wifi_qr, true);
    lv_obj_center(wiz_wifi_qr);
    lv_obj_add_flag(wiz_wifi_qr_frame, LV_OBJ_FLAG_HIDDEN);
    wiz_wifi_qr_data[0] = '\0';

    // Instructions
    lv_obj_t* instr = lv_label_create(scr);
    lv_label_set_text(instr, "Checking Wi-Fi...");
    lv_obj_set_style_text_color(instr, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(instr, &lv_font_montserrat_16, 0);
    lv_obj_set_style_text_line_space(instr, 2, 0);
    lv_obj_set_width(instr, 278);
    lv_obj_set_pos(instr, 182, 54);
    lbl_wiz_wifi_instructions = instr;

    add_next_button(scr, "Next");
}

// --------------------------------------------------------------------------
// Step 3: Probe Check
// --------------------------------------------------------------------------

static void create_step_probes() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[3] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Probe Check");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 10);

    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Plug in probes to see live readings:");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT_DIM, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 44);

    // Probe readings
    int y_start = 80;
    int y_spacing = 50;

    // Pit
    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Pit:");
    lv_obj_set_style_text_color(lbl, COLOR_ORANGE, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_set_pos(lbl, 60, y_start);

    lbl_wiz_pit = lv_label_create(scr);
    lv_label_set_text(lbl_wiz_pit, "---");
    lv_obj_set_style_text_color(lbl_wiz_pit, COLOR_ORANGE, 0);
    lv_obj_set_style_text_font(lbl_wiz_pit, &lv_font_montserrat_36, 0);
    lv_obj_set_pos(lbl_wiz_pit, 250, y_start - 6);

    // Meat 1
    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Meat 1:");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_set_pos(lbl, 60, y_start + y_spacing);

    lbl_wiz_meat1 = lv_label_create(scr);
    lv_label_set_text(lbl_wiz_meat1, "---");
    lv_obj_set_style_text_color(lbl_wiz_meat1, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl_wiz_meat1, &lv_font_montserrat_36, 0);
    lv_obj_set_pos(lbl_wiz_meat1, 250, y_start + y_spacing - 6);

    // Meat 2
    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Meat 2:");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_set_pos(lbl, 60, y_start + 2 * y_spacing);

    lbl_wiz_meat2 = lv_label_create(scr);
    lv_label_set_text(lbl_wiz_meat2, "---");
    lv_obj_set_style_text_color(lbl_wiz_meat2, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl_wiz_meat2, &lv_font_montserrat_36, 0);
    lv_obj_set_pos(lbl_wiz_meat2, 250, y_start + 2 * y_spacing - 6);

    add_next_button(scr, "Next");
}

// --------------------------------------------------------------------------
// Step 4: Hardware Test
// --------------------------------------------------------------------------

static void start_hardware_test(unsigned index) {
    if (test_timer) return;
    for (auto button : wiz_test_buttons) lv_obj_add_state(button, LV_STATE_DISABLED);
    const char* names[] = {"Fan", "Servo", "Buzzer"};
    lv_label_set_text_fmt(lbl_test_status, "%s test running...", names[index]);
    if (index == 0 && cb_fan_test) cb_fan_test();
    if (index == 1 && cb_servo_test) cb_servo_test();
    if (index == 2 && cb_buzzer_test) cb_buzzer_test();
    test_timer = lv_timer_create([](lv_timer_t* timer) {
        for (auto button : wiz_test_buttons) lv_obj_remove_state(button, LV_STATE_DISABLED);
        lv_label_set_text(lbl_test_status, "Test sent. Check that it worked.");
        test_timer = nullptr;
        lv_timer_delete(timer);
    }, 1200, nullptr);
}
static void fan_test_cb(lv_event_t*) { start_hardware_test(0); }
static void servo_test_cb(lv_event_t*) { start_hardware_test(1); }
static void buzzer_test_cb(lv_event_t*) { start_hardware_test(2); }

static void create_step_hwtest() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[4] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Hardware Test");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 10);

    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Tap each button to test:");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT_DIM, 0);
    lv_obj_align(lbl, LV_ALIGN_TOP_MID, 0, 44);

    const char* texts[] = {LV_SYMBOL_REFRESH "\nFan", LV_SYMBOL_SETTINGS "\nServo", LV_SYMBOL_BELL "\nBuzzer"};
    lv_event_cb_t callbacks[] = {fan_test_cb, servo_test_cb, buzzer_test_cb};
    for (int i = 0; i < 3; ++i) {
        wiz_test_buttons[i] = UiStyle::button(scr, texts[i], 30 + i * 145, 100, 120, 60, UiStyle::Button::Secondary, &lv_font_montserrat_16);
        lv_obj_add_event_cb(wiz_test_buttons[i], callbacks[i], LV_EVENT_CLICKED, nullptr);
    }
    lbl_test_status = UiStyle::label(scr, "", 20, 190, &lv_font_montserrat_16, COLOR_TEXT_DIM, 440, LV_TEXT_ALIGN_CENTER);

    add_next_button(scr, "Finish");
}

// --------------------------------------------------------------------------
// Step 5: Done
// --------------------------------------------------------------------------

static void create_step_done() {
    lv_obj_t* scr = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr, COLOR_BG, 0);
    wiz_screens[5] = scr;

    lv_obj_t* lbl = lv_label_create(scr);
    lv_label_set_text(lbl, LV_SYMBOL_OK);
    lv_obj_set_style_text_color(lbl, COLOR_GREEN, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_48, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, -40);

    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Setup Complete!");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_24, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, 20);

    lbl = lv_label_create(scr);
    lv_label_set_text(lbl, "Your Pit Claw is ready.");
    lv_obj_set_style_text_color(lbl, COLOR_TEXT_DIM, 0);
    lv_obj_align(lbl, LV_ALIGN_CENTER, 0, 55);
}

// --------------------------------------------------------------------------
// Public API
// --------------------------------------------------------------------------

void ui_wizard_init() {
    if (test_timer) { lv_timer_delete(test_timer); test_timer = nullptr; }
    for (auto& screen : wiz_screens) { if (screen) lv_obj_delete(screen); screen = nullptr; }
    wizard_active = true;
    wizard_step = 0;

    create_step_welcome();
    create_step_units();
    create_step_wifi();
    create_step_probes();
    create_step_hwtest();
    create_step_done();

    for (int i = 1; i < 5; ++i) {
        char step[12]; snprintf(step, sizeof(step), "%d / 5", i + 1);
        UiStyle::label(wiz_screens[i], step, 418, 16, &lv_font_montserrat_14, COLOR_TEXT_DIM, 50, LV_TEXT_ALIGN_RIGHT);
        lv_obj_remove_flag(wiz_screens[i], LV_OBJ_FLAG_SCROLLABLE);
    }
    // Show the welcome screen
    lv_screen_load(wiz_screens[0]);
    ui_refresh_alert_layout();
}

bool ui_wizard_is_active() {
    return wizard_active;
}

void ui_wizard_update_wifi(const WifiInfo& info) {
    if (!wizard_active || !lbl_wiz_wifi_instructions) return;

    char instructions[320];
    char qrData[sizeof(wiz_wifi_qr_data)] = {};
    const char* title = "Wi-Fi Setup";
    if (info.apMode) {
        snprintf(qrData, sizeof(qrData), "WIFI:T:WPA;S:" AP_SSID ";P:" AP_PASSWORD ";;");
        snprintf(instructions, sizeof(instructions),
                 "Join " AP_SSID "\nPassword: " AP_PASSWORD "\n\n"
                 "Stay connected if your phone\nsays \"No Internet\".\n"
                 "Open http://%s", info.ip ? info.ip : "192.168.4.1");
    } else if (info.connected) {
        title = "Wi-Fi Connected";
        snprintf(qrData, sizeof(qrData), "http://%s", info.ip ? info.ip : "bbq.local");
        snprintf(instructions, sizeof(instructions),
                 "Connected to:\n%s\n\n"
                 "On the same Wi-Fi, scan\nthis code or open:\n%s",
                 info.ssid ? info.ssid : "", qrData);
    } else {
        snprintf(instructions, sizeof(instructions),
                 "Reconnecting to Wi-Fi...\n\n"
                 "Setup details will appear\nwhen the hotspot is ready.\n\n"
                 "You can also tap Next\nto continue offline.");
    }

    if (strcmp(lv_label_get_text(lbl_wiz_wifi_title), title) != 0) {
        lv_label_set_text(lbl_wiz_wifi_title, title);
    }
    if (strcmp(lv_label_get_text(lbl_wiz_wifi_instructions), instructions) != 0) {
        lv_label_set_text(lbl_wiz_wifi_instructions, instructions);
    }
    if (qrData[0] == '\0') {
        lv_obj_add_flag(wiz_wifi_qr_frame, LV_OBJ_FLAG_HIDDEN);
        wiz_wifi_qr_data[0] = '\0';
    } else if (strcmp(wiz_wifi_qr_data, qrData) != 0) {
        lv_result_t result = lv_qrcode_update(wiz_wifi_qr, qrData, strlen(qrData));
        if (result == LV_RESULT_OK) {
            snprintf(wiz_wifi_qr_data, sizeof(wiz_wifi_qr_data), "%s", qrData);
            lv_obj_remove_flag(wiz_wifi_qr_frame, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(wiz_wifi_qr_frame, LV_OBJ_FLAG_HIDDEN);
            wiz_wifi_qr_data[0] = '\0';
        }
    }
}

void ui_wizard_set_callbacks(WizardFanTestCb fanCb,
                              WizardServoTestCb servoCb,
                              WizardBuzzerTestCb buzzerCb,
                              WizardUnitsCb unitsCb,
                              WizardCompleteCb completeCb) {
    cb_fan_test    = fanCb;
    cb_servo_test  = servoCb;
    cb_buzzer_test = buzzerCb;
    cb_units       = unitsCb;
    cb_complete    = completeCb;
}

void ui_wizard_update_probes(float pit, float meat1, float meat2,
                              bool pitConn, bool meat1Conn, bool meat2Conn) {
    if (!wizard_active || wizard_step != 3) return;

    char buf[16];

    if (lbl_wiz_pit) {
        if (pitConn) {
            snprintf(buf, sizeof(buf), "%.0f\xC2\xB0%s", ui_display_temp(pit), ui_unit_suffix());
            lv_label_set_text(lbl_wiz_pit, buf);
            lv_obj_set_style_text_color(lbl_wiz_pit, COLOR_GREEN, 0);
        } else {
            lv_label_set_text(lbl_wiz_pit, "---");
            lv_obj_set_style_text_color(lbl_wiz_pit, COLOR_TEXT_DIM, 0);
        }
    }

    if (lbl_wiz_meat1) {
        if (meat1Conn) {
            snprintf(buf, sizeof(buf), "%.0f\xC2\xB0%s", ui_display_temp(meat1), ui_unit_suffix());
            lv_label_set_text(lbl_wiz_meat1, buf);
            lv_obj_set_style_text_color(lbl_wiz_meat1, COLOR_GREEN, 0);
        } else {
            lv_label_set_text(lbl_wiz_meat1, "---");
            lv_obj_set_style_text_color(lbl_wiz_meat1, COLOR_TEXT_DIM, 0);
        }
    }

    if (lbl_wiz_meat2) {
        if (meat2Conn) {
            snprintf(buf, sizeof(buf), "%.0f\xC2\xB0%s", ui_display_temp(meat2), ui_unit_suffix());
            lv_label_set_text(lbl_wiz_meat2, buf);
            lv_obj_set_style_text_color(lbl_wiz_meat2, COLOR_GREEN, 0);
        } else {
            lv_label_set_text(lbl_wiz_meat2, "---");
            lv_obj_set_style_text_color(lbl_wiz_meat2, COLOR_TEXT_DIM, 0);
        }
    }
}

#else // NATIVE_BUILD && !SIMULATOR_BUILD
// Native test stubs
void ui_wizard_init() {}
bool ui_wizard_is_active() { return false; }
void ui_wizard_update_wifi(const WifiInfo&) {}
void ui_wizard_set_callbacks(WizardFanTestCb, WizardServoTestCb,
                              WizardBuzzerTestCb, WizardUnitsCb, WizardCompleteCb) {}
void ui_wizard_update_probes(float, float, float, bool, bool, bool) {}
#endif
