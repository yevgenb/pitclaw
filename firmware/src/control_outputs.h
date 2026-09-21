#pragma once

#include "fan_controller.h"
#include "servo_controller.h"
#include "split_range.h"

// Apply one control command, including the pit-probe fault interlock.
inline void applyControlOutputs(FanController& fan, ServoController& damper,
                                bool controlReady, float pidOutput,
                                const char* fanMode, float fanOnThreshold, bool lidOpen = false,
                                bool damperSetup = false) {
    if (damperSetup) {
        fan.off(); // Manual bench setup owns the servo; PID and probe state cannot sweep it.
        return;
    }
    if (!controlReady) {
        // off() cancels kick-start and manual duty immediately.
        // splitRange(0, "fan_only", ...) would leave the damper fully open.
        fan.off();
        damper.setPosition(0.0f);
        return;
    }
    if (lidOpen) {
        fan.off(); // Cancel a running kick-start too, not just its target duty.
        damper.setPosition(splitRange(0, fanMode, fanOnThreshold).damperPercent);
        return;
    }
    const SplitRangeOutput output = splitRange(pidOutput, fanMode, fanOnThreshold);
    damper.setPosition(output.damperPercent);
    fan.setSpeed(output.fanPercent);
}
