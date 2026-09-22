#include "web_assets.h"
#ifndef NATIVE_BUILD
#include <ESPAsyncWebServer.h>

// PlatformIO embeds the original data/ files; no generated copies are checked in.
#define WEB_ASSET(symbol) \
    extern const uint8_t symbol##_start[] asm("_binary_data_" #symbol "_start"); \
    extern const uint8_t symbol##_end[] asm("_binary_data_" #symbol "_end");
WEB_ASSET(index_html)
WEB_ASSET(app_js)
WEB_ASSET(style_css)
WEB_ASSET(sw_js)
WEB_ASSET(favicon_svg)
WEB_ASSET(manifest_json)
#undef WEB_ASSET

struct WebAsset { const char* path; const char* mime; const uint8_t* start; const uint8_t* end; };
static const WebAsset assets[] = {
    {"/", "text/html; charset=utf-8", index_html_start, index_html_end},
    {"/index.html", "text/html; charset=utf-8", index_html_start, index_html_end},
    {"/app.js", "application/javascript; charset=utf-8", app_js_start, app_js_end},
    {"/style.css", "text/css; charset=utf-8", style_css_start, style_css_end},
    {"/sw.js", "application/javascript; charset=utf-8", sw_js_start, sw_js_end},
    {"/favicon.svg", "image/svg+xml", favicon_svg_start, favicon_svg_end},
    {"/manifest.json", "application/manifest+json", manifest_json_start, manifest_json_end},
};

void registerWebAssets(AsyncWebServer& server) {
    for (const auto& asset : assets) {
        const auto* entry = &asset;
        server.on(entry->path, HTTP_GET, [entry](AsyncWebServerRequest* request) {
            request->send(200, entry->mime, entry->start, size_t(entry->end - entry->start));
        });
    }
}
#endif
