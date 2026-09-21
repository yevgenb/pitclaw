#pragma once
#include <stdint.h>
#include <cmath>
extern uint32_t testNow;
inline uint32_t millis() { return testNow; }
inline uint32_t micros() { return testNow * 1000u; }
#define constrain(x,lo,hi) ((x)<(lo)?(lo):((x)>(hi)?(hi):(x)))
struct TestSerial { template<class... T> void printf(const char*,T...) {} void println(const char*) {} };
static TestSerial Serial;
