#pragma once
#include <cmath>

// Broad sanity limits, including the full ADC conversion range. These reject
// corrupt/transient values; they are not the probe's rated operating limits.
inline bool isPlausibleTempC(float value) {
    return std::isfinite(value) && value >= -50.0f && value <= 400.0f;
}
inline bool isPlausibleTempF(float value) {
    return std::isfinite(value) && value >= -58.0f && value <= 752.0f;
}
