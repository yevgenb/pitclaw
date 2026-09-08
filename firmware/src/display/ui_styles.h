#pragma once

#include "ui_colors.h"
#include <stdarg.h>
#include <stdio.h>

#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)
namespace UiStyle {
// One shape family for interactive surfaces; larger dialogs use its next size.
constexpr int CORNER_RADIUS = 12;
constexpr int DIALOG_RADIUS = 16;
constexpr int SPACE = 8;
constexpr int NAV_HEIGHT = 52;
constexpr int NAV_TOP = 264;
constexpr int ACTION_HEIGHT = 52;

enum class Button { Secondary, Primary, Danger };

// LVGL's built-in printf may be compiled without floating-point support.
inline void text_fmt(lv_obj_t* label, const char* format, ...) {
    char text[192];
    va_list args;
    va_start(args, format);
    vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    lv_label_set_text(label, text);
}

inline lv_obj_t* box(lv_obj_t* parent, int x, int y, int w, int h,
                     lv_color_t color, int radius = CORNER_RADIUS) {
    auto obj = lv_obj_create(parent);
    lv_obj_remove_style_all(obj);
    lv_obj_set_pos(obj, x, y);
    lv_obj_set_size(obj, w, h);
    lv_obj_set_style_bg_color(obj, color, 0);
    lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    lv_obj_set_style_radius(obj, radius, 0);
    lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
    return obj;
}

inline lv_obj_t* label(lv_obj_t* parent, const char* text, int x, int y,
                       const lv_font_t* font = &lv_font_montserrat_16,
                       lv_color_t color = COLOR_TEXT, int width = 0,
                       lv_text_align_t align = LV_TEXT_ALIGN_LEFT) {
    auto obj = lv_label_create(parent);
    lv_obj_remove_style_all(obj);
    lv_label_set_text(obj, text);
    lv_obj_set_pos(obj, x, y);
    lv_obj_set_style_text_font(obj, font, 0);
    lv_obj_set_style_text_color(obj, color, 0);
    lv_obj_set_style_text_align(obj, align, 0);
    if (width) lv_obj_set_width(obj, width);
    return obj;
}

inline lv_obj_t* button(lv_obj_t* parent, const char* text, int x, int y,
                        int w, int h = ACTION_HEIGHT, Button role = Button::Secondary,
                        const lv_font_t* font = &lv_font_montserrat_18) {
    auto obj = lv_button_create(parent);
    lv_obj_remove_style_all(obj);
    lv_obj_set_pos(obj, x, y);
    lv_obj_set_size(obj, w, h);
    lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    lv_obj_set_style_radius(obj, CORNER_RADIUS, 0);
    lv_obj_set_style_bg_color(obj, role == Button::Primary ? COLOR_ORANGE :
                                  role == Button::Danger ? COLOR_DANGER : COLOR_BUTTON_BG, 0);
    lv_obj_set_style_text_color(obj, role == Button::Primary ? COLOR_BG : COLOR_TEXT, 0);
    lv_obj_set_style_text_font(obj, font, 0);
    lv_obj_set_style_bg_color(obj, lv_color_hex(role == Button::Primary ? 0xE95D00 :
                                               role == Button::Danger ? 0x932018 : 0x484848), LV_STATE_PRESSED);
    lv_obj_set_style_bg_color(obj, COLOR_ORANGE, LV_STATE_CHECKED);
    lv_obj_set_style_text_color(obj, COLOR_BG, LV_STATE_CHECKED);
    lv_obj_set_style_bg_color(obj, lv_color_hex(0xE95D00), LV_STATE_CHECKED | LV_STATE_PRESSED);
    lv_obj_set_style_bg_color(obj, COLOR_CARD_BG, LV_STATE_DISABLED);
    lv_obj_set_style_text_color(obj, COLOR_TEXT_DIM, LV_STATE_DISABLED);

    auto text_obj = lv_label_create(obj);
    lv_obj_remove_style_all(text_obj); // Text inherits every button state's foreground.
    lv_label_set_text(text_obj, text);
    lv_obj_set_width(text_obj, w - 8);
    lv_obj_set_style_text_align(text_obj, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_center(text_obj);

    auto selection = box(obj, (w - 40) / 2, h - 5, 40, 2, COLOR_BG, 0);
    lv_obj_remove_flag(selection, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_flag(selection, LV_OBJ_FLAG_HIDDEN);
    return obj;
}

inline void selected(lv_obj_t* button, bool value) {
    if (!button) return;
    if (value) lv_obj_add_state(button, LV_STATE_CHECKED);
    else lv_obj_remove_state(button, LV_STATE_CHECKED);
    auto line = lv_obj_get_child(button, 1);
    if (value) lv_obj_remove_flag(line, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_add_flag(line, LV_OBJ_FLAG_HIDDEN);
}

inline lv_obj_t* card(lv_obj_t* parent, int x, int y, int w, int h, lv_color_t accent) {
    auto obj = box(parent, x, y, w, h, COLOR_CARD_BG);
    lv_obj_set_style_border_width(obj, 3, 0);
    lv_obj_set_style_border_side(obj, LV_BORDER_SIDE_LEFT, 0);
    lv_obj_set_style_border_color(obj, accent, 0);
    lv_obj_set_style_bg_color(obj, COLOR_BUTTON_BG, LV_STATE_PRESSED);
    return obj;
}
} // namespace UiStyle
#endif
