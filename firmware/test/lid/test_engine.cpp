// Exercise the actual embedded controller AND real QuickPID, with only its clock/Serial mocked.
#include <cassert>
#include <cmath>
#include <cstdio>
#include "pid_controller.h"
uint32_t testNow = 0;
static float compute(PidController& p, float t, float sp, uint32_t ms) {
    testNow = ms; return p.compute(t,sp);
}
static void pause(PidController& p) {
    compute(p,246,250,0); compute(p,246,250,30000);
    assert(compute(p,230,250,34000)==0 && p.isLidOpen());
}
int main() {
    PidController cold; cold.begin();
    assert(compute(cold,70,250,0)>0 && !cold.isLidOpen());
    PidController manual; manual.begin(); pause(manual); manual.resumeLid();
    assert(std::fabs(compute(manual,220,250,38000)-2.4f)<.001f && !manual.isLidOpen());
    PidController recovery; recovery.begin(); pause(recovery);
    assert(std::fabs(compute(recovery,245,250,38000)-.4f)<.001f && !recovery.isLidOpen());
    PidController timeout; timeout.begin(); pause(timeout);
    assert(std::fabs(compute(timeout,200,250,154000)-4.0f)<.001f && !timeout.isLidOpen());
    assert(compute(timeout,200,250,158000)>0 && !timeout.isLidOpen());
    PidController disabled; disabled.begin(); pause(disabled); disabled.setLidDetectionEnabled(false);
    assert(std::fabs(compute(disabled,230,250,38000)-1.6f)<.001f && !disabled.isLidOpen());
    std::puts("PASS: real QuickPID cold start and clean history after resume, recovery, timeout and disable");
}
