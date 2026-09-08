#pragma once
struct FakeMDNS {
    void end() {}
    bool begin(const char*) { return true; }
    void addService(const char*, const char*, int) {}
};
static FakeMDNS MDNS;
