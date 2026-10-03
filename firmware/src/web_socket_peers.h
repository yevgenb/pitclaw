#pragma once
#include <cstdint>
#include <map>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

// ESPAsyncWebServer calls connect/disconnect handlers while holding its client
// list lock. Never call into that library while holding our bookkeeping lock.
class WebSocketPeers {
public:
    void add(uint32_t id, const std::string& token) {
        std::lock_guard<std::mutex> lock(_mutex);
        _tokens[id] = token;
    }
    void remove(uint32_t id) {
        std::lock_guard<std::mutex> lock(_mutex);
        _tokens.erase(id);
    }
    bool token(uint32_t id, std::string& result) const {
        std::lock_guard<std::mutex> lock(_mutex);
        const auto found = _tokens.find(id);
        if (found == _tokens.end()) return false;
        result = found->second;
        return true;
    }
    template <typename Callback>
    void visit(Callback callback) const {
        std::vector<std::pair<uint32_t, std::string>> peers;
        {
            std::lock_guard<std::mutex> lock(_mutex);
            peers.assign(_tokens.begin(), _tokens.end());
        }
        // Sending/closing may acquire the library lock or invoke a callback.
        for (const auto& peer : peers) callback(peer.first, peer.second);
    }
private:
    mutable std::mutex _mutex;
    std::map<uint32_t, std::string> _tokens;
};
