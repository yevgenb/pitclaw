#pragma once
#include <stdint.h>
#include <string>
using String = std::string;
template <typename T> T min(T a, T b) { return a < b ? a : b; }
static unsigned long fakeNow;
inline unsigned long millis() { return fakeNow; }
inline void delay(unsigned long ms) { fakeNow += ms; }
struct FakeSerial {
    void println(const char* = "") {}
    void print(const char*) {}
    template <typename... Args> void printf(const char*, Args...) {}
};
static FakeSerial Serial;
