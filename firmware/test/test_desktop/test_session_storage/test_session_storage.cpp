#include <unity.h>
#include "Arduino.h"
#include <memory>
#include <vector>
#include <map>
#include <cstring>
#include <algorithm>
#include "cook_session.h"
#include "storage_files.h"

// Exercise the production LittleFS branch with append-create semantics.
struct File {
    std::shared_ptr<std::vector<uint8_t>> bytes;
    size_t cursor = 0;
    explicit operator bool() const { return bool(bytes); }
    size_t size() const { return bytes->size(); }
    size_t write(const uint8_t* data, size_t count) {
        if (cursor + count > bytes->size()) bytes->resize(cursor + count);
        std::memcpy(bytes->data() + cursor, data, count); cursor += count; return count;
    }
    size_t read(uint8_t* data, size_t count) {
        count = std::min(count, bytes->size() - cursor);
        std::memcpy(data, bytes->data() + cursor, count); cursor += count; return count;
    }
    bool seek(size_t offset) { cursor = offset; return offset <= bytes->size(); }
    void close() {}
};
struct FakeFS {
    std::map<std::string, std::shared_ptr<std::vector<uint8_t>>> files;
    File open(const char* path, const char* mode) {
        if (*mode == 'r' && !files.count(path)) return {};
        if (*mode == 'w' || !files.count(path)) files[path] = std::make_shared<std::vector<uint8_t>>();
        File file; file.bytes = files[path]; file.cursor = *mode == 'a' ? file.size() : 0; return file;
    }
    void remove(const char* path) { files.erase(path); }
} LittleFS;
bool storageFileExists(const char* path) { return LittleFS.files.count(path); }
#undef NATIVE_BUILD
#include "cook_session.cpp"

void setUp() { LittleFS.files.clear(); }
void tearDown() {}
static DataPoint point(unsigned i) {
    DataPoint p{}; p.timestamp = 1790293080 + i * 5;
    p.pitTemp = 2250; p.meat1Temp = 0; p.meat2Temp = 1600;
    p.fanPct = 50; p.damperPct = 20; p.flags = DP_FLAG_MEAT1_DISC; return p;
}
static void verify(const CookSession& session, unsigned index, unsigned original) {
    const auto* p = session.getPoint(index); TEST_ASSERT_NOT_NULL(p);
    TEST_ASSERT_EQUAL_UINT32(point(original).timestamp, p->timestamp);
    TEST_ASSERT_EQUAL_INT16(2250, p->pitTemp);
    TEST_ASSERT_EQUAL_INT16(0, p->meat1Temp);
    TEST_ASSERT_EQUAL_INT16(1600, p->meat2Temp);
    TEST_ASSERT_EQUAL_UINT8(DP_FLAG_MEAT1_DISC, p->flags);
}
void test_new_file_header_round_trip_and_append() {
    CookSession session; session.startSession(); session.addPoint(point(0)); session.flush();
    TEST_ASSERT_EQUAL(sizeof(uint32_t) + sizeof(DataPoint), LittleFS.open(SESSION_FILE_PATH, "r").size());
    session.addPoint(point(1)); session.flush();
    CookSession recovered; TEST_ASSERT_TRUE(recovered.loadFromFlash());
    TEST_ASSERT_EQUAL_UINT32(2, recovered.getPointCount()); verify(recovered, 0, 0); verify(recovered, 1, 1);
}
void test_headerless_legacy_file_recovers_without_shifting_fields() {
    File file = LittleFS.open(SESSION_FILE_PATH, "a");
    for (unsigned i=0; i<2; ++i) { auto p=point(i); file.write((const uint8_t*)&p, sizeof(p)); }
    CookSession recovered; TEST_ASSERT_TRUE(recovered.loadFromFlash());
    verify(recovered, 0, 0); verify(recovered, 1, 1);
    recovered.addPoint(point(2)); recovered.flush();
    CookSession again; TEST_ASSERT_TRUE(again.loadFromFlash());
    TEST_ASSERT_EQUAL_UINT32(3, again.getPointCount()); verify(again, 2, 2);
}
void test_large_history_retains_correct_boundaries() {
    for (bool header : {false, true}) {
        LittleFS.files.clear(); File file = LittleFS.open(SESSION_FILE_PATH, "a");
        uint32_t start = point(0).timestamp;
        if (header) file.write((const uint8_t*)&start, sizeof(start));
        for (unsigned i=0; i<SESSION_BUFFER_SIZE+8; ++i) { auto p=point(i); file.write((const uint8_t*)&p, sizeof(p)); }
        CookSession recovered; TEST_ASSERT_TRUE(recovered.loadFromFlash());
        TEST_ASSERT_EQUAL_UINT32(SESSION_BUFFER_SIZE, recovered.getPointCount());
        TEST_ASSERT_EQUAL_UINT32(start, recovered.getStartTime());
        verify(recovered, 0, 8); verify(recovered, SESSION_BUFFER_SIZE-1, SESSION_BUFFER_SIZE+7);
    }
}
void test_overflow_flush_and_recovery_preserve_chronological_order() {
    for (unsigned initialCount : {SESSION_BUFFER_SIZE, 2*SESSION_BUFFER_SIZE+8}) {
        CookSession session; session.startSession();
        for (unsigned i=0; i<initialCount; ++i) session.addPoint(point(i));
        session.flush();
        TEST_ASSERT_EQUAL(sizeof(uint32_t) + SESSION_BUFFER_SIZE * sizeof(DataPoint),
                          LittleFS.open(SESSION_FILE_PATH, "r").size());
        CookSession recovered; TEST_ASSERT_TRUE(recovered.loadFromFlash());
        const unsigned first = initialCount - SESSION_BUFFER_SIZE;
        for (unsigned i=0; i<SESSION_BUFFER_SIZE; ++i) {
            verify(session, i, i+first); verify(recovered, i, i+first);
        }
        recovered.addPoint(point(initialCount)); recovered.flush(); recovered.flush();
        TEST_ASSERT_EQUAL(sizeof(uint32_t) + (SESSION_BUFFER_SIZE+1) * sizeof(DataPoint),
                          LittleFS.open(SESSION_FILE_PATH, "r").size());
        CookSession again; TEST_ASSERT_TRUE(again.loadFromFlash());
        TEST_ASSERT_EQUAL_UINT32(SESSION_BUFFER_SIZE, again.getPointCount());
        for (unsigned i=0; i<SESSION_BUFFER_SIZE; ++i) {
            verify(recovered, i, i+first+1); verify(again, i, i+first+1);
        }
    }
}
void test_graph_elapsed_across_time_sync_and_reboot() {
    TEST_ASSERT_EQUAL_UINT32(5, sessionPointElapsed(120, 1790293080));
    TEST_ASSERT_EQUAL_UINT32(5, sessionPointElapsed(1790293080, 120));
    TEST_ASSERT_EQUAL_UINT32(5, sessionPointElapsed(120, 10));
    TEST_ASSERT_EQUAL_UINT32(60, sessionPointElapsed(1790293080, 1790293140));
}
int main() {
    UNITY_BEGIN();
    RUN_TEST(test_new_file_header_round_trip_and_append);
    RUN_TEST(test_headerless_legacy_file_recovers_without_shifting_fields);
    RUN_TEST(test_large_history_retains_correct_boundaries);
    RUN_TEST(test_overflow_flush_and_recovery_preserve_chronological_order);
    RUN_TEST(test_graph_elapsed_across_time_sync_and_reboot);
    return UNITY_END();
}
