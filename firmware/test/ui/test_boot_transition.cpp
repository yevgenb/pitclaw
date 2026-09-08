// Headless regression check linked against the simulator's LVGL build.
// Include the production screen implementation to create its widgets without SDL.
#include <cassert>
#include <cstdio>
#include "../../src/display/ui_init.cpp"
#include "../../src/display/ui_boot_splash.cpp"

static uint16_t test_pixels[480 * 40];
static unsigned flush_count = 0;
static uint32_t test_time_ms = 1;
static bool touch_down = false;
static lv_point_t touch_point = {};
static unsigned tab_taps = 0;

static void test_flush(lv_display_t* display, const lv_area_t*, uint8_t*) {
    ++flush_count;
    lv_display_flush_ready(display);
}

static void test_touch(lv_indev_t*, lv_indev_data_t* data) {
    data->point = touch_point;
    data->state = touch_down ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
}

static void pump_display(unsigned ms = 300) {
    for (unsigned i = 0; i < ms; i += 10) {
        test_time_ms += 10;
        lv_timer_handler();
    }
}

static void tap_tab(Screen from, unsigned target, int x, int y, int drift = 0) {
    ui_switch_screen(from);
    lv_obj_update_layout(lv_screen_active());
    auto button = nav_btns[static_cast<unsigned>(from)][target];

    touch_point = {x, y};
    touch_down = true;
    pump_display(10);
    assert(lv_obj_has_state(button, LV_STATE_PRESSED));
    // Preserve click-on-release so starting a drag doesn't activate controls.
    assert(ui_get_current_screen() == from);
    if (drift) {
        touch_point.y += drift;
        pump_display(10);
    }
    touch_down = false;
    pump_display(10);
    assert(ui_get_current_screen() == static_cast<Screen>(target));
    assert(lv_display_get_screen_prev(nullptr) == nullptr);
    assert(lv_anim_count_running() == 0);
    ++tab_taps;
}

int main() {
    lv_init();
    lv_tick_set_cb([]() -> uint32_t { return test_time_ms; });
    auto display = lv_display_create(480, 320);
    lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(display, test_pixels, nullptr, sizeof(test_pixels),
                           LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(display, test_flush);
    auto input = lv_indev_create();
    lv_indev_set_type(input, LV_INDEV_TYPE_POINTER);
    lv_indev_set_display(input, display);
    lv_indev_set_read_cb(input, test_touch);
    lv_timer_set_period(lv_indev_get_read_timer(input), 10);

    create_dashboard_screen();
    create_graph_screen();
    create_settings_screen();
    create_setpoint_modal();
    create_meat_target_modal();
    create_confirm_modal();
    ui_graph_init();
    lv_screen_load(scr_dashboard);
    pump_display();

    // Blocking startup must not consume the splash's interactive countdown.
    ui_boot_splash_init();
    test_time_ms += 15000;
    ui_boot_splash_restart_timer();
    ui_boot_splash_update();
    assert(ui_boot_splash_is_active());
    pump_display(1990);
    ui_boot_splash_update();
    assert(ui_boot_splash_is_active());
    pump_display(10);
    ui_boot_splash_update();
    assert(!ui_boot_splash_is_active());
    ui_boot_splash_cleanup();
    ui_switch_screen(Screen::DASHBOARD);
    assert(lv_screen_active() != nullptr);
    const unsigned before = flush_count;
    pump_display();
    assert(lv_screen_active() == scr_dashboard);
    assert(flush_count > before);

    // A touch seen before blocking startup must still require a fresh 10s hold.
    ui_boot_splash_init();
    touch_point = {240, 160};
    touch_down = true;
    pump_display(10);
    test_time_ms += 15000;
    ui_boot_splash_restart_timer();
    ui_boot_splash_update();
    assert(!ui_boot_splash_factory_reset_triggered());
    pump_display(9990);
    ui_boot_splash_update();
    assert(!ui_boot_splash_factory_reset_triggered());
    pump_display(10);
    ui_boot_splash_update();
    assert(ui_boot_splash_factory_reset_triggered());
    touch_down = false;
    pump_display(10);
    ui_boot_splash_cleanup();
    ui_switch_screen(Screen::DASHBOARD);

    // Real pointer events, including the former dead areas at edges and gaps.
    for (unsigned source = 0; source < 3; ++source) {
        for (unsigned target = 0; target < 3; ++target) {
            auto from = static_cast<Screen>(source);
            const int left = static_cast<int>(target) * 160;
            tap_tab(from, target, left, 270);
            tap_tab(from, target, left + 159, 319);
            tap_tab(from, target, left + 80, 271);
            tap_tab(from, target, left + 80, 318);
            tap_tab(from, target, left + 80, 295);
            tap_tab(from, target, left + 80, 295, 12);
            tap_tab(from, target, left + 80, 295, -12);
        }
    }
    // Follow-up taps arrive without waiting out a screen transition.
    for (unsigned i = 0; i < 60; ++i) {
        unsigned target = (static_cast<unsigned>(ui_get_current_screen()) + 1) % 3;
        tap_tab(ui_get_current_screen(), target, target * 160 + 80, 295);
    }
    const unsigned before_render = flush_count;
    pump_display(40);
    assert(flush_count > before_render);
    printf("Splash timing/lifecycle and %u tab taps passed (edges, drags, rapid navigation).\n", tab_taps);
}
