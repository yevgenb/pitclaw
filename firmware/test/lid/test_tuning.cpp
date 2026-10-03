// Drive the real embedded controller/library with measured-temperature fixtures.
// These check output response, not a prediction of any particular smoker's overshoot.
#include <cassert>
#include <cmath>
#include <cstdio>
#include "pid_controller.h"
#include "split_range.h"
uint32_t testNow = 0;
struct Response { unsigned fanStarts = 0, fullOutput = 0; float fanAtTwoMinutes = 0; };
static Response stalled(float ki) {
    PidController pid; pid.begin(PID_KP, ki, PID_KD);
    Response result;
    for (unsigned seconds = 0; seconds <= 600; seconds += 4) {
        testNow = seconds * 1000;
        float output = pid.compute(210, 225);
        assert(!pid.isLidOpen()); // Initial warm-up must never become a lid pause.
        assert(std::isfinite(output) && output >= 0 && output <= 100);
        auto actuators = splitRange(output, "fan_and_damper", FAN_ON_THRESHOLD);
        if (actuators.fanPercent > 0 && !result.fanStarts) result.fanStarts = seconds;
        if (output == 100 && !result.fullOutput) result.fullOutput = seconds;
        if (seconds == 120) result.fanAtTwoMinutes = actuators.fanPercent;
    }
    // Rising above the target still removes heat demand rather than holding max.
    for (unsigned seconds = 604; seconds <= 1500; seconds += 4) {
        testNow = seconds * 1000;
        pid.compute(250, 225);
    }
    assert(pid.getOutput() == 0);
    return result;
}
int main() {
    const auto old = stalled(0.02f), tuned = stalled(PID_KI);
    assert(old.fanStarts >= 96 && old.fanStarts <= 100 && tuned.fanStarts <= 68);
    assert(old.fullOutput >= 328 && tuned.fullOutput <= 224);
    assert(old.fanAtTwoMinutes < 11 && tuned.fanAtTwoMinutes > 35);
    std::printf("PASS: 210F/225F fixture: fan starts %us -> %us, full demand %us -> %us; above-target demand returns to zero\n",
                old.fanStarts, tuned.fanStarts, old.fullOutput, tuned.fullOutput);
}
