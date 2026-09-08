#pragma once

#include "fan_controller.h"
#include "servo_controller.h"
#include "split_range.h"

// Apply one control command, including the pit-probe fault interlock.
inline void applyControlOutputs(FanController& fan, ServoController& damper,
                                bool controlReady, float pidOutput,
                                const char* fanMode, float fanOnThreshold) {
    if (!controlReady) {
        // off() cancels kick-start and manual duty immediately.
        // splitRange(0, "fan_only", ...) would leave the damper fully open.
        fan.off();
        damper.setPosition(0.0f);
        return;
    }
    const SplitRangeOutput output = splitRange(pidOutput, fanMode, fanOnThreshold);
    damper.setPosition(output.damperPercent);
    fan.setSpeed(output.fanPercent);
}
