// Headless regression check linked against the simulator's LVGL build.
// Include the production screen implementation to create its widgets without SDL.
#include <cassert>
#include <cstdio>
#include "../../src/display/ui_init.cpp"
#include "../../src/display/ui_boot_splash.cpp"

static uint16_t test_pixels[480 * 40];
static unsigned flush_count = 0;

static void test_flush(lv_display_t* display, const lv_area_t*, uint8_t*) {
    ++flush_count;
    lv_display_flush_ready(display);
}

static void pump_display() {
    for (unsigned i = 0; i < 30; ++i) {
        lv_tick_inc(10);
        lv_timer_handler();
    }
}

int main() {
    lv_init();
    auto display = lv_display_create(480, 320);
    lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB565);
    lv_display_set_buffers(display, test_pixels, nullptr, sizeof(test_pixels),
                           LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(display, test_flush);

    create_dashboard_screen();
    create_graph_screen();
    create_settings_screen();
    create_setpoint_modal();
    create_meat_target_modal();
    create_confirm_modal();
    ui_graph_init();
    lv_screen_load(scr_dashboard);
    pump_display();

    // Reproduce the completed-setup boot sequence.
    ui_boot_splash_init();
    pump_display();
    ui_boot_splash_cleanup();
    ui_switch_screen(Screen::DASHBOARD);
    assert(lv_screen_active() != nullptr);
    const unsigned before = flush_count;
    pump_display();
    assert(lv_screen_active() == scr_dashboard);
    assert(flush_count > before);

    // Navigation must still complete after returning from the boot splash.
    ui_switch_screen(Screen::SETTINGS);
    pump_display();
    assert(lv_screen_active() == scr_settings);
    ui_switch_screen(Screen::DASHBOARD);
    pump_display();
    assert(lv_screen_active() == scr_dashboard);
    puts("Boot transition renders and subsequent navigation completes.");
}
