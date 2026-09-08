#pragma once

// Shared color constants for LVGL touchscreen UI.
// Included by ui_init.cpp, ui_update.cpp, and ui_setup_wizard.cpp.

#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)
#include <lvgl.h>

#define COLOR_BG          lv_color_hex(0x1A1A1A)
#define COLOR_CARD_BG     lv_color_hex(0x2A2A2A)
#define COLOR_NAV_BG      lv_color_hex(0x111111)
#define COLOR_TEXT         lv_color_hex(0xFFFFFF)
#define COLOR_TEXT_DIM     lv_color_hex(0xB3B3B3)
#define COLOR_TEXT_VDIM    lv_color_hex(0xB3B3B3)
#define COLOR_ORANGE       lv_color_hex(0xFF6600)
#define COLOR_RED          lv_color_hex(0xFF6B62)
#define COLOR_BLUE         lv_color_hex(0x75B6FF)
#define COLOR_GREEN        lv_color_hex(0x55DD66)
#define COLOR_PURPLE       lv_color_hex(0xB499FF)
#define COLOR_BAR_BG      lv_color_hex(0x333333)
#define COLOR_BUTTON_BG   lv_color_hex(0x383838)
#define COLOR_DANGER      lv_color_hex(0xB3261E)

#endif
