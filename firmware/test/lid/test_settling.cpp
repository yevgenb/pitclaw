// Exercise production PID behavior with real QuickPID and the fake Arduino clock.
// Temperature fixtures verify demand, not the physical smoker's overshoot.
#include <cassert>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <initializer_list>
#include <deque>
#include "pid_controller.h"

uint32_t testNow = 0;

struct Reference {
    float input = 0, output = 0, setpoint = 225;
    QuickPID pid;

    Reference(float temperature, QuickPID::iAwMode mode)
        : input(temperature), pid(&input, &output, &setpoint, PID_KP, PID_KI, PID_KD,
              QuickPID::pMode::pOnMeas, QuickPID::dMode::dOnMeas,
              mode, QuickPID::Action::direct) {
        pid.SetOutputLimits(0, 100);
        pid.SetSampleTimeUs(PID_SAMPLE_MS * 1000UL);
        pid.Reset();
        pid.SetMode(QuickPID::Control::automatic);
    }

    float compute(float temperature) {
        input = temperature;
        pid.Compute();
        return output;
    }
};

static float compute(PidController& pid, float temperature, float target, unsigned seconds) {
    testNow = seconds * 1000;
    const float output = pid.compute(temperature, target);
    assert(std::isfinite(output) && output >= 0 && output <= 100);
    return output;
}

static void matchesReference(PidController& pid, Reference& reference,
                             float temperature, float target, unsigned seconds) {
    const float actual = compute(pid, temperature, target, seconds);
    const float expected = reference.compute(temperature);
    assert(std::fabs(actual - expected) < .001f);
}

static void persistentShortfall() {
    testNow = 0;
    PidController pid; pid.begin();
    Reference legacy(224, QuickPID::iAwMode::iAwCondition);
    for (unsigned seconds = 0; seconds <= 1200; seconds += 4) {
        const float temperature = 224 + .6f * std::sin(seconds * 2 * 3.141592653589793 / 120);
        assert(temperature < 225);
        compute(pid, temperature, 225, seconds);
        legacy.compute(temperature);
        assert(!pid.isLidOpen());
    }
    // A persistent one-degree shortfall must build useful demand despite ripple.
    assert(pid.getOutput() > 30);
    assert(pid.getOutput() > legacy.output + 20);
    std::printf("PASS: noisy one-degree shortfall: final demand %.2f%% versus legacy %.2f%%\n",
                pid.getOutput(), legacy.output);
}

static void warmupAndHysteresis() {
    testNow = 0;
    PidController pid; pid.begin();
    Reference reference(82, QuickPID::iAwMode::iAwCondition);
    for (unsigned seconds = 0; seconds <= 300; seconds += 4) {
        const float temperature = 82 + 130.0f * seconds / 300;
        matchesReference(pid, reference, temperature, 225, seconds);
    }
    // Enter clamping at a 10F error; remain there throughout the 10..15F band.
    reference.pid.SetAntiWindupMode(QuickPID::iAwMode::iAwClamp);
    unsigned seconds = 304;
    for (float temperature : {215.0f, 214.0f, 213.0f, 214.5f, 210.0f}) {
        matchesReference(pid, reference, temperature, 225, seconds);
        seconds += 4;
    }
    reference.pid.SetAntiWindupMode(QuickPID::iAwMode::iAwCondition);
    for (float temperature : {209.5f, 210.5f, 212.0f, 214.0f}) {
        matchesReference(pid, reference, temperature, 225, seconds);
        seconds += 4;
    }
    reference.pid.SetAntiWindupMode(QuickPID::iAwMode::iAwClamp);
    matchesReference(pid, reference, 215, 225, seconds);
    std::puts("PASS: cold warm-up matches legacy; mode hysteresis retains PID history");
}

static void resetsAndOvershoot() {
    PidController pid; pid.begin();
    for (unsigned seconds = 0; seconds <= 240; seconds += 4)
        compute(pid, 222, 225, seconds);
    assert(pid.getOutput() > 20);
    // Heating demand must unwind on sustained overshoot.
    for (unsigned seconds = 244; seconds <= 600; seconds += 4)
        compute(pid, 228, 225, seconds);
    assert(pid.getOutput() == 0);

    pid.begin();
    for (unsigned seconds = 0; seconds <= 240; seconds += 4)
        compute(pid, 222, 225, seconds);
    compute(pid, NAN, 225, 244);
    assert(pid.getOutput() == 0);
    testNow = 248000;
    Reference fresh(210, QuickPID::iAwMode::iAwCondition);
    matchesReference(pid, fresh, 210, 225, 248);

    // A target change resets settling and accumulated demand.
    testNow = 252000;
    Reference changed(230, QuickPID::iAwMode::iAwCondition);
    changed.setpoint = 250;
    matchesReference(pid, changed, 230, 250, 252);

    pid.openLid(256000);
    assert(compute(pid, 248, 250, 256) == 0 && pid.isLidOpen());
    pid.resumeLid();
    testNow = 260000;
    Reference resumed(220, QuickPID::iAwMode::iAwCondition);
    resumed.setpoint = 250;
    matchesReference(pid, resumed, 220, 250, 260);
    assert(!pid.isLidOpen());

    pid.setEnabled(false);
    assert(compute(pid, 249, 250, 264) == 0);
    pid.setEnabled(true);
    assert(compute(pid, 249, 250, 268) > 0);
    assert(pid.getKp() == float(PID_KP) && pid.getKi() == float(PID_KI) && pid.getKd() == float(PID_KD));
    std::puts("PASS: overshoot removes demand; probe, target, lid and disable reset history");
}

struct ThermalResult { double mean = 0, peak = 0; };

static ThermalResult thermalResponse(bool legacy, bool hotRestart) {
    testNow = 0;
    double temperature = hotRestart ? 224 : 82, sensor = temperature;
    PidController pid; pid.begin();
    Reference reference(temperature, QuickPID::iAwMode::iAwCondition);
    std::deque<float> delayedDemand(16, 0);
    ThermalResult result;
    float demand = 0;
    // Illustrative lit-fire plant, not calibrated to the physical smoker:
    // 300s time constant, 15s transport delay, and 30% demand needed at 225F.
    for (unsigned seconds = 0; seconds < 7200; ++seconds) {
        const double noise = .65 * std::sin(seconds * 2 * 3.141592653589793 / 45)
                           + .25 * std::sin(seconds * 2 * 3.141592653589793 / 17);
        sensor += .2 * (temperature + noise - sensor);
        if (seconds % 4 == 0) {
            testNow = seconds * 1000;
            demand = legacy ? reference.compute(sensor) : compute(pid, sensor, 225, seconds);
        }
        delayedDemand.push_back(demand);
        const float effectiveDemand = delayedDemand.front(); delayedDemand.pop_front();
        temperature += (195 + effectiveDemand - temperature) * (1 - std::exp(-1.0 / 300));
        result.peak = std::max(result.peak, temperature);
        if (seconds >= 6000) result.mean += temperature / 1200;
    }
    return result;
}

static void closedLoopFixtures() {
    for (bool hotRestart : {false, true}) {
        const auto legacy = thermalResponse(true, hotRestart);
        const auto settling = thermalResponse(false, hotRestart);
        assert(legacy.mean < 223);
        assert(settling.mean > 224.8 && settling.mean < 225.2);
        assert(settling.peak < 230);
        std::printf("PASS: illustrative %s plant: mean %.2fF -> %.2fF, new peak %.2fF\n",
                    hotRestart ? "hot-restart" : "cold-start", legacy.mean, settling.mean, settling.peak);
    }
}

int main() {
    persistentShortfall();
    warmupAndHysteresis();
    resetsAndOvershoot();
    closedLoopFixtures();
}
