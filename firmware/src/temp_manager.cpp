#include "temp_manager.h"

#ifndef NATIVE_BUILD
#include <Arduino.h>
#endif

// ADC channel mapping: probe index -> ADS1115 channel
const uint8_t TempManager::_adcChannels[NUM_PROBES] = {
    ADC_CHANNEL_PIT,
    ADC_CHANNEL_MEAT1,
    ADC_CHANNEL_MEAT2
};

TempManager::TempManager()
    : _emaAlpha(TEMP_EMA_ALPHA)
    , _useFahrenheit(true)
    , _lastSampleMs(0)
{
    for (uint8_t i = 0; i < NUM_PROBES; i++) {
        _rawADC[i] = 0;
        _filteredTempC[i] = 0.0f;
        _status[i] = ProbeStatus::OPEN_CIRCUIT;
        _firstReading[i] = true;
        // ProbeConfig default-initialized with THERM_A/B/C and offset 0
    }
}

bool TempManager::begin() {
#ifndef NATIVE_BUILD
    Wire.begin(PIN_SDA, PIN_SCL);

    _adcReady = _ads.begin(ADS1115_ADDR, &Wire);
    if (!_adcReady) {
        Serial.println("[TEMP] ADS1115 not found at 0x48!");
        return false;
    }

    // Set gain to GAIN_ONE (+/- 4.096V range)
    _ads.setGain(GAIN_ONE);

    Serial.println("[TEMP] ADS1115 initialized OK.");
#endif
    _lastSampleMs = 0;
    return true;
}

void TempManager::update() {
#ifndef NATIVE_BUILD
    if (!_adcReady) return;  // Display-only bring-up: leave all probes unavailable.
    unsigned long now = millis();
    if (now - _lastSampleMs < TEMP_SAMPLE_INTERVAL_MS) {
        return;  // Not time to sample yet
    }
    _lastSampleMs = now;

    const int16_t rawSupply = _ads.readADC_SingleEnded(ADC_CHANNEL_SUPPLY);
    for (uint8_t i = 0; i < NUM_PROBES; i++) {
        // Read raw ADC value from ADS1115 single-ended
        int16_t raw = _ads.readADC_SingleEnded(_adcChannels[i]);
        processSample(i, raw, rawSupply);
    }
#endif
}

void TempManager::processSample(uint8_t probe, int16_t raw, int16_t rawSupply) {
    if (probe >= NUM_PROBES) return;
    _rawADC[probe] = raw;

    // Without a plausible excitation measurement no probe temperature is valid.
    if (rawSupply < ADC_SUPPLY_MIN_RAW || rawSupply > ADC_SUPPLY_MAX_RAW ||
        raw >= ERROR_PROBE_OPEN_RATIO * rawSupply) {
        _status[probe] = ProbeStatus::OPEN_CIRCUIT;
        _firstReading[probe] = true;
        return;
    }
    if (raw <= ERROR_PROBE_SHORT_THRESHOLD) {
        _status[probe] = ProbeStatus::SHORT_CIRCUIT;
        _firstReading[probe] = true;
        return;
    }

    const float resistance = adcToResistance(raw, rawSupply);
    const float tempC = resistanceToTempC(resistance, _probeConfig[probe]) +
                        _probeConfig[probe].offset;

    if (_firstReading[probe]) {
        _filteredTempC[probe] = tempC;
        _firstReading[probe] = false;
    } else {
        _filteredTempC[probe] = _emaAlpha * tempC +
                              (1.0f - _emaAlpha) * _filteredTempC[probe];
    }
    _status[probe] = ProbeStatus::OK;
}

float TempManager::getTemp(uint8_t probe) const {
    if (probe >= NUM_PROBES) return 0.0f;
    if (_status[probe] != ProbeStatus::OK) return 0.0f;

    if (_useFahrenheit) {
        return cToF(_filteredTempC[probe]);
    }
    return _filteredTempC[probe];
}

float TempManager::getTempC(uint8_t probe) const {
    if (probe >= NUM_PROBES) return 0.0f;
    if (_status[probe] != ProbeStatus::OK) return 0.0f;
    return _filteredTempC[probe];
}

bool TempManager::isConnected(uint8_t probe) const {
    if (probe >= NUM_PROBES) return false;
    return _status[probe] == ProbeStatus::OK;
}

ProbeStatus TempManager::getStatus(uint8_t probe) const {
    if (probe >= NUM_PROBES) return ProbeStatus::OPEN_CIRCUIT;
    return _status[probe];
}

int16_t TempManager::getRawADC(uint8_t probe) const {
    if (probe >= NUM_PROBES) return 0;
    return _rawADC[probe];
}

void TempManager::setEMAAlpha(float alpha) {
    if (alpha > 0.0f && alpha <= 1.0f) {
        _emaAlpha = alpha;
    }
}

void TempManager::setOffset(uint8_t probe, float offset) {
    if (probe < NUM_PROBES) {
        _probeConfig[probe].offset = offset;
    }
}

void TempManager::setCoefficients(uint8_t probe, float a, float b, float c) {
    if (probe < NUM_PROBES) {
        _probeConfig[probe].a = a;
        _probeConfig[probe].b = b;
        _probeConfig[probe].c = c;
    }
}

void TempManager::setUseFahrenheit(bool useF) {
    _useFahrenheit = useF;
}

float TempManager::adcToResistance(int16_t raw, int16_t rawSupply) const {
    // Carrier: +3V3_A -> 10k pull-up -> ADC/probe node -> NTC -> GND.
    // AIN3 measures the same excitation, independent of the ADC full-scale range.
    if (raw <= 0 || raw >= rawSupply) return 0.0f;
    return REFERENCE_RESISTANCE * (float)raw / (float)(rawSupply - raw);
}

float TempManager::resistanceToTempC(float resistance, const ProbeConfig& cfg) const {
    // Steinhart-Hart equation:
    // 1/T = A + B * ln(R) + C * (ln(R))^3
    // T is in Kelvin
    float lnR = logf(resistance);
    float lnR3 = lnR * lnR * lnR;
    float invT = cfg.a + cfg.b * lnR + cfg.c * lnR3;

    if (invT == 0.0f) return 0.0f;

    float tempK = 1.0f / invT;
    float tempC = tempK - 273.15f;
    return tempC;
}
