#pragma once
#include <string>
#include <cstdint>
using String = std::string;
inline unsigned long millis() { return 10000; }
struct TestSerial {
    void println(const char*) {}
    template<typename... Args> void printf(const char*, Args...) {}
};
static TestSerial Serial;
