#pragma once
#include <cstdint>
#include <mutex>

// Fixed-size records only. No strings, credentials, or per-packet logging.
class WifiEventLog {
public:
    static constexpr unsigned Capacity = 32;
    static constexpr uint32_t SaveIntervalMs = 60000;
    static constexpr const char* Path = "/wifi-events.bin";
    static constexpr const char* TemporaryPath = "/wifi-events.tmp";
    enum Kind : uint8_t { Boot, Started, Stopped, Associated, Disconnected, GotIP, LostIP, AuthChanged };
    struct Event {
        uint32_t timestamp = 0, uptimeMs = 0, boot = 0, freeHeap = 0, statusBits = 0;
        uint8_t ip[4] = {}, gateway[4] = {};
        uint8_t kind = Boot, reason = 0, status = 0;
        int8_t rssi = 0;
    };
    struct Image {
        uint32_t magic = 0x57494649;
        uint16_t version = 1, count = 0, next = 0, reserved = 0;
        uint32_t boot = 0;
        Event events[Capacity] = {};
    };
    static_assert(sizeof(Event) == 32, "Wi-Fi event storage must remain bounded");
    static_assert(sizeof(Image) == 1040, "Update the log format before changing records");

    void startBoot(Event event) {
        std::lock_guard<std::mutex> lock(_mutex);
        ++_image.boot;
        event.kind = Boot;
        append(event);
    }
    void record(Event event) {
        std::lock_guard<std::mutex> lock(_mutex);
        append(event);
    }
    Image snapshot() const {
        std::lock_guard<std::mutex> lock(_mutex);
        return _image;
    }
    bool pending() const {
        std::lock_guard<std::mutex> lock(_mutex);
        return _generation != _savedGeneration;
    }
    bool lastSaveOK() const {
        std::lock_guard<std::mutex> lock(_mutex);
        return _lastSaveOK;
    }
    static const Event& chronological(const Image& image, unsigned index) {
        return image.events[(image.next + Capacity - image.count + index) % Capacity];
    }
    static const char* name(uint8_t kind) {
        static const char* names[] = {"boot", "station_started", "station_stopped", "associated",
            "disconnected", "got_ip", "lost_ip", "authentication_changed"};
        return kind <= AuthChanged ? names[kind] : "unknown";
    }
    template<class FileSystem> bool load(FileSystem& fs) {
        if (!fs.exists(Path)) return false;
        auto file = fs.open(Path, "r");
        if (!file) return false;
        Image image;
        const bool complete = file.size() == sizeof(image) &&
            file.read(reinterpret_cast<uint8_t*>(&image), sizeof(image)) == sizeof(image);
        file.close();
        if (!complete || image.magic != 0x57494649 || image.version != 1 ||
            image.count > Capacity || image.next >= Capacity ||
            (image.count < Capacity && image.next != image.count)) return false;
        for (unsigned i = 0; i < image.count; ++i)
            if (chronological(image, i).kind > AuthChanged) return false;
        std::lock_guard<std::mutex> lock(_mutex);
        _image = image;
        _generation = _savedGeneration = 0;
        _lastSaveOK = true;
        return true;
    }
    // Called from the control loop, never from the Wi-Fi callback. A snapshot
    // write releases our lock so networking can continue recording events.
    template<class FileSystem> void persist(FileSystem& fs, uint32_t now) {
        Image image;
        uint32_t generation;
        {
            std::lock_guard<std::mutex> lock(_mutex);
            if (_generation == _savedGeneration ||
                (_attemptedSave && uint32_t(now - _lastSaveAt) < SaveIntervalMs)) return;
            image = _image;
            generation = _generation;
            _lastSaveAt = now;
            _attemptedSave = true;
        }
        auto file = fs.open(TemporaryPath, "w");
        bool saved = false;
        if (file) {
            saved = file.write(reinterpret_cast<const uint8_t*>(&image), sizeof(image)) == sizeof(image);
            file.close();
            saved = saved && fs.rename(TemporaryPath, Path);
        }
        if (!saved) fs.remove(TemporaryPath);
        std::lock_guard<std::mutex> lock(_mutex);
        _lastSaveOK = saved;
        if (saved) _savedGeneration = generation;
    }

private:
    void append(Event event) {
        event.boot = _image.boot;
        _image.events[_image.next] = event;
        _image.next = (_image.next + 1) % Capacity;
        if (_image.count < Capacity) ++_image.count;
        ++_generation;
    }
    mutable std::mutex _mutex;
    Image _image;
    uint32_t _generation = 0, _savedGeneration = 0, _lastSaveAt = 0;
    bool _attemptedSave = false, _lastSaveOK = false;
};
