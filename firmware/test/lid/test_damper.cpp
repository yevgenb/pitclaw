#include <cassert>
#include <cmath>
#include <cstdio>
#include <initializer_list>
#include "damper_setup.h"
#include "control_outputs.h"
#include "servo_controller.cpp"
#include "fan_controller.cpp"

int main() {
    ServoController servo; FanController fan;
    DamperCalibration defaults;
    assert(defaults.pulseAt(0) == 544 && defaults.pulseAt(100) == 1472);
    DamperCalibration reversed; reversed.closedUs = 1600; reversed.openUs = 900;
    assert(reversed.valid());
    servo.setCalibration(reversed); servo.begin();
    assert(servo.getCurrentPulseUs() == 1600 && servo.getCurrentPositionPct() == 0);
    servo.setPosition(50); assert(servo.getCurrentPulseUs() == 1250 && servo.getCurrentPositionPct() == 50);
    servo.setPosition(100); assert(servo.getCurrentPulseUs() == 900 && servo.getCurrentPositionPct() == 100);
    servo.setPosition(NAN); assert(servo.getCurrentPulseUs() == 1600);
    servo.setPosition(-1); assert(servo.getCurrentPulseUs() == 1600);
    servo.setPosition(101); assert(servo.getCurrentPulseUs() == 900);
    DamperCalibration invalid; invalid.closedUs = 900; invalid.openUs = 900;
    servo.setCalibration(invalid); assert(servo.getCalibration().closedUs == 1600);
    servo.setPulseWidth(100); assert(servo.getCurrentPulseUs() == SERVO_MIN_US);
    servo.setPulseWidth(65000); assert(servo.getCurrentPulseUs() == SERVO_MAX_US);

    DamperSetup setup;
    setup.begin(defaults,1472,1000);
    assert(setup.state().pulseUs == 1472 && !setup.state().ready());
    assert(setup.test(0,1000) && setup.state().pulseUs == 544);
    assert(setup.test(50,1000) && setup.state().pulseUs == 1008);
    assert(setup.test(100,1000) && setup.state().pulseUs == 1472);
    assert(!setup.state().closedMarked && !setup.state().openMarked);
    assert(setup.mark(true,1001) && setup.mark(false,1002));
    assert(!setup.state().ready() && setup.test(100,1003)); // Invalid draft falls back to saved positions.
    assert(setup.state().pulseUs == 1472);
    for (int i=0; i<10; ++i) assert(setup.jog(-50,1010+i));
    assert(setup.mark(false,1030) && setup.state().ready());
    assert(setup.state().endpoints.closedUs == 1472 && setup.state().endpoints.openUs == 972);
    assert(setup.test(50,1040) && setup.state().pulseUs == 1222);
    assert(!setup.jog(1000,1041) && !setup.test(25,1041));
    assert(!setup.timeout(1040 + DamperSetup::IDLE_MS - 1));
    assert(setup.timeout(1040 + DamperSetup::IDLE_MS));
    assert(setup.state().active && setup.state().stopped && !setup.mark(true,62000));
    assert(setup.jog(10,62000) && !setup.state().stopped);
    setup.begin(reversed,1250,62001);
    assert(setup.mark(true,62002)); // Only one new endpoint must not change the tested saved range.
    assert(setup.test(0,62003) && setup.state().pulseUs == 1600);
    setup.stop(); assert(setup.test(50,62004) && setup.state().pulseUs == 1250 && !setup.state().stopped);
    assert(setup.timeout(62004 + DamperSetup::IDLE_MS));
    assert(setup.test(100,122005) && setup.state().pulseUs == 900 && !setup.state().stopped);
    setup.begin(defaults,SERVO_MIN_US,0xfffffff0u);
    assert(!setup.timeout(100) && setup.timeout(uint32_t(0xfffffff0u + DamperSetup::IDLE_MS)));
    setup.begin(defaults,SERVO_MIN_US,0); setup.jog(-50,1); assert(setup.state().pulseUs==SERVO_MIN_US);
    setup.begin(defaults,SERVO_MAX_US,0); setup.jog(50,1); assert(setup.state().pulseUs==SERVO_MAX_US);
    setup.end(); assert(!setup.jog(10,2) && !setup.mark(false,2) && !setup.test(0,2));

    for (auto mode : {"fan_only","fan_and_damper","damper_primary"}) {
        for (bool ready : {false,true}) {
            fan.setManualDuty(255); servo.setPulseWidth(1222);
            applyControlOutputs(fan,servo,ready,100,mode,30,false,true);
            fan.update(); assert(fan.getCurrentDuty()==0 && !fan.isKickStarting());
            assert(servo.getCurrentPulseUs()==1222); // No automatic/fault-driven sweep during manual setup.
        }
        applyControlOutputs(fan,servo,false,100,mode,30);
        assert(servo.getCurrentPulseUs()==1600 && fan.getCurrentDuty()==0); // Calibrated fault-close after exit.
    }
    std::puts("PASS: servo endpoints, reversed travel, manual setup, limits, idle stop and blower override");
}
