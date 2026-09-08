#pragma once

#include <stdint.h>

// Hardware boundary fake: compile the real driver's embedded branch on the host.
constexpr int OUTPUT = 1;
constexpr int LOW = 0;
struct FakeSerial {
    void println(const char*) {}
    template <typename... Args> void printf(const char*, Args...) {}
};
static FakeSerial Serial;
static unsigned long fakeNow;
static bool failSetup;
static unsigned setupFrequency, setupResolution;
static int attachedPin, outputLevel;
static uint32_t outputDuty;
static unsigned writeCount;
static uint8_t toneChannel;

inline unsigned long millis() { return fakeNow; }
inline void pinMode(int, int) {}
inline void digitalWrite(int, int level) { outputLevel = level; }
inline uint32_t ledcSetup(uint8_t, uint32_t frequency, uint8_t bits) {
    setupFrequency = frequency;
    setupResolution = bits;
    return failSetup ? 0 : frequency;
}
inline void ledcAttachPin(int pin, uint8_t) { attachedPin = pin; }
inline void ledcWrite(uint8_t, uint32_t duty) { outputDuty = duty; ++writeCount; }
inline void setToneChannel(uint8_t channel) { toneChannel = channel; }
inline void tone(int, unsigned) {}
inline void noTone(int) {}
