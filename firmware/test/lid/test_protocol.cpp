#include <ArduinoJson.h>
#include <cassert>
#include <cstring>
#include <cstdio>
#include "web_protocol.h"
// Access only the real JSON codec for round-trip tests; no simulated copy of its logic.
#define private public
#include "config_manager.h"
#undef private
#include "config_manager.cpp"
static bbq_protocol::ParsedCommand parse(const char* s) { return bbq_protocol::parseCommand(s,strlen(s)); }
int main() {
    using bbq_protocol::CmdType;
    auto off=parse(R"({"type":"config","lidEnabled":false})");
    assert(off.type==CmdType::SET_LID_ENABLED && !off.lidEnabled);
    auto on=parse(R"({"type":"config","lidEnabled":true})");
    assert(on.type==CmdType::SET_LID_ENABLED && on.lidEnabled);
    assert(parse(R"({"type":"lid","action":"resume"})").type==CmdType::RESUME_LID);
    assert(parse(R"({"type":"lid","action":"open"})").type==CmdType::OPEN_LID);
    for (const char* bad : {R"({"type":"config","lidEnabled":"false"})",R"({"type":"config","lidEnabled":0})",R"({"type":"config","lidEnabled":false,"fanMode":"fan_only"})",R"({"type":"lid","action":"disable"})"})
        assert(parse(bad).type==CmdType::UNKNOWN);
    ConfigManager cfg;
    assert(cfg.isLidDetectionEnabled());
    JsonDocument old; old["fan"]["mode"]="fan_only"; cfg.fromJson(old);
    assert(cfg.isLidDetectionEnabled() && strcmp(cfg.getFanMode(),"fan_only")==0);
    cfg.setLidDetectionEnabled(false); JsonDocument persisted; cfg.toJson(persisted);
    char stored[2048]; serializeJson(persisted,stored,sizeof(stored));
    JsonDocument loaded; assert(!deserializeJson(loaded,stored));
    ConfigManager rebooted; rebooted.fromJson(loaded);
    assert(!rebooted.isLidDetectionEnabled() && strcmp(rebooted.getFanMode(),"fan_only")==0);
    rebooted.resetDefaults(); assert(rebooted.isLidDetectionEnabled());
    // Old configs retain the panel map. Calibration is enabled only by Save.
    assert(!rebooted.getConfig().touch.enabled && rebooted.getConfig().touch.mapY(257,320) == 257);
    JsonDocument calibrated;
    calibrated["touch"]["enabled"] = true;
    calibrated["touch"]["yScale"] = .85704777f;
    calibrated["touch"]["yOffset"] = 15.216774f;
    cfg.fromJson(calibrated); cfg.toJson(persisted); rebooted.fromJson(persisted);
    const auto& touch = rebooted.getConfig().touch;
    assert(touch.enabled && touch.mapY(257,320) == 235 && touch.mapY(259,320) == 237);
    assert(touch.mapY(324,320) == 293); // No premature clipping to screen height.
    assert(touch.mapY(-100,320) == 0 && touch.mapY(1000,320) == 319);
    for (const char* invalid : {R"({"touch":{"enabled":true,"yScale":0,"yOffset":0}})",
                               R"({"touch":{"enabled":true,"yScale":1,"yOffset":1000}})",
                               R"({"touch":{"enabled":true,"yScale":".85","yOffset":15}})",
                               R"({"touch":{"enabled":true,"yScale":0.85}})"}) {
        JsonDocument bad; assert(!deserializeJson(bad,invalid)); cfg.fromJson(bad);
        assert(!cfg.getConfig().touch.enabled && cfg.getConfig().touch.mapY(257,320) == 257);
    }
    calibrated["touch"]["enabled"] = false; cfg.fromJson(calibrated); cfg.toJson(persisted);
    rebooted.fromJson(persisted);
    assert(!rebooted.getConfig().touch.enabled && rebooted.getConfig().touch.hasCorrection());
    bbq_protocol::DataPayload d{}; d.lidEnabled=false; d.lid=false; d.lidRemaining=0;
    d.errorCount=8; for(auto& e:d.errors) { memset(e,'E',47); e[47]=0; }
    char packet[1024]; auto len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    JsonDocument result; assert(!deserializeJson(result,packet,len));
    assert(result["lidEnabled"].is<bool>() && !result["lidEnabled"].as<bool>());
    assert(result["errors"].size()==8);
    d.lidEnabled=false; d.lid=true; d.lidRemaining=83; d.lidManual=true;
    len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    assert(!deserializeJson(result,packet,len) && result["lid"].as<bool>() && result["lidRemaining"]==83);
    assert(result["lidManual"].as<bool>() && !result["lidEnabled"].as<bool>());
    d.errorCount=0; d.meat1=NAN; d.meat2=-1;
    len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    assert(!deserializeJson(result,packet,len));
    assert(result["meat1"].isNull() && result["meat2"]==-1 && result["errors"].size()==0);
    std::puts("PASS: lid commands, invalid command rejection, old-config migration, disabled-setting persistence and complete broadcasts");
}
