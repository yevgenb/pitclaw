// Runs the production simulator HTTP/WS adapter without SDL or hardware.
#include "simulator/sim_web_server.h"
#include "simulator/mongoose.h"
#include <cstdlib>
#include <cstdio>
#include <thread>
#include <chrono>
static float setpoint = 225;
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    mg_log_set(0);
    SimWebServer server;
    server.onSetpoint([](float value) { setpoint = value; });
    server.begin(atoi(argv[1]), argv[2]);
    puts("READY"); fflush(stdout);
    for (;;) {
        server.tick();
        bbq_protocol::DataPayload data = {};
        data.sp = setpoint; data.pit = 225; data.fanMode = "fan_and_damper";
        server.broadcastData(data);
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
}
