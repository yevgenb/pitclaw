// Design comparison renderer only. This file is outside the firmware src tree.
#include <cstdio>
#include <cstdint>
#include <cmath>
#include <cassert>
#include <string>
#include "src/display/ui_init.cpp"
#define cb_units wizard_units_callback
#include "src/display/ui_setup_wizard.cpp"
#undef cb_units

static uint16_t compare_buf[480*40];
static uint8_t compare_rgb[480*320*3];
static uint32_t compare_clock=1;
static bool compare_outline=false;
static std::string compare_output;
static void compare_flush(lv_display_t* d,const lv_area_t* a,uint8_t* p){
 auto rgb=reinterpret_cast<uint16_t*>(p);
 for(int y=a->y1;y<=a->y2;++y)for(int x=a->x1;x<=a->x2;++x){
  uint16_t v=*rgb++;size_t k=(y*480+x)*3;
  compare_rgb[k]=((v>>11)&31)*255/31;compare_rgb[k+1]=((v>>5)&63)*255/63;compare_rgb[k+2]=(v&31)*255/31;
 }
 lv_display_flush_ready(d);
}
static void compare_shot(const char* name){
 lv_obj_update_layout(lv_screen_active());lv_obj_update_layout(lv_layer_top());lv_obj_invalidate(lv_screen_active());
 for(int i=0;i<10;++i){compare_clock+=10;lv_timer_handler();}
 auto file=compare_output+"/"+name+".ppm";FILE* f=fopen(file.c_str(),"wb");assert(f);
 fprintf(f,"P6\n480 320\n255\n");fwrite(compare_rgb,1,sizeof(compare_rgb),f);fclose(f);
}
static lv_color_t pc(uint32_t c){return lv_color_hex(c);}
static const uint32_t P_BG=0x1A1A1A,P_SURFACE=0x2A2A2A,P_NAV=0x111111,P_TEXT=0xFFFFFF,P_MUTED=0xB3B3B3,P_ORANGE=0xFF6600,P_RED=0xFF6B62,P_BLUE=0x75B6FF,P_BUTTON=0x383838;
static lv_obj_t* p_box(lv_obj_t* parent,int x,int y,int w,int h,uint32_t color,int radius=8){
 auto o=lv_obj_create(parent);lv_obj_remove_style_all(o);lv_obj_set_pos(o,x,y);lv_obj_set_size(o,w,h);
 lv_obj_set_style_bg_color(o,pc(color),0);lv_obj_set_style_bg_opa(o,LV_OPA_COVER,0);lv_obj_set_style_radius(o,radius,0);
 lv_obj_remove_flag(o,LV_OBJ_FLAG_SCROLLABLE);return o;
}
static lv_obj_t* p_screen(){auto s=p_box(nullptr,0,0,480,320,P_BG,0);lv_screen_load(s);return s;}
static lv_obj_t* p_label(lv_obj_t* parent,const char* text,int x,int y,const lv_font_t* font,uint32_t color=P_TEXT,int width=0,lv_text_align_t align=LV_TEXT_ALIGN_LEFT){
 auto l=lv_label_create(parent);lv_obj_remove_style_all(l);lv_label_set_text(l,text);lv_obj_set_pos(l,x,y);
 lv_obj_set_style_text_font(l,font,0);lv_obj_set_style_text_color(l,pc(color),0);lv_obj_set_style_text_align(l,align,0);
 if(width)lv_obj_set_width(l,width);return l;
}
static lv_obj_t* p_button(lv_obj_t* parent,const char* text,int x,int y,int w,int h,int kind=0,const lv_font_t* font=&lv_font_montserrat_18){
 auto b=lv_btn_create(parent);lv_obj_remove_style_all(b);lv_obj_set_pos(b,x,y);lv_obj_set_size(b,w,h);lv_obj_remove_flag(b,LV_OBJ_FLAG_SCROLLABLE);
 uint32_t bg=kind==1?P_ORANGE:kind==2?0xB3261E:P_BUTTON;
 lv_obj_set_style_bg_color(b,pc(bg),0);lv_obj_set_style_bg_opa(b,LV_OPA_COVER,0);lv_obj_set_style_radius(b,8,0);
 lv_obj_set_style_bg_color(b,pc(kind==1?0xE95D00:kind==2?0x932018:0x484848),LV_STATE_PRESSED);
 auto l=p_label(b,text,0,0,font,kind==1?P_BG:P_TEXT,w-8,LV_TEXT_ALIGN_CENTER);lv_obj_center(l);return b;
}
static void p_nav(lv_obj_t* s,int selected){
 auto n=p_box(s,0,264,480,56,P_NAV,0);
 const char* labels[]={LV_SYMBOL_HOME " Home",LV_SYMBOL_IMAGE " Graph",LV_SYMBOL_SETTINGS " Settings"};
 for(int i=0;i<3;++i){
  auto b=p_button(n,labels[i],i*160,0,160,56,(selected==i&&!compare_outline)?1:0,&lv_font_montserrat_18);
  lv_obj_set_style_radius(b,0,0);
  if(selected!=i||compare_outline)lv_obj_set_style_bg_color(b,pc(P_NAV),0);
  if(selected==i){
   auto label=lv_obj_get_child(b,0);
   if(compare_outline)lv_obj_set_style_text_color(label,pc(P_ORANGE),0);
   p_box(b,48,49,64,3,compare_outline?P_ORANGE:P_BG,0);
  }
 }
}
static void p_header(lv_obj_t* s){
 auto h=p_box(s,0,0,480,32,P_NAV,0);
 p_label(h,LV_SYMBOL_WIFI,12,8,&lv_font_montserrat_16,0x55DD66);
 p_label(h,"Cook",40,7,&lv_font_montserrat_16,P_MUTED);
 p_label(h,"05:20:45",156,2,&lv_font_montserrat_24,P_TEXT,168,LV_TEXT_ALIGN_CENTER);
 p_label(h,"\xC2\xB0" "F",428,5,&lv_font_montserrat_18,P_MUTED,40,LV_TEXT_ALIGN_RIGHT);
}
static void p_output(lv_obj_t* s){
 p_label(s,"FAN 100%",12,38,&lv_font_montserrat_16,0x55DD66);
 p_box(s,105,45,111,6,0x55DD66,3);
 p_label(s,"DAMPER 100%",246,38,&lv_font_montserrat_16,0xB499FF);
 p_box(s,373,45,95,6,0xB499FF,3);
}
static lv_obj_t* p_card(lv_obj_t* s,int x,int y,int w,int h,uint32_t accent){
 auto c=p_box(s,x,y,w,h,P_SURFACE,8);lv_obj_add_flag(c,LV_OBJ_FLAG_CLICKABLE);
 lv_obj_set_style_border_width(c,3,0);lv_obj_set_style_border_side(c,LV_BORDER_SIDE_LEFT,0);lv_obj_set_style_border_color(c,pc(accent),0);
 lv_obj_set_style_bg_color(c,pc(0x383838),LV_STATE_PRESSED);return c;
}
static void p_dashboard(lv_obj_t* s,bool alarm=false){
 p_header(s);p_output(s);
 int height=alarm?136:190;
 auto pit=p_card(s,8,64,226,height,P_ORANGE);
 p_label(pit,"PIT",16,alarm?10:18,&lv_font_montserrat_18,P_ORANGE,190,LV_TEXT_ALIGN_CENTER);
 p_label(pit,LV_SYMBOL_EDIT,190,12,&lv_font_montserrat_14,P_MUTED);
 p_label(pit,"225\xC2\xB0",12,alarm?36:69,&lv_font_montserrat_48,P_ORANGE,198,LV_TEXT_ALIGN_CENTER);
 p_label(pit,"Target 225\xC2\xB0" "F",12,height-34,&lv_font_montserrat_18,P_MUTED,198,LV_TEXT_ALIGN_CENTER);
 for(int i=0;i<2;++i){
  int mh=alarm?64:91;int yy=64+i*(mh+8);auto c=p_card(s,242,yy,230,mh,i==0?P_RED:P_BLUE);
  p_label(c,i==0?"MEAT 1":"MEAT 2",14,alarm?5:9,&lv_font_montserrat_16,P_MUTED);
  p_label(c,LV_SYMBOL_EDIT,196,alarm?5:9,&lv_font_montserrat_14,P_MUTED);
  p_label(c,i==0?(alarm?"203\xC2\xB0":"165\xC2\xB0"):"172\xC2\xB0",14,alarm?29:36,alarm?&lv_font_montserrat_24:&lv_font_montserrat_36,i==0?P_RED:P_BLUE);
  p_label(c,"Target",128,alarm?23:32,&lv_font_montserrat_16,P_MUTED);
  p_label(c,i==0?"203\xC2\xB0" "F":"195\xC2\xB0" "F",128,alarm?42:54,&lv_font_montserrat_16,P_TEXT);
 }
 if(alarm){
  auto a=p_box(s,8,208,464,52,0xB3261E,8);
  p_label(a,LV_SYMBOL_WARNING " MEAT 1 DONE",12,16,&lv_font_montserrat_18,P_TEXT);
  auto b=p_button(a,"Silence",338,0,126,52,0,&lv_font_montserrat_18);lv_obj_set_style_bg_color(b,pc(0x801A15),0);
 }
 p_nav(s,0);
}
static lv_obj_t* p_overlay(){
 auto o=lv_obj_create(lv_layer_top());lv_obj_remove_style_all(o);lv_obj_set_pos(o,0,0);lv_obj_set_size(o,480,320);
 lv_obj_set_style_bg_color(o,pc(0),0);lv_obj_set_style_bg_opa(o,LV_OPA_60,0);lv_obj_remove_flag(o,LV_OBJ_FLAG_SCROLLABLE);return o;
}
static lv_obj_t* p_editor(bool meat){
 auto o=p_overlay();auto c=p_box(o,32,32,416,256,P_SURFACE,12);
 p_label(c,meat?"Meat 2 target":"Pit setpoint",16,18,&lv_font_montserrat_24,P_TEXT,384,LV_TEXT_ALIGN_CENTER);
 p_button(c,"-5",20,70,76,64,0,&lv_font_montserrat_24);
 p_label(c,meat?"195\xC2\xB0" "F":"225\xC2\xB0" "F",108,81,&lv_font_montserrat_36,meat?P_BLUE:P_ORANGE,200,LV_TEXT_ALIGN_CENTER);
 p_button(c,"+5",320,70,76,64,0,&lv_font_montserrat_24);
 p_label(c,meat?"100 - 212\xC2\xB0" "F":"100 - 500\xC2\xB0" "F",16,146,&lv_font_montserrat_16,P_MUTED,384,LV_TEXT_ALIGN_CENTER);
 if(meat){p_button(c,"Clear",16,188,120,52);p_button(c,"Cancel",148,188,120,52);p_button(c,"Set",280,188,120,52,1);}
 else{p_button(c,"Cancel",16,188,186,52);p_button(c,"Apply",214,188,186,52,1);}
 return o;
}
static void p_settings(lv_obj_t* s,bool lower){
 p_label(s,"Settings",8,8,&lv_font_montserrat_24,P_TEXT,464,LV_TEXT_ALIGN_CENTER);
 if(!lower){
  auto r=p_box(s,8,46,464,56,P_SURFACE);
  p_label(r,"Units",16,18,&lv_font_montserrat_18);
  p_button(r,LV_SYMBOL_OK " \xC2\xB0" "F",280,2,80,52,1);p_button(r,"\xC2\xB0" "C",368,2,88,52);
  r=p_box(s,8,110,464,64,P_SURFACE);p_label(r,"Fan",16,22,&lv_font_montserrat_18);
  p_button(r,"Fan only",116,6,108,52,0,&lv_font_montserrat_16);
  auto b=p_button(r,"Fan +\ndamper",232,6,108,52,1,&lv_font_montserrat_16);p_box(b,34,47,40,2,P_BG,0);
  p_button(r,"Damper\npriority",348,6,108,52,0,&lv_font_montserrat_16);
  p_button(s,"New session",8,182,464,56,0);
  p_label(s,"Wi-Fi and device settings " LV_SYMBOL_DOWN,16,243,&lv_font_montserrat_14,P_MUTED,448,LV_TEXT_ALIGN_CENTER);
 }else{
  p_label(s,"v0.2.0",386,13,&lv_font_montserrat_14,P_MUTED,82,LV_TEXT_ALIGN_RIGHT);
  auto r=p_box(s,8,44,464,96,P_SURFACE);
  p_label(r,LV_SYMBOL_WIFI " Connected",14,5,&lv_font_montserrat_16,0x55DD66);
  p_label(r,"SSID: Example-network-with-a-long-name",14,27,&lv_font_montserrat_16,P_MUTED);
  p_label(r,"IP: 192.168.100.100  (bbq.local)",14,49,&lv_font_montserrat_16,P_MUTED);
  p_label(r,"Signal: -62 dBm (Fair)",14,71,&lv_font_montserrat_16,P_MUTED);
  p_button(s,"Disconnect",8,148,228,52);p_button(s,"Setup mode",244,148,228,52);
  p_button(s,"Factory reset",8,208,464,52,2);
 }
 p_nav(s,2);
}
static void p_graph(lv_obj_t* s){
 p_label(s,"Temperature history (\xC2\xB0" "F)",12,8,&lv_font_montserrat_18);
 p_label(s,"15 min",390,10,&lv_font_montserrat_16,P_MUTED,76,LV_TEXT_ALIGN_RIGHT);
 auto ch=lv_chart_create(s);lv_obj_remove_style_all(ch);lv_obj_set_pos(ch,50,40);lv_obj_set_size(ch,422,168);
 lv_obj_set_style_bg_color(ch,pc(P_SURFACE),0);lv_obj_set_style_bg_opa(ch,LV_OPA_COVER,0);lv_obj_set_style_line_color(ch,pc(0x474747),LV_PART_MAIN);
 lv_obj_set_style_line_width(ch,1,LV_PART_MAIN);lv_obj_set_style_line_width(ch,2,LV_PART_ITEMS);lv_obj_set_style_size(ch,0,0,LV_PART_INDICATOR);
 lv_chart_set_type(ch,LV_CHART_TYPE_LINE);lv_chart_set_range(ch,LV_CHART_AXIS_PRIMARY_Y,50,250);lv_chart_set_point_count(ch,181);lv_chart_set_div_line_count(ch,5,3);
 auto pit=lv_chart_add_series(ch,pc(P_ORANGE),LV_CHART_AXIS_PRIMARY_Y);auto m1=lv_chart_add_series(ch,pc(P_RED),LV_CHART_AXIS_PRIMARY_Y);auto m2=lv_chart_add_series(ch,pc(P_BLUE),LV_CHART_AXIS_PRIMARY_Y);
 for(int i=0;i<=180;++i){lv_chart_set_next_value(ch,pit,220+7*sin(i/12.));lv_chart_set_next_value(ch,m1,95+i*.4);lv_chart_set_next_value(ch,m2,90+i*.35);}
 for(int x=0;x<420;x+=14)p_box(ch,x,20,8,2,P_MUTED,0);
 for(int i=0;i<5;++i){char b[12];snprintf(b,sizeof(b),"%d",250-i*50);p_label(s,b,0,32+i*42,&lv_font_montserrat_14,P_MUTED,42,LV_TEXT_ALIGN_RIGHT);}
 p_label(s,"0 min",50,212,&lv_font_montserrat_14,P_MUTED);
 p_label(s,"7.5 min",220,212,&lv_font_montserrat_14,P_MUTED,82,LV_TEXT_ALIGN_CENTER);
 p_label(s,"15 min",390,212,&lv_font_montserrat_14,P_MUTED,82,LV_TEXT_ALIGN_RIGHT);
 p_label(s,"Pit",80,239,&lv_font_montserrat_16,P_ORANGE);p_label(s,"Meat 1",150,239,&lv_font_montserrat_16,P_RED);
 p_label(s,"Meat 2",246,239,&lv_font_montserrat_16,P_BLUE);p_label(s,"-- Target",346,239,&lv_font_montserrat_16,P_MUTED);
 p_nav(s,1);
}
static void p_wifi(lv_obj_t* s){
 p_label(s,"Wi-Fi setup",12,10,&lv_font_montserrat_24,P_TEXT,456,LV_TEXT_ALIGN_CENTER);
 p_label(s,"3 / 5",410,16,&lv_font_montserrat_14,P_MUTED,54,LV_TEXT_ALIGN_RIGHT);
 auto frame=p_box(s,16,70,156,156,0xFFFFFF,0);auto qr=lv_qrcode_create(frame);
 lv_qrcode_set_size(qr,140);lv_qrcode_set_dark_color(qr,lv_color_black());lv_qrcode_set_light_color(qr,lv_color_white());lv_qrcode_set_quiet_zone(qr,true);lv_obj_center(qr);
 const char* data="WIFI:T:WPA;S:" AP_SSID ";P:" AP_PASSWORD ";;";lv_qrcode_update(qr,data,strlen(data));
 p_label(s,"Join " AP_SSID "\nPassword: " AP_PASSWORD "\n\nStay connected if your phone\nshows \"No Internet\".\nOpen 192.168.4.1",190,65,&lv_font_montserrat_16,P_TEXT,278);
 p_button(s,LV_SYMBOL_LEFT " Back",16,256,212,56);p_button(s,"Next " LV_SYMBOL_RIGHT,252,256,212,56,1);
}
int main(int argc,char**argv){
 compare_output=argc>1?argv[1]:"work/ui-comparison/screens";
 lv_init();lv_tick_set_cb([]()->uint32_t{return compare_clock;});auto d=lv_display_create(480,320);
 lv_display_set_color_format(d,LV_COLOR_FORMAT_RGB565);lv_display_set_buffers(d,compare_buf,nullptr,sizeof(compare_buf),LV_DISPLAY_RENDER_MODE_PARTIAL);lv_display_set_flush_cb(d,compare_flush);
 create_dashboard_screen();create_graph_screen();create_settings_screen();create_setpoint_modal();create_meat_target_modal();create_confirm_modal();ui_graph_init();ui_switch_screen(Screen::DASHBOARD);
 ui_set_units(true);ui_update_temps(225,165,172,true,true,true);ui_update_setpoint(225);ui_update_meat1_target(203);ui_update_meat2_target(195);ui_update_output_bars(100,100);ui_update_wifi(true);ui_update_cook_timer(0,19245,0);
 compare_shot("current-dashboard");pit_card_click_cb(nullptr);compare_shot("current-pit-editor");hide_modal(modal_setpoint);meat2_card_click_cb(nullptr);compare_shot("current-meat-editor");hide_modal(modal_meat);
 ui_update_temps(225,203,172,true,true,true);ui_update_alerts(3,false,false,0);compare_shot("current-alarm");ui_update_alerts(0,false,false,0);ui_update_temps(225,165,172,true,true,true);
 ui_switch_screen(Screen::SETTINGS);ui_update_wifi_info({true,false,"Example-network-with-a-long-name","192.168.100.100",-62});compare_shot("current-settings");
 lv_obj_scroll_to_y(lv_obj_get_child(scr_settings,1),1000,LV_ANIM_OFF);compare_shot("current-settings-more");
 ui_switch_screen(Screen::GRAPH);ui_graph_clear();for(int i=0;i<=180;++i)ui_graph_add_point(220+7*sin(i/12.),95+i*.4,90+i*.35,225,false,false,false);compare_shot("current-graph");
 ui_wizard_init();go_to_step(2);ui_wizard_update_wifi({false,true,AP_SSID,"192.168.4.1",0});compare_shot("current-wifi-setup");
 for(int v=0;v<2;++v){
  compare_outline=v;const char* names[]={"dashboard","pit-editor","meat-editor","settings","settings-more","alarm","graph","wifi-setup"};
  for(int i=0;i<8;++i){auto s=p_screen();lv_obj_t* overlay=nullptr;
   if(i<3){p_dashboard(s);if(i==1||i==2)overlay=p_editor(i==2);}
   if(i==3||i==4)p_settings(s,i==4);if(i==5)p_dashboard(s,true);if(i==6)p_graph(s);if(i==7)p_wifi(s);
   std::string name=std::string(v?"proposed-underline-":"proposed-filled-")+names[i];compare_shot(name.c_str());
   if(overlay)lv_obj_delete(overlay);
   lv_screen_load(scr_dashboard);lv_obj_delete(s);
  }
 }
 printf("Rendered 8 current screens and 16 proposed screens at 480x320 RGB565.\n");
}
