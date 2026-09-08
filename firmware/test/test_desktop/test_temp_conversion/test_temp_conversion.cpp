/** Production TempManager tests using known resistor-fixture ADC counts. */
#include <unity.h>
#include "temp_manager.h"
#include "temp_manager.cpp"

static TempManager manager;

void setUp(void) { manager = TempManager(); }
void tearDown(void) {}

void test_known_resistor_fixture_temperatures(void) {
    manager.setEMAAlpha(1.0f);
    // At 3.3 V / 26400 counts: 33k, 10k, 5k, and 3k to ground.
    const int16_t raw[] = {20260, 13200, 8800, 6092};
    const float expectedF[] = {124.0f, 184.0f, 220.0f, 257.0f};
    float previous = 0.0f;
    for (uint8_t i = 0; i < 4; ++i) {
        manager.processSample(PROBE_PIT, raw[i], 26400);
        TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
        const float temperature = manager.getPitTemp();
        TEST_ASSERT_FLOAT_WITHIN(5.0f, expectedF[i], temperature);
        TEST_ASSERT_GREATER_THAN_FLOAT(previous, temperature);
        previous = temperature;
    }
}

void test_supply_variation_preserves_temperature(void) {
    manager.setEMAAlpha(1.0f);
    manager.processSample(PROBE_PIT, 13200, 26400); // 10k at 3.3 V
    const float nominal = manager.getPitTemp();
    manager.processSample(PROBE_PIT, 12000, 24000); // Same 10k at 3.0 V
    TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, nominal, manager.getPitTemp());
    manager.processSample(PROBE_PIT, 14400, 28800); // Same 10k at 3.6 V
    TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, nominal, manager.getPitTemp());
}

void test_open_threshold_tracks_excitation(void) {
    manager.processSample(PROBE_PIT, 25871, 26400); // Just below 98%
    TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
    manager.processSample(PROBE_PIT, 25872, 26400); // Exactly 98%
    TEST_ASSERT_EQUAL(ProbeStatus::OPEN_CIRCUIT, manager.getStatus(PROBE_PIT));
    TEST_ASSERT_FALSE(manager.isConnected(PROBE_PIT));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, manager.getPitTemp());
    manager.processSample(PROBE_PIT, 23520, 24000); // 98% of 3.0 V
    TEST_ASSERT_EQUAL(ProbeStatus::OPEN_CIRCUIT, manager.getStatus(PROBE_PIT));
    manager.processSample(PROBE_PIT, 26400, 26400); // Physically unplugged
    TEST_ASSERT_EQUAL(ProbeStatus::OPEN_CIRCUIT, manager.getStatus(PROBE_PIT));
    manager.processSample(PROBE_PIT, 32767, 26400); // Beyond excitation
    TEST_ASSERT_EQUAL(ProbeStatus::OPEN_CIRCUIT, manager.getStatus(PROBE_PIT));
}

void test_short_and_negative_readings_are_rejected(void) {
    const int16_t raw[] = {-1, 0, ERROR_PROBE_SHORT_THRESHOLD};
    for (int16_t value : raw) {
        manager.processSample(PROBE_PIT, value, 26400);
        TEST_ASSERT_EQUAL(ProbeStatus::SHORT_CIRCUIT, manager.getStatus(PROBE_PIT));
        TEST_ASSERT_FALSE(manager.isConnected(PROBE_PIT));
        TEST_ASSERT_EQUAL_INT16(value, manager.getRawADC(PROBE_PIT));
    }
    manager.processSample(PROBE_PIT, ERROR_PROBE_SHORT_THRESHOLD + 1, 26400);
    TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
}

void test_invalid_excitation_rejects_readings_and_resets_filter(void) {
    const int16_t invalidSupply[] = {-1, 0, 23999, 28801, 32767};
    for (int16_t supply : invalidSupply) {
        manager.processSample(PROBE_PIT, 20260, 26400); // Previous cold reading
        manager.processSample(PROBE_PIT, 13200, supply);
        TEST_ASSERT_FALSE(manager.isConnected(PROBE_PIT));
        TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, manager.getTempC(PROBE_PIT));
        manager.processSample(PROBE_PIT, 13200, 26400); // Recovered 10k
        TEST_ASSERT_TRUE(manager.isConnected(PROBE_PIT));
        TEST_ASSERT_FLOAT_WITHIN(5.0f, 184.0f, manager.getPitTemp());
    }
}

void test_probe_reconnect_resets_filter(void) {
    const int16_t faults[] = {0, 26400};
    for (int16_t fault : faults) {
        manager.processSample(PROBE_PIT, 20260, 26400);
        manager.processSample(PROBE_PIT, fault, 26400);
        manager.processSample(PROBE_PIT, 6092, 26400);
        TEST_ASSERT_FLOAT_WITHIN(5.0f, 257.0f, manager.getPitTemp());
    }
}

void test_calibration_units_and_channel_filtering(void) {
    manager.setUseFahrenheit(false);
    manager.setOffset(PROBE_MEAT1, 2.0f);
    manager.processSample(PROBE_PIT, 13200, 26400);
    manager.processSample(PROBE_MEAT1, 13200, 26400);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, manager.getTempC(PROBE_PIT) + 2.0f,
                             manager.getMeat1Temp());
    const float initial = manager.getPitTemp();
    TempManager unfiltered;
    unfiltered.processSample(PROBE_PIT, 8800, 26400);
    manager.processSample(PROBE_PIT, 8800, 26400);
    TEST_ASSERT_FLOAT_WITHIN(0.001f,
        initial * (1.0f - TEMP_EMA_ALPHA) + unfiltered.getTempC(PROBE_PIT) * TEMP_EMA_ALPHA,
        manager.getPitTemp());
    TEST_ASSERT_FLOAT_WITHIN(0.001f, initial + 2.0f, manager.getMeat1Temp());
    TEST_ASSERT_FALSE(manager.isConnected(PROBE_MEAT2));
}

void test_celsius_to_fahrenheit(void) {
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 32.0f, TempManager::cToF(0.0f));
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 212.0f, TempManager::cToF(100.0f));
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -40.0f, TempManager::cToF(-40.0f));
}

int main(int argc, char** argv) {
    UNITY_BEGIN();
    RUN_TEST(test_known_resistor_fixture_temperatures);
    RUN_TEST(test_supply_variation_preserves_temperature);
    RUN_TEST(test_open_threshold_tracks_excitation);
    RUN_TEST(test_short_and_negative_readings_are_rejected);
    RUN_TEST(test_invalid_excitation_rejects_readings_and_resets_filter);
    RUN_TEST(test_probe_reconnect_resets_filter);
    RUN_TEST(test_calibration_units_and_channel_filtering);
    RUN_TEST(test_celsius_to_fahrenheit);
    return UNITY_END();
}
