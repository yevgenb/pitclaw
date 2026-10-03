#pragma once
#include <cstdint>
#include <mutex>
#include <string>
#include <functional>

struct WebAuthConfig {
    bool enabled = false;
    char salt[33] = {};
    char hash[65] = {};
    // Records written before this field existed used 600,000 rounds.
    uint32_t iterations = 600000;
};
struct WebAuthReply { int status; std::string body; std::string cookie; };

// Shared policy for the ESP32 server and desktop simulator. Credentials are
// persisted by the caller; session tokens live only in RAM.
class WebAuth {
public:
    static constexpr uint32_t SessionMs = 12 * 60 * 60 * 1000;
    static constexpr unsigned PasswordIterations = 20000;
    static constexpr unsigned LegacyPasswordIterations = 600000;
    static constexpr unsigned MinPasswordLength = 8;
    static constexpr unsigned MaxPasswordBytes = 128;
    void load(const WebAuthConfig& config);
    WebAuthConfig config() const;
    bool enabled() const;
    bool authenticated(const std::string& token, uint64_t now) const;
    int login(const std::string& password, uint64_t now, std::string& token);
    bool setPassword(const std::string& password);
    void disable();
    void logout(const std::string& token);

    // Only the bundled shell and login/status routes are public. Unknown paths
    // require a session too; private LittleFS files are never HTTP resources.
    int gate(const std::string& method, const std::string& path,
             const std::string& cookie, const std::string& origin,
             const std::string& host, uint64_t now) const;
    static bool publicAsset(const std::string& path);
    static std::string tokenFromCookie(const std::string& cookie);
    static std::string sessionCookie(const std::string& token, bool secure);
    WebAuthReply handle(const std::string& method, const std::string& path,
        const std::string& cookie, const std::string& password, bool enable,
        uint64_t now, bool secure, const std::function<bool(const WebAuthConfig&)>& persist);
private:
    static bool validPassword(const std::string& password);
    struct Session { std::string token; uint64_t created = 0; };
    mutable std::mutex _mutex;
    std::mutex _credentialMutex;
    WebAuthConfig _config;
    Session _sessions[8];
    unsigned _failures = 0;
    uint64_t _failureStart = 0;
};
