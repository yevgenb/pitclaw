#pragma once
#include <stdint.h>
constexpr int OUTPUT = 1, LOW = 0;
static unsigned long fakeNow;
static bool buzzerSounding;
static unsigned toneCalls;
inline unsigned long millis() { return fakeNow; }
inline void pinMode(int, int) {}
inline void digitalWrite(int, int) {}
inline void setToneChannel(uint8_t) {}
inline void tone(int, unsigned) { buzzerSounding = true; ++toneCalls; }
inline void noTone(int) { buzzerSounding = false; }
struct FakeSerial {
    template <typename... Args> void printf(const char*, Args...) {}
    void println(const char*) {}
};
static FakeSerial Serial;
