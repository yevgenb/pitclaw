#include "web_socket_peers.h"
#include <cassert>
#include <chrono>
#include <future>
#include <mutex>
#include <thread>
#include <cstdio>

int main() {
    WebSocketPeers peers;
    peers.add(300, "first"); // IDs must not truncate to uint8_t.
    std::string token;
    assert(peers.token(300, token) && token == "first");
    assert(!peers.token(44, token));

    // The actual production registry must permit disconnect callbacks during
    // a send. Holding its mutex across visit()'s callback would deadlock here.
    auto reentrant = std::async(std::launch::async, [&] {
        peers.visit([&](uint32_t id, const std::string& saved) {
            assert(saved == "first");
            peers.remove(id);
            peers.add(301, "second");
        });
    });
    assert(reentrant.wait_for(std::chrono::seconds(2)) == std::future_status::ready);
    reentrant.get();
    assert(!peers.token(300, token) && peers.token(301, token) && token == "second");

    // Model ESPAsyncWebServer's real lock ordering: its callback holds the
    // library lock before updating our registry; sending takes that same lock.
    std::mutex libraryLock;
    std::promise<void> libraryHeld, sendStarted, callbackFinished;
    auto callback = std::async(std::launch::async, [&] {
        std::lock_guard<std::mutex> lock(libraryLock);
        libraryHeld.set_value();
        sendStarted.get_future().wait();
        peers.remove(301);
        callbackFinished.set_value();
    });
    auto broadcast = std::async(std::launch::async, [&] {
        libraryHeld.get_future().wait();
        peers.visit([&](uint32_t, const std::string&) {
            sendStarted.set_value();
            std::lock_guard<std::mutex> lock(libraryLock);
        });
    });
    assert(callbackFinished.get_future().wait_for(std::chrono::seconds(2)) == std::future_status::ready);
    assert(callback.wait_for(std::chrono::seconds(2)) == std::future_status::ready);
    assert(broadcast.wait_for(std::chrono::seconds(2)) == std::future_status::ready);
    callback.get(); broadcast.get();
    assert(!peers.token(301, token));
    puts("PASS: WebSocket disconnect/reentrant callbacks and broadcast lock ordering");
}
