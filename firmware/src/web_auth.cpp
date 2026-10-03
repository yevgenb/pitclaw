#include "web_auth.h"
#include <cstring>
#if !defined(NATIVE_BUILD) || defined(SIMULATOR_BUILD)
#ifdef SIMULATOR_BUILD
#include "simulator/mongoose.h"
#else
#include <Arduino.h>
#include <esp_system.h>
#include <mbedtls/md.h>
#endif

namespace {
bool randomHex(char* output, size_t bytes) {
    uint8_t random[32];
#ifdef SIMULATOR_BUILD
    if (!mg_random(random, bytes)) return false;
#else
    esp_fill_random(random, bytes);
#endif
    const char* hex = "0123456789abcdef";
    for (size_t i = 0; i < bytes; ++i) {
        output[i * 2] = hex[random[i] >> 4];
        output[i * 2 + 1] = hex[random[i] & 15];
    }
    output[bytes * 2] = 0;
    return true;
}
bool validHex(const char* value, size_t len) {
    if (strlen(value) != len) return false;
    return strspn(value, "0123456789abcdef") == len;
}
bool equal(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    unsigned diff = 0;
    for (size_t i = 0; i < a.size(); ++i) diff |= a[i] ^ b[i];
    return diff == 0;
}
bool derive(const std::string& password, const char* salt, unsigned iterations, char* output) {
    if (!validHex(salt, 32) || iterations < WebAuth::PasswordIterations ||
        iterations > WebAuth::LegacyPasswordIterations) return false;
    uint8_t block[20] = {}, u[32], result[32];
    for (unsigned i = 0; i < 16; ++i) {
        auto digit = [](char c) { return c <= '9' ? c - '0' : c - 'a' + 10; };
        block[i] = (digit(salt[i * 2]) << 4) | digit(salt[i * 2 + 1]);
    }
    block[19] = 1; // PBKDF2's big-endian block index
#ifndef SIMULATOR_BUILD
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    if (mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1)) {
        mbedtls_md_free(&ctx); return false;
    }
    mbedtls_md_hmac_starts(&ctx, reinterpret_cast<const uint8_t*>(password.data()), password.size());
#endif
    for (unsigned iteration = 0; iteration < iterations; ++iteration) {
        uint8_t* data = iteration ? u : block;
        const size_t size = iteration ? sizeof(u) : sizeof(block);
#ifdef SIMULATOR_BUILD
        mg_hmac_sha256(u, reinterpret_cast<uint8_t*>(const_cast<char*>(password.data())), password.size(), data, size);
#else
        mbedtls_md_hmac_reset(&ctx);
        mbedtls_md_hmac_update(&ctx, data, size);
        mbedtls_md_hmac_finish(&ctx, u);
        if (iteration % 512 == 0) delay(1); // Keep the control task and watchdog running.
#endif
        if (!iteration) memcpy(result, u, sizeof(result));
        else for (unsigned i = 0; i < sizeof(result); ++i) result[i] ^= u[i];
    }
#ifndef SIMULATOR_BUILD
    mbedtls_md_free(&ctx);
#endif
    const char* hex = "0123456789abcdef";
    for (unsigned i = 0; i < sizeof(result); ++i) {
        output[i * 2] = hex[result[i] >> 4]; output[i * 2 + 1] = hex[result[i] & 15];
    }
    output[64] = 0;
    return true;
}
}

void WebAuth::load(const WebAuthConfig& config) {
    std::lock_guard<std::mutex> lock(_mutex);
    _config = config;
    _config.salt[32] = 0; _config.hash[64] = 0;
    _failures = 0; _failureStart = 0;
    for (auto& session : _sessions) session = {};
}
WebAuthConfig WebAuth::config() const {
    std::lock_guard<std::mutex> lock(_mutex); return _config;
}
bool WebAuth::enabled() const { return config().enabled; }
bool WebAuth::authenticated(const std::string& token, uint64_t now) const {
    std::lock_guard<std::mutex> lock(_mutex);
    if (!_config.enabled) return true;
    if (token.size() != 64) return false;
    for (const auto& session : _sessions)
        if (equal(token, session.token) && now - session.created < SessionMs) return true;
    return false;
}
int WebAuth::login(const std::string& password, uint64_t now, std::string& token) {
    WebAuthConfig cfg;
    {
        std::lock_guard<std::mutex> lock(_mutex);
        if (!_config.enabled) { token.clear(); return 200; }
        if (_failures && now - _failureStart >= 60000) _failures = 0;
        if (_failures >= 5) return 429;
        if (!_failures) _failureStart = now;
        ++_failures;
        cfg = _config;
    }
    char hash[65] = {}, random[65] = {};
    if (password.empty() || password.size() > MaxPasswordBytes || !validHex(cfg.hash, 64) ||
        !derive(password, cfg.salt, cfg.iterations, hash) || !equal(hash, cfg.hash)) return 401;
    if (!randomHex(random, 32)) return 503;
    std::lock_guard<std::mutex> lock(_mutex);
    if (!_config.enabled || cfg.iterations != _config.iterations ||
        strcmp(cfg.hash, _config.hash) || strcmp(cfg.salt, _config.salt)) return 401;
    _failures = 0;
    Session* slot = &_sessions[0];
    for (auto& session : _sessions) {
        if (session.token.empty() || now - session.created >= SessionMs) { slot = &session; break; }
        if (now - session.created > now - slot->created) slot = &session;
    }
    token = random; slot->token = token; slot->created = now;
    return 200;
}
bool WebAuth::validPassword(const std::string& password) {
    if (password.size() < MinPasswordLength || password.size() > MaxPasswordBytes) return false;
    unsigned characters = 0;
    for (size_t i = 0; i < password.size();) {
        const uint8_t lead = uint8_t(password[i]);
        unsigned width;
        uint32_t value, minimum;
        if (lead < 0x80) { width = 1; value = lead; minimum = 0; }
        else if (lead >= 0xc2 && lead <= 0xdf) { width = 2; value = lead & 0x1f; minimum = 0x80; }
        else if (lead >= 0xe0 && lead <= 0xef) { width = 3; value = lead & 0x0f; minimum = 0x800; }
        else if (lead >= 0xf0 && lead <= 0xf4) { width = 4; value = lead & 7; minimum = 0x10000; }
        else return false;
        if (i + width > password.size()) return false;
        for (unsigned j = 1; j < width; ++j) {
            const uint8_t next = uint8_t(password[i + j]);
            if ((next & 0xc0) != 0x80) return false;
            value = (value << 6) | (next & 0x3f);
        }
        if (!value || value < minimum || value > 0x10ffff || (value >= 0xd800 && value <= 0xdfff)) return false;
        ++characters; i += width;
    }
    return characters >= MinPasswordLength;
}
bool WebAuth::setPassword(const std::string& password) {
    if (!validPassword(password)) return false;
    WebAuthConfig cfg;
    cfg.enabled = true;
    cfg.iterations = PasswordIterations;
    if (!randomHex(cfg.salt, 16) || !derive(password, cfg.salt, cfg.iterations, cfg.hash)) return false;
    load(cfg);
    return true;
}
void WebAuth::disable() { load({}); }
void WebAuth::logout(const std::string& token) {
    std::lock_guard<std::mutex> lock(_mutex);
    for (auto& session : _sessions) if (equal(session.token, token)) session = {};
}
bool WebAuth::publicAsset(const std::string& path) {
    return path == "/" || path == "/index.html" || path == "/app.js" ||
        path == "/style.css" || path == "/sw.js" || path == "/favicon.svg" || path == "/manifest.json";
}
int WebAuth::gate(const std::string& method, const std::string& path,
                  const std::string& cookie, const std::string& origin,
                  const std::string& host, uint64_t now) const {
    // Protect authenticated commands and auth setup from foreign origins.
    // While auth is off, retain legacy anonymous access through proxies that
    // have not installed the Host forwarding required by authenticated mode.
    const bool checkOrigin = enabled() || path.compare(0, 9, "/api/auth") == 0;
    if (checkOrigin && (method != "GET" || path == "/ws" || path == "/ota/start")) {
        if (!origin.empty() && origin != "http://" + host && origin != "https://" + host) return 403;
    }
    if (publicAsset(path) && method == "GET") return 0;
    if (path == "/api/auth" && method == "GET") return 0;
    if (path == "/api/auth/login" && method == "POST") return 0;
    return authenticated(tokenFromCookie(cookie), now) ? 0 : 401;
}
std::string WebAuth::tokenFromCookie(const std::string& cookie) {
    size_t start = 0;
    while (start < cookie.size()) {
        size_t end = cookie.find(';', start);
        if (end == std::string::npos) end = cookie.size();
        while (start < end && cookie[start] == ' ') ++start;
        const std::string name = "pitclaw_session=";
        if (cookie.compare(start, name.size(), name) == 0) return cookie.substr(start + name.size(), end - start - name.size());
        start = end + 1;
    }
    return {};
}
std::string WebAuth::sessionCookie(const std::string& token, bool secure) {
    return "pitclaw_session=" + token + "; Path=/; HttpOnly; SameSite=Strict; Max-Age=" +
        (token.empty() ? "0" : "43200") + (secure ? "; Secure" : "");
}

WebAuthReply WebAuth::handle(const std::string& method, const std::string& path,
    const std::string& cookie, const std::string& password, bool enable,
    uint64_t now, bool secure, const std::function<bool(const WebAuthConfig&)>& persist) {
    const auto token = tokenFromCookie(cookie);
    if (path == "/api/auth" && method == "GET") {
        return {200, std::string("{\"enabled\":") + (enabled() ? "true" : "false") +
            ",\"authenticated\":" + (authenticated(token, now) ? "true" : "false") + "}", {}};
    }
    if (method != "POST") return {405, "{\"error\":\"Method not allowed\"}", {}};
    if (path == "/api/auth/login") {
        std::lock_guard<std::mutex> credentials(_credentialMutex);
        const auto previous = config();
        std::string issued;
        const int status = login(password, now, issued);
        // Verify legacy hashes at their original cost once, then persist a new
        // salt and the embedded-device cost. Keep all issued sessions valid.
        if (status == 200 && previous.enabled && previous.iterations > PasswordIterations) {
            WebAuthConfig upgraded;
            upgraded.enabled = true;
            upgraded.iterations = PasswordIterations;
            if (randomHex(upgraded.salt, 16) && derive(password, upgraded.salt, upgraded.iterations, upgraded.hash) && persist(upgraded)) {
                std::lock_guard<std::mutex> lock(_mutex);
                _config = upgraded;
            }
        }
        return {status, status == 200 ? "{\"ok\":true}" : status == 429 ?
            "{\"error\":\"Too many attempts. Try again in one minute.\"}" :
            "{\"error\":\"Incorrect password\"}", status == 200 ? sessionCookie(issued, secure) : ""};
    }
    if (!authenticated(token, now)) return {401, "{\"error\":\"Sign in required\"}", {}};
    if (path == "/api/auth/logout") {
        logout(token);
        return {200, "{\"ok\":true}", sessionCookie({}, secure)};
    }
    if (path == "/api/auth/settings") {
        std::lock_guard<std::mutex> credentials(_credentialMutex);
        if (!authenticated(token, now)) return {401, "{\"error\":\"Sign in required\"}", {}};
        const auto previous = config();
        if (enable) {
            if (!validPassword(password)) return {400,
                "{\"error\":\"Use 8 or more characters (maximum 128 UTF-8 bytes)\"}", {}};
            if (!setPassword(password)) return {503, "{\"error\":\"Could not set password\"}", {}};
        } else disable();
        if (!persist(config())) {
            load(previous);
            return {500, "{\"error\":\"Could not save authentication settings\"}", {}};
        }
        // Password changes revoke every session, including the caller's.
        return {200, "{\"ok\":true}", sessionCookie({}, secure)};
    }
    return {404, "{\"error\":\"Not found\"}", {}};
}
#endif
