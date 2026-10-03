#include <ArduinoJson.h>
#include <cassert>
#include <cstring>
#include <cstdio>
#include "web_protocol.h"
#include "alarm_manager.h"
// Access only the real JSON codec for round-trip tests; no simulated copy of its logic.
#define private public
#include "config_manager.h"
#undef private
#include "config_manager.cpp"
static bbq_protocol::ParsedCommand parse(const char* s) { return bbq_protocol::parseCommand(s,strlen(s)); }
int main() {
    using bbq_protocol::CmdType;
    // Partial alarm commands leave omitted fields untouched. An explicit null
    // clears only its named target; ArduinoJson also reports missing keys as null.
    struct AlarmCase {
        const char* json;
        bool meat1, meat2, pitBand;
        float value1, value2, band;
    };
    const AlarmCase alarmCases[] = {
        {R"({"type":"alarm","meat1Target":185})", true, false, false, 185, 0, 0},
        {R"({"type":"alarm","meat2Target":175})", false, true, false, 0, 175, 0},
        {R"({"type":"alarm","pitBand":20})", false, false, true, 0, 0, 20},
        {R"({"type":"alarm"})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":null})", true, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat2Target":null})", false, true, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":185,"meat2Target":175})", true, true, false, 185, 175, 0},
        {R"({"type":"alarm","meat1Target":null,"meat2Target":175})", true, true, false, 0, 175, 0},
        {R"({"type":"alarm","meat1Target":185,"meat2Target":null})", true, true, false, 185, 0, 0},
        {R"({"type":"alarm","meat1Target":null,"meat2Target":null})", true, true, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":185.5})", true, false, false, 185.5f, 0, 0},
        {R"({"type":"alarm","meat2Target":175.25})", false, true, false, 0, 175.25f, 0},
        {R"({"type":"alarm","meat1Target":185.5,"meat2Target":175.25,"pitBand":20.5})", true, true, true, 185.5f, 175.25f, 20.5f},
        {R"({"type":"alarm","meat1Target":0})", true, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":true})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":"185"})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":[]})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat1Target":{}})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat2Target":false})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat2Target":"175"})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat2Target":[]})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","meat2Target":{}})", false, false, false, 0, 0, 0},
        {R"({"type":"alarm","pitBand":null})", false, false, false, 0, 0, 0},
    };
    const auto applyAlarm = [](AlarmManager& alarms, const bbq_protocol::ParsedCommand& cmd) {
        if (cmd.hasMeat1Target) alarms.setMeat1Target(cmd.meat1Target);
        if (cmd.hasMeat2Target) alarms.setMeat2Target(cmd.meat2Target);
        if (cmd.hasPitBand) alarms.setPitBand(cmd.pitBand);
    };
    for (const auto& expected : alarmCases) {
        const auto cmd = parse(expected.json);
        assert(cmd.type == CmdType::ALARM);
        assert(cmd.hasMeat1Target == expected.meat1 && cmd.hasMeat2Target == expected.meat2);
        assert(cmd.hasPitBand == expected.pitBand);
        if (expected.meat1) assert(cmd.meat1Target == expected.value1);
        if (expected.meat2) assert(cmd.meat2Target == expected.value2);
        if (expected.pitBand) assert(cmd.pitBand == expected.band);

        AlarmManager alarms;
        alarms.setMeat1Target(180); alarms.setMeat2Target(170);
        const auto previousBand = alarms.getPitBand();
        applyAlarm(alarms, cmd);
        assert(alarms.getMeat1Target() == (expected.meat1 ? expected.value1 : 180));
        assert(alarms.getMeat2Target() == (expected.meat2 ? expected.value2 : 170));
        assert(alarms.getPitBand() == (expected.pitBand ? expected.band : previousBand));
    }
    AlarmManager partialAlarms;
    partialAlarms.setMeat1Target(180); partialAlarms.setMeat2Target(170);
    applyAlarm(partialAlarms, parse(R"({"type":"alarm","meat1Target":185})"));
    applyAlarm(partialAlarms, parse(R"({"type":"alarm","meat2Target":175})"));
    assert(partialAlarms.getMeat1Target() == 185 && partialAlarms.getMeat2Target() == 175);
    applyAlarm(partialAlarms, parse(R"({"type":"alarm","meat1Target":null})"));
    assert(partialAlarms.getMeat1Target() == 0 && partialAlarms.getMeat2Target() == 175);
    std::puts("PASS: partial alarm commands preserve untouched targets; explicit null clears only its named target");
    auto off=parse(R"({"type":"config","lidEnabled":false})");
    assert(off.type==CmdType::SET_LID_ENABLED && !off.lidEnabled);
    auto on=parse(R"({"type":"config","lidEnabled":true})");
    assert(on.type==CmdType::SET_LID_ENABLED && on.lidEnabled);
    for (auto seconds : {30,120,300,600}) {
        char request[80]; snprintf(request,sizeof(request),"{\"type\":\"config\",\"lidTimeoutSeconds\":%d}",seconds);
        const auto command=parse(request); assert(command.type==CmdType::SET_LID_TIMEOUT && command.lidTimeoutSeconds==seconds);
    }
    for (const char* bad : {R"({"type":"config","lidTimeoutSeconds":0})",R"({"type":"config","lidTimeoutSeconds":-30})",
                           R"({"type":"config","lidTimeoutSeconds":31})",R"({"type":"config","lidTimeoutSeconds":630})",
                           R"({"type":"config","lidTimeoutSeconds":90.5})",R"({"type":"config","lidTimeoutSeconds":"120"})",
                           R"({"type":"config","lidTimeoutSeconds":120,"lidEnabled":true})",R"({"type":"config","lidTimeoutSeconds":120,"fanMode":"fan_only"})"})
        assert(parse(bad).type==CmdType::UNKNOWN);
    assert(parse(R"({"type":"lid","action":"resume"})").type==CmdType::RESUME_LID);
    assert(parse(R"({"type":"lid","action":"open"})").type==CmdType::OPEN_LID);
    for (const char* bad : {R"({"type":"config","lidEnabled":"false"})",R"({"type":"config","lidEnabled":0})",R"({"type":"config","lidEnabled":false,"fanMode":"fan_only"})",R"({"type":"lid","action":"disable"})"})
        assert(parse(bad).type==CmdType::UNKNOWN);
    ConfigManager cfg;
    assert(cfg.isLidDetectionEnabled());
    JsonDocument old; old["fan"]["mode"]="fan_only"; cfg.fromJson(old);
    assert(cfg.isLidDetectionEnabled() && strcmp(cfg.getFanMode(),"fan_only")==0);
    assert(cfg.getLidTimeoutSeconds()==120);
    assert(cfg.setLidTimeoutSeconds(300) && !cfg.setLidTimeoutSeconds(0));
    cfg.setLidDetectionEnabled(false); JsonDocument persisted; cfg.toJson(persisted);
    char stored[2048]; serializeJson(persisted,stored,sizeof(stored));
    JsonDocument loaded; assert(!deserializeJson(loaded,stored));
    ConfigManager rebooted; rebooted.fromJson(loaded);
    assert(!rebooted.isLidDetectionEnabled() && strcmp(rebooted.getFanMode(),"fan_only")==0);
    assert(rebooted.getLidTimeoutSeconds()==300);
    JsonDocument badTimeout; badTimeout["lid"]["timeoutSeconds"]=65535;
    ConfigManager invalidTimeout; invalidTimeout.fromJson(badTimeout); assert(invalidTimeout.getLidTimeoutSeconds()==120);
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
    assert(rebooted.getConfig().damper.closedUs == 544 && rebooted.getConfig().damper.openUs == 1472);
    JsonDocument endpoints; endpoints["damper"]["closedUs"] = 1600; endpoints["damper"]["openUs"] = 900;
    cfg.fromJson(endpoints); cfg.toJson(persisted); rebooted.fromJson(persisted);
    assert(rebooted.getConfig().damper.closedUs == 1600 && rebooted.getConfig().damper.openUs == 900);
    for (const char* invalid : {R"({"damper":{"closedUs":100,"openUs":900}})",
                               R"({"damper":{"closedUs":900,"openUs":900}})",
                               R"({"damper":{"closedUs":-1,"openUs":1600}})",
                               R"({"damper":{"closedUs":1500,"openUs":2401}})",
                               R"({"damper":{"closedUs":1500}})"}) {
        JsonDocument bad; assert(!deserializeJson(bad,invalid)); cfg.fromJson(bad);
        assert(cfg.getConfig().damper.closedUs == 544 && cfg.getConfig().damper.openUs == 1472);
    }
    bbq_protocol::DataPayload d{}; d.lidEnabled=false; d.lid=false; d.lidRemaining=0;
    d.errorCount=8; for(auto& e:d.errors) { memset(e,'E',47); e[47]=0; }
    char packet[1024]; auto len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    JsonDocument result; assert(!deserializeJson(result,packet,len));
    assert(result["lidEnabled"].is<bool>() && !result["lidEnabled"].as<bool>());
    assert(result["lidTimeoutSeconds"]==120);
    assert(result["errors"].size()==8);
    d.lidEnabled=false; d.lid=true; d.lidRemaining=83; d.lidManual=true;
    d.lidTimeoutSeconds=300;
    len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    assert(!deserializeJson(result,packet,len) && result["lid"].as<bool>() && result["lidRemaining"]==83);
    assert(result["lidManual"].as<bool>() && !result["lidEnabled"].as<bool>());
    assert(result["lidTimeoutSeconds"]==300);
    d.errorCount=0; d.meat1=NAN; d.meat2=-1;
    len=bbq_protocol::buildDataMessage(packet,sizeof(packet),d);
    assert(!deserializeJson(result,packet,len));
    assert(result["meat1"].isNull() && result["meat2"]==-1 && result["errors"].size()==0);
    std::puts("PASS: lid commands, invalid command rejection, old-config migration, disabled-setting persistence and complete broadcasts");
}
