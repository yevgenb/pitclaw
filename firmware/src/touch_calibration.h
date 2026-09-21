#pragma once

#include <cmath>
#include <stdint.h>

// Correction of display-oriented coordinates, after the panel driver's rotation.
// Device-specific values live in config.json; other boards keep their native map.
struct TouchCalibration {
    bool enabled = false;
    float yScale = 1.0f;
    float yOffset = 0.0f;

    bool valid() const {
        return std::isfinite(yScale) && std::isfinite(yOffset) &&
               yScale >= 0.5f && yScale <= 1.5f && std::fabs(yOffset) <= 80.0f;
    }
    bool hasCorrection() const { return valid() && (yScale != 1.0f || yOffset != 0.0f); }
    int32_t mapY(int32_t reported, int32_t height) const {
        if (!enabled || !valid() || height <= 0) return reported;
        // Correct before bounding: a stretched sensor can report > screen height.
        const float y = reported * yScale + yOffset;
        if (y <= 0) return 0;
        if (y >= height - 1) return height - 1;
        return static_cast<int32_t>(std::lround(y));
    }
};
