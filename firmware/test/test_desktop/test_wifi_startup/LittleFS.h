#pragma once
#include <algorithm>
#include <cstring>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

struct File {
    std::shared_ptr<std::vector<uint8_t>> bytes;
    size_t cursor = 0;
    bool failWrite = false;
    unsigned* writeCount = nullptr;
    std::function<void()> onWrite;
    explicit operator bool() const { return bool(bytes); }
    size_t size() const { return bytes->size(); }
    size_t read(uint8_t* data, size_t count) {
        count = std::min(count, bytes->size() - cursor);
        std::memcpy(data, bytes->data() + cursor, count); cursor += count; return count;
    }
    size_t write(const uint8_t* data, size_t count) {
        ++*writeCount;
        if (failWrite) return 0;
        bytes->assign(data, data + count);
        if (onWrite) onWrite();
        return count;
    }
    void close() {}
};
struct FakeFS {
    std::map<std::string, std::shared_ptr<std::vector<uint8_t>>> files;
    unsigned writeCount = 0;
    bool failWrite = false, failRename = false;
    std::function<void()> onWrite;
    size_t totalBytes() const { return 4 * 1024 * 1024; }
    bool exists(const char* path) const { return files.count(path); }
    File open(const char* path, const char* mode) {
        if (*mode == 'r' && !exists(path)) return {};
        if (*mode == 'w') files[path] = std::make_shared<std::vector<uint8_t>>();
        return {files[path], 0, failWrite, &writeCount, onWrite};
    }
    bool rename(const char* from, const char* to) {
        if (failRename || !exists(from)) return false;
        files[to] = files[from]; files.erase(from); return true;
    }
    bool remove(const char* path) { return files.erase(path) != 0; }
};
static FakeFS LittleFS;
