#include "web_auth.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ArduinoJson.h>
#define private public
#include "config_manager.h"
#undef private
#include "config_manager.cpp"

int main() {
    WebAuth auth;
    assert(!auth.enabled());
    assert(auth.gate("GET", "/api/version", "", "", "bbq", 0) == 0);
    assert(auth.gate("GET", "/ws", "", "https://proxy.example", "192.168.0.29", 0) == 0);
    assert(auth.gate("GET", "/ota/start", "", "https://proxy.example", "192.168.0.29", 0) == 0);
    assert(auth.gate("POST", "/ota/upload", "", "https://proxy.example", "192.168.0.29", 0) == 0);
    assert(auth.gate("POST", "/api/auth/settings", "", "https://evil.example", "bbq", 0) == 403);
    assert(!auth.setPassword("short"));
    assert(!auth.setPassword("1234567"));
    assert(!auth.setPassword(u8"ééééééé")); // Seven characters, even though UTF-8 occupies 14 bytes.
    assert(!auth.setPassword(std::string(129, 'x')));
    assert(auth.setPassword("12345678"));
    { std::string token; assert(auth.login("12345678", 0, token) == 200); }
    auth.disable();
    const std::string password = "a long test password";
    assert(auth.setPassword(password));
    const auto saved = auth.config();
    assert(strlen(saved.salt) == 32 && strlen(saved.hash) == 64);
    assert(saved.iterations == WebAuth::PasswordIterations);
    {
        ConfigManager cfg;
        assert(!cfg.getConfig().webAuth.enabled);
        cfg.getConfigMutable().webAuth = saved;
        JsonDocument json; cfg.toJson(json);
        ConfigManager rebooted; rebooted.fromJson(json);
        assert(rebooted.getConfig().webAuth.enabled);
        assert(strcmp(rebooted.getConfig().webAuth.salt, saved.salt) == 0);
        assert(strcmp(rebooted.getConfig().webAuth.hash, saved.hash) == 0);
        assert(rebooted.getConfig().webAuth.iterations == saved.iterations);
        assert(json["webAuth"]["password"].isNull());
        json["webAuth"].remove("iterations"); rebooted.fromJson(json);
        assert(rebooted.getConfig().webAuth.iterations == WebAuth::LegacyPasswordIterations);
        json["webAuth"]["iterations"] = "invalid"; rebooted.fromJson(json);
        assert(rebooted.getConfig().webAuth.iterations == 0);
        JsonDocument legacy; rebooted.fromJson(legacy);
        assert(!rebooted.getConfig().webAuth.enabled);
        legacy["webAuth"]["enabled"] = "invalid"; rebooted.fromJson(legacy);
        assert(rebooted.getConfig().webAuth.enabled);
        auth.load(rebooted.getConfig().webAuth);
        std::string invalidToken;
        assert(auth.login(password, 0, invalidToken) == 401);
        auth.load(saved);
    }
    for (const auto* path : {"/api/version", "/api/servo", "/ws", "/update", "/ota/start", "/ota/upload", "/config.json", "/session.csv"})
        assert(auth.gate("GET", path, "", "", "bbq", 0) == 401);
    assert(auth.gate("GET", "/api/auth", "", "", "bbq", 0) == 0);
    assert(auth.gate("GET", "/app.js", "", "", "bbq", 0) == 0);
    assert(auth.gate("POST", "/api/auth/login", "", "", "bbq", 0) == 0);
    std::string token;
    for (unsigned i = 0; i < 5; ++i) assert(auth.login("", 100 + i, token) == 401);
    assert(auth.login(password, 200, token) == 429);
    const uint64_t now = UINT32_MAX - 100;
    assert(auth.login(password, now, token) == 200);
    assert(token.size() == 64 && auth.authenticated(token, now));
    assert(auth.authenticated(token, now + 200)); // millis() wraparound
    assert(!auth.authenticated(token, now + WebAuth::SessionMs));
    assert(!auth.authenticated(token, now + uint64_t(UINT32_MAX) + 1)); // No revival after 49 days.
    assert(!auth.authenticated(std::string(64, '0'), now));
    const auto cookie = WebAuth::sessionCookie(token, true);
    assert(cookie.find("HttpOnly") != std::string::npos && cookie.find("SameSite=Strict") != std::string::npos);
    assert(cookie.find("Secure") != std::string::npos);
    assert(WebAuth::tokenFromCookie("other=1; " + cookie) == token);
    assert(WebAuth::tokenFromCookie("other_pitclaw_session=" + token).empty());
    assert(auth.gate("GET", "/ws", cookie, "https://bbq:8443", "bbq:8443", now) == 0);
    assert(auth.gate("GET", "/ws", cookie, "https://evil.example", "bbq:8443", now) == 403);
    assert(auth.gate("GET", "/ota/start", cookie, "null", "bbq", now) == 403);
    assert(auth.gate("POST", "/ota/upload", cookie, "https://bbq", "bbq", now) == 0);
    auto persist = [](const WebAuthConfig&) { return true; };
    assert(auth.handle("POST", "/api/auth/settings", "", "replacement password", true, now, false, persist).status == 401);
    auto result = auth.handle("POST", "/api/auth/settings", cookie, "replacement password", true, now, false,
        [](const WebAuthConfig&) { return false; });
    assert(result.status == 500 && strcmp(auth.config().hash, saved.hash) == 0);
    assert(!auth.authenticated(token, now));
    assert(auth.login(password, now, token) == 200);
    auth.logout(token); assert(!auth.authenticated(token, now));
    assert(auth.login(password, now, token) == 200);
    assert(auth.setPassword(password));
    assert(strcmp(auth.config().salt, saved.salt) != 0);
    assert(!auth.authenticated(token, now));
    auth.load(saved);
    assert(auth.login(password, now, token) == 200);
    auth.load(saved); assert(!auth.authenticated(token, now)); // reboot invalidates sessions
    WebAuthConfig corrupt; corrupt.enabled = true;
    auth.load(corrupt);
    assert(auth.login(password, now, token) == 401);
    assert(auth.gate("GET", "/api/version", "", "", "bbq", now) == 401);
    auth.disable(); assert(!auth.enabled() && auth.authenticated("", now));
    // Legacy hashes migrate only after successful verification and persistence.
    WebAuthConfig legacy;
    legacy.enabled = true;
    strcpy(legacy.salt, "00112233445566778899aabbccddeeff");
    strcpy(legacy.hash, "274a463e74516c4753827bf2c5af039fe588e19c0e130986c97085cdfc4c6dc7");
    auth.load(legacy);
    bool persisted = false;
    result = auth.handle("POST", "/api/auth/login", "", "wrong", false, now, false,
        [&persisted](const WebAuthConfig&) { persisted = true; return true; });
    assert(result.status == 401 && !persisted);
    result = auth.handle("POST", "/api/auth/login", "", password, false, now, false,
        [](const WebAuthConfig&) { return false; });
    assert(result.status == 200 && strcmp(auth.config().hash, legacy.hash) == 0);
    const auto beforeMigration = WebAuth::tokenFromCookie(result.cookie);
    WebAuthConfig upgraded;
    result = auth.handle("POST", "/api/auth/login", "", password, false, now, false,
        [&upgraded, &persisted](const WebAuthConfig& cfg) { upgraded = cfg; persisted = true; return true; });
    assert(result.status == 200 && persisted && upgraded.iterations == WebAuth::PasswordIterations);
    assert(strcmp(upgraded.salt, legacy.salt) != 0 && strcmp(upgraded.hash, legacy.hash) != 0);
    assert(auth.authenticated(beforeMigration, now));
    assert(auth.authenticated(WebAuth::tokenFromCookie(result.cookie), now));
    auth.load(upgraded);
    assert(auth.login(password, now, token) == 200);
    for (const auto rounds : {0u, WebAuth::PasswordIterations - 1, WebAuth::LegacyPasswordIterations + 1}) {
        upgraded.iterations = rounds; auth.load(upgraded);
        assert(auth.login(password, now, token) == 401);
    }
    puts("PASS: password policy, legacy hash migration and failure recovery, persisted cost, rate limiting, sessions, cookies and origin checks");
}
