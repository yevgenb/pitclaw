#pragma once

#include <stdint.h>

#define GRAPH_HISTORY_SIZE 240

// A single condensable graph data slot
struct GraphSlot {
    float pit;
    float meat1;
    float meat2;
    float setpoint;
    bool pitValid;
    bool meat1Valid;
    bool meat2Valid;
    uint32_t elapsedSec;
};

// Adaptive-condensing graph history buffer.
// Stores up to 240 slots. When full, merges all 240 into 120 by pairwise
// averaging, then continues appending from slot 120. Oldest points gradually
// represent wider time spans while recent data stays detailed. Slot timestamps
// preserve the spacing of those samples on the graph.
//
// Pure C++ — no LVGL or Arduino dependencies. Fully testable on native.
class GraphHistory {
public:
    GraphHistory();

    // Append a data point. Disconnected probes are marked invalid.
    // When the buffer is full, condenses 240 -> 120 before appending.
    void addPoint(float pit, float meat1, float meat2, float setpoint,
                  bool pitDisc, bool meat1Disc, bool meat2Disc,
                  uint32_t elapsedSec = UINT32_MAX);

    // Clear all stored data
    void clear();

    // Number of valid slots currently stored
    uint16_t getCount() const { return _count; }
    uint32_t getStartSec() const { return _startSec; }
    uint32_t getEndSec() const { return _endSec; }

    // Access a slot by index (0 = oldest)
    const GraphSlot& getSlot(uint16_t index) const;

private:
    GraphSlot _buffer[GRAPH_HISTORY_SIZE];
    uint16_t _count;
    uint32_t _startSec = 0;
    uint32_t _endSec = 0;

    // Merge the full buffer into half by pairwise averaging
    void condense();

    // Average two values respecting validity flags
    static float mergeValues(float a, bool aValid, float b, bool bValid, bool& outValid);
};
