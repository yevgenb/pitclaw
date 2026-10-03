#include <unity.h>
#include <cmath>
#include "display/graph_history.cpp"
void setUp() {}
void tearDown() {}
void test_disconnected_and_implausible_readings_stay_out_of_graph() {
    GraphHistory graph;
    graph.addPoint(225, 5000, NAN, 225, false, false, false, 0);
    TEST_ASSERT_TRUE(graph.getSlot(0).pitValid);
    TEST_ASSERT_FALSE(graph.getSlot(0).meat1Valid);
    TEST_ASSERT_FALSE(graph.getSlot(0).meat2Valid);
    graph.addPoint(225, 100, 100, 225, false, true, true, 5);
    TEST_ASSERT_FALSE(graph.getSlot(1).meat1Valid);
    for (unsigned i = 2; i <= GRAPH_HISTORY_SIZE; ++i)
        graph.addPoint(225, 150, 160, 225, false, false, false, i * 5);
    TEST_ASSERT_FALSE(graph.getSlot(0).meat1Valid); // Condensing cannot revive invalid values.
    TEST_ASSERT_EQUAL_FLOAT(150, graph.getSlot(graph.getCount()-1).meat1);
}
int main() {
    UNITY_BEGIN(); RUN_TEST(test_disconnected_and_implausible_readings_stay_out_of_graph); return UNITY_END();
}
