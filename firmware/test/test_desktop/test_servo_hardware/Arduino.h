#pragma once
#include <stdint.h>
#include <vector>
constexpr int OUTPUT = 1, LOW = 0, HIGH = 1;
struct FakeSerial {
    void println(const char*) {}
    template <typename... Args> void printf(const char*, Args...) {}
};
static FakeSerial Serial;
struct PwmChannel { uint32_t frequency = 0, duty = 0; uint8_t bits = 0; };
struct PwmCall { char type; int pinOrChannel; uint32_t value; };
static PwmChannel channels[8];
static std::vector<PwmCall> calls;
static bool failSetup;
static bool attachReadsPreviousDuty;
static int pinChannel[64];
static int pinLevel[64];
static bool inputEnabled[64];
inline void pinMode(int, int) {}
inline void digitalWrite(int pin, int level) { pinLevel[pin]=level; calls.push_back({'L',pin,uint32_t(level)}); }
inline uint32_t ledcSetup(uint8_t channel, uint32_t frequency, uint8_t bits) {
    calls.push_back({'S',channel,frequency});
    if (failSetup || channel >= 8 || bits > 14) return 0;
    // Real LEDC channels share timers in pairs.
    for (int i=(channel/2)*2; i<(channel/2)*2+2; ++i) {
        channels[i].frequency=frequency; channels[i].bits=bits;
    }
    return frequency;
}
inline void ledcAttachPin(int pin, uint8_t channel) {
    pinChannel[pin]=channel; calls.push_back({'A',pin,channels[channel].duty});
    if (attachReadsPreviousDuty) channels[channel].duty=0;
}
inline void ledcDetachPin(int pin) { pinChannel[pin]=-1; calls.push_back({'D',pin,0}); }
inline void ledcWrite(uint8_t channel, uint32_t duty) { channels[channel].duty=duty; calls.push_back({'W',channel,duty}); }
inline uint32_t ledcRead(uint8_t channel) { return channels[channel].duty; }
inline uint32_t ledcReadFreq(uint8_t channel) { return channels[channel].duty ? channels[channel].frequency : 0; }
inline unsigned long pulseIn(int pin, int level, unsigned long timeout) {
    calls.push_back({'R',pin,uint32_t(timeout)});
    if (!inputEnabled[pin] || pinChannel[pin] < 0) return 0;
    const auto& c = channels[pinChannel[pin]];
    if (!c.duty || !c.frequency) return 0;
    const unsigned long period = 1000000UL / c.frequency;
    const unsigned long high = uint64_t(c.duty) * period / (1UL << c.bits);
    return level == HIGH ? high : period-high;
}
