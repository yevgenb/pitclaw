// Exercise the actual embedded controller AND real QuickPID, with only its clock/Serial mocked.
#include <cassert>
#include <cmath>
#include <cstdio>
#include <initializer_list>
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
    PidController opened; opened.begin(); opened.setLidDetectionEnabled(false); opened.openLid(0);
    assert(compute(opened,250,250,0)==0 && opened.isLidManual());
    assert(compute(opened,250,250,10000)==0 && opened.isLidOpen());
    opened.resumeLid();
    assert(std::fabs(compute(opened,220,250,14000)-2.4f)<.001f && !opened.isLidOpen());
    PidController adjustable; adjustable.begin();
    assert(adjustable.getLidTimeoutSeconds()==120);
    assert(adjustable.setLidTimeoutSeconds(60)); adjustable.openLid(1000);
    assert(compute(adjustable,250,250,46000)==0 && adjustable.lidRemainingSeconds(46000)==15);
    assert(adjustable.setLidTimeoutSeconds(120));
    assert(adjustable.lidRemainingSeconds(46000)==75); // Extends from original opening, not now.
    assert(adjustable.setLidTimeoutSeconds(30));
    assert(adjustable.lidRemainingSeconds(46000)==0);
    assert(compute(adjustable,220,250,46000)>0 && !adjustable.isLidOpen());
    for (auto invalid : {0,29,31,601,65535}) {
        assert(!adjustable.setLidTimeoutSeconds(invalid));
        assert(adjustable.getLidTimeoutSeconds()==30);
    }
    PidController automatic; automatic.begin(); automatic.setLidTimeoutSeconds(30); pause(automatic);
    assert(compute(automatic,230,250,63999)==0 && automatic.isLidOpen());
    compute(automatic,230,250,64000); assert(!automatic.isLidOpen());
    automatic.begin(); automatic.setLidTimeoutSeconds(600); pause(automatic);
    assert(compute(automatic,230,250,154000)==0 && automatic.isLidOpen());
    compute(automatic,245,250,158000); assert(!automatic.isLidOpen()); // Recovery can end sooner.
    const uint32_t start=UINT32_MAX-1000;
    adjustable.openLid(start); adjustable.setLidTimeoutSeconds(600);
    compute(adjustable,NAN,250,start+599999); assert(adjustable.isLidOpen());
    compute(adjustable,NAN,250,start+600000); assert(!adjustable.isLidOpen());
    std::puts("PASS: real QuickPID cold start and clean history after resume, recovery, timeout and disable");
}
