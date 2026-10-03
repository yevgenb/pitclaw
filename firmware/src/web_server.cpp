#include "web_server.h"
#include "web_assets.h"

#ifndef NATIVE_BUILD
#include <Arduino.h>
#include <time.h>
#include <cmath>
#include <esp_timer.h>
#include <new>

#include "temp_manager.h"
#include "pid_controller.h"
#include "fan_controller.h"
#include "servo_controller.h"
#include "config_manager.h"
#include "cook_session.h"
#include "alarm_manager.h"
#include "error_manager.h"

namespace {
uint64_t authNow() { return esp_timer_get_time() / 1000; }
std::string header(AsyncWebServerRequest* request, const char* name) {
    return request->hasHeader(name) ? request->getHeader(name)->value().c_str() : "";
}
void sendAuthReply(AsyncWebServerRequest* request, const WebAuthReply& reply) {
    auto* response = request->beginResponse(reply.status, "application/json", reply.body.c_str());
    response->addHeader("Cache-Control", "no-store");
    if (!reply.cookie.empty()) response->addHeader("Set-Cookie", reply.cookie.c_str());
    if (reply.status == 429) response->addHeader("Retry-After", "60");
    request->send(response);
}
// This handler is selected at the end of HTTP headers, before any upload/body
// callback can run. A response-only middleware is too late for ElegantOTA.
class AuthGate : public AsyncWebHandler {
public:
    explicit AuthGate(WebAuth& auth) : _auth(auth) {}
    int rejection(AsyncWebServerRequest* request) const {
        if (request->url().startsWith("/api/auth") && request->contentLength() > 1024) return 413;
        return _auth.gate(request->methodToString(), request->url().c_str(),
            header(request, "Cookie"), header(request, "Origin"), request->host().c_str(), authNow());
    }
    bool canHandle(AsyncWebServerRequest* request) const override {
        const int status = rejection(request);
        if (status) request->setAttribute("authRejection", long(status));
        return status != 0;
    }
    void handleRequest(AsyncWebServerRequest* request) override {
        auto* response = request->beginResponse(request->getAttribute("authRejection", 401L),
            "application/json", "{\"error\":\"Access denied\"}");
        response->addHeader("Cache-Control", "no-store"); request->send(response);
    }
private:
    WebAuth& _auth;
};
}
#endif

BBQWebServer::BBQWebServer()
    :
#ifndef NATIVE_BUILD
      _server(nullptr)
    , _ws(nullptr)
    ,
#endif
      _temp(nullptr)
    , _pid(nullptr)
    , _fan(nullptr)
    , _servo(nullptr)
    , _config(nullptr)
    , _session(nullptr)
    , _alarm(nullptr)
    , _error(nullptr)
    , _setpoint(225.0f)
    , _estimatedTime(0)
    , _lastBroadcastMs(0)
    , _onSetpoint(nullptr)
    , _onAlarm(nullptr)
    , _onSession(nullptr)
    , _onFanMode(nullptr)
    , _onLidEnabled(nullptr)
    , _onResumeLid(nullptr)
{
}

void BBQWebServer::begin(bool startListening) {
#ifndef NATIVE_BUILD
    _server = new AsyncWebServer(WEB_PORT);
    if (_config) _auth.load(_config->getConfig().webAuth);
    _server->addHandler(new AuthGate(_auth));
    auto authHandler = [this](AsyncWebServerRequest* request) {
        const auto parameter = [request](const char* name) -> std::string {
            if (!request->hasParam(name, true)) return {};
            const auto& value = request->getParam(name, true)->value();
            return std::string(value.c_str(), value.length());
        };
        if (request->url() == "/api/auth/settings" && parameter("enabled") != "true" && parameter("enabled") != "false") {
            request->send(400, "application/json", "{\"error\":\"Specify enabled as true or false\"}"); return;
        }
        const std::string method = request->methodToString(), path = request->url().c_str();
        const auto cookie = header(request, "Cookie"), password = parameter("password");
        const bool enable = parameter("enabled") == "true", secure = header(request, "X-Forwarded-Proto") == "https";
        const auto process = [this, method, path, cookie, password, enable, secure]() {
            return _auth.handle(method, path, cookie, password, enable, authNow(), secure,
                [this](const WebAuthConfig& cfg) { return _config && _config->saveWebAuth(cfg); });
        };
        if (path != "/api/auth/login" && path != "/api/auth/settings") {
            const auto reply = process();
            sendAuthReply(request, reply);
            if (path == "/api/auth/settings" && reply.status == 200 && _ws) _ws->closeAll(1008, "Access settings changed");
            return;
        }
        // PBKDF2 must not occupy AsyncTCP's watched network task. Keep one job
        // in flight, pause safely using the library's weak request continuation,
        // and let the network/control tasks continue while the worker hashes.
        if (_authBusy.exchange(true)) {
            sendAuthReply(request, {429, "{\"error\":\"Authentication is busy. Try again shortly.\"}", {}}); return;
        }
        const auto continuation = request->pause();
        auto* work = new (std::nothrow) std::function<void()>([this, continuation, process, path]() {
            if (!continuation.expired()) {
                const auto reply = process();
                if (auto request = continuation.lock()) sendAuthReply(request.get(), reply);
                if (path == "/api/auth/settings" && reply.status == 200 && _ws) _ws->closeAll(1008, "Access settings changed");
            }
            _authBusy = false;
        });
        if (!work || xTaskCreate([](void* arg) {
            auto* work = static_cast<std::function<void()>*>(arg);
            (*work)(); delete work; vTaskDelete(nullptr);
        }, "web_auth", 6144, work, 1, nullptr) != pdPASS) {
            delete work; _authBusy = false;
            sendAuthReply(request, {503, "{\"error\":\"Authentication unavailable. Try again.\"}", {}});
        }
    };
    _server->on("/api/auth", HTTP_GET, authHandler);
    for (const char* path : {"/api/auth/login", "/api/auth/logout", "/api/auth/settings"})
        _server->on(path, HTTP_POST, authHandler);
    _ws = new AsyncWebSocket(WS_PATH);

    // WebSocket event handler
    _ws->onEvent([this](AsyncWebSocket* server, AsyncWebSocketClient* client,
                        AwsEventType type, void* arg, uint8_t* data, size_t len) {
        this->onWsEvent(server, client, type, arg, data, len);
    });

    _server->addHandler(_ws);

    // Version API endpoint
    _server->on("/api/version", HTTP_GET, [](AsyncWebServerRequest* request) {
        char json[160];
        snprintf(json, sizeof(json),
                 "{\"version\":\"%s\",\"uiBuild\":\"%s\",\"board\":\"wt32_sc01_plus\",\"releaseUpdatesEnabled\":%s}",
                 FIRMWARE_VERSION, WEB_UI_BUILD, ENABLE_RELEASE_UPDATES ? "true" : "false");
        auto* response = request->beginResponse(200, "application/json", json);
        response->addHeader("Cache-Control", "no-store");
        request->send(response);
    });

    // Read-only timer register diagnostics; this does not measure the external signal.
    _server->on("/api/servo", HTTP_GET, [this](AsyncWebServerRequest* request) {
        if (!_servo) { request->send(503, "application/json", "{\"error\":\"Servo unavailable\"}"); return; }
        const uint32_t duty = _servo->getPwmDutyTicks();
        const uint32_t frequency = _servo->getPwmFrequencyHz();
        const double pulse = frequency ? double(duty) * 1000000.0 / (frequency * (1UL << SERVO_PWM_RESOLUTION)) : 0;
        char sampled[192] = "";
        if (request->hasParam("sample") && request->getParam("sample")->value() == "1") {
            const auto sample = _servo->sampleSignal();
            const bool complete = sample.highUs && sample.lowUs;
            const double measuredHz = complete ? 1000000.0 / (sample.highUs + sample.lowUs) : 0;
            snprintf(sampled, sizeof(sampled), ",\"pinSampleComplete\":%s,\"pinHighUs\":%lu,\"pinLowUs\":%lu,\"pinFrequencyHz\":%.2f",
                     complete ? "true" : "false", (unsigned long)sample.highUs, (unsigned long)sample.lowUs, measuredHz);
        }
        char json[448];
        snprintf(json, sizeof(json), "{\"source\":\"PWM registers\",\"gpio\":%u,\"channel\":%u,\"frequencyHz\":%lu,\"dutyTicks\":%lu,\"pulseUs\":%.2f%s}",
                 PIN_SERVO, SERVO_PWM_CHANNEL, (unsigned long)frequency, (unsigned long)duty, pulse, sampled);
        request->send(200, "application/json", json);
    });

    registerWebAssets(*_server);

    // LittleFS holds passwords, notification keys and cook data; it is private.

    // Fallback 404
    _server->onNotFound([](AsyncWebServerRequest* request) {
        request->send(404, "text/plain", "Not Found");
    });

    _lastBroadcastMs = millis();
    setEnabled(startListening);
#endif
}

void BBQWebServer::setEnabled(bool enabled) {
#ifndef NATIVE_BUILD
    if (!_server || enabled == _listening) return;
    if (enabled) {
        _server->begin();
        Serial.printf("[WEB] Server started on port %d, WebSocket at %s\n", WEB_PORT, WS_PATH);
    } else {
        if (_ws) _ws->closeAll();
        _server->end();
        Serial.println("[WEB] Server paused for Wi-Fi setup portal.");
    }
    _listening = enabled;
#endif
}

void BBQWebServer::update() {
#ifndef NATIVE_BUILD
    unsigned long now = millis();

    // Periodic broadcast to all connected clients
    if (now - _lastBroadcastMs >= WS_SEND_INTERVAL) {
        _lastBroadcastMs = now;

        if (_ws && _ws->count() > 0) {
            bbq_protocol::DataPayload payload = buildDataPayload();
            char buf[1024];
            size_t len = bbq_protocol::buildDataMessage(buf, sizeof(buf), payload);
            broadcastAuthenticated(buf, len);
        }
    }

    // Clean up disconnected clients
    if (_ws) {
        _ws->cleanupClients(WS_MAX_CLIENTS);
    }
#endif
}

void BBQWebServer::setModules(TempManager* temp, PidController* pid, FanController* fan,
                            ServoController* servo, ConfigManager* config, CookSession* session,
                            AlarmManager* alarm, ErrorManager* error) {
    _temp   = temp;
    _pid    = pid;
    _fan    = fan;
    _servo  = servo;
    _config = config;
    _session = session;
    _alarm  = alarm;
    _error  = error;
}

void BBQWebServer::broadcastNow() {
#ifndef NATIVE_BUILD
    if (_ws && _ws->count() > 0) {
        bbq_protocol::DataPayload payload = buildDataPayload();
        char buf[1024];
        size_t len = bbq_protocol::buildDataMessage(buf, sizeof(buf), payload);
        broadcastAuthenticated(buf, len);
    }
#endif
}

uint8_t BBQWebServer::getClientCount() const {
#ifndef NATIVE_BUILD
    if (_ws) return _ws->count();
#endif
    return 0;
}

bbq_protocol::DataPayload BBQWebServer::buildDataPayload() {
    bbq_protocol::DataPayload payload;
    memset(&payload, 0, sizeof(payload));

#ifndef NATIVE_BUILD
    // Timestamp
    time_t now;
    time(&now);
    payload.ts = (uint32_t)now;

    // Temperatures
    if (_temp) {
        auto reading = [this](uint8_t probe) -> float {
            if (_temp->getStatus(probe) == ProbeStatus::SHORT_CIRCUIT) return -1.0f;
            return _temp->isConnected(probe) ? _temp->getTemp(probe) : NAN;
        };
        payload.pit = reading(PROBE_PIT);
        payload.meat1 = reading(PROBE_MEAT1);
        payload.meat2 = reading(PROBE_MEAT2);
    } else {
        payload.pit = payload.meat1 = payload.meat2 = NAN;
    }

    // Fan and damper
    payload.fan    = _fan    ? (uint8_t)_fan->getCurrentSpeedPct()        : 0;
    payload.damper = _servo  ? (uint8_t)_servo->getCurrentPositionPct()   : 0;

    // Setpoint
    payload.sp = _setpoint;

    // Lid-open
    payload.lid = _pid ? _pid->isLidOpen() : false;
    payload.lidEnabled = _pid ? _pid->isLidDetectionEnabled() : true;
    payload.lidTimeoutSeconds = _pid ? _pid->getLidTimeoutSeconds() : LID_OPEN_TIMEOUT_MS / 1000;
    payload.lidRemaining = _pid ? _pid->lidRemainingSeconds(millis()) : 0;
    payload.lidManual = _pid && _pid->isLidManual();

    // Meat targets from alarm manager
    payload.meat1Target = _alarm ? _alarm->getMeat1Target() : 0;
    payload.meat2Target = _alarm ? _alarm->getMeat2Target() : 0;

    // Fan mode
    payload.fanMode = _config ? _config->getFanMode() : "fan_and_damper";

    // Estimated done time
    payload.est = _estimatedTime;

    // Errors
    payload.errorCount = 0;
    if (_error) {
        auto activeErrors = _error->getErrors();
        for (size_t i = 0; i < activeErrors.size() && payload.errorCount < 8; i++) {
            char* message = payload.errors[payload.errorCount++];
            snprintf(message, sizeof(payload.errors[0]), "%s", activeErrors[i].message);
        }
    }
#endif

    return payload;
}

void BBQWebServer::sendHistory(uint32_t clientId) {
#ifndef NATIVE_BUILD
    if (!_session || !_ws) return;

    uint32_t count = _session->getPointCount();
    if (count == 0) return;

    // Build array of HistoryPoints from session data
    bbq_protocol::HistoryPoint* points =
        (bbq_protocol::HistoryPoint*)malloc(count * sizeof(bbq_protocol::HistoryPoint));
    if (!points) return;

    for (uint32_t i = 0; i < count; i++) {
        const DataPoint* dp = _session->getPoint(i);
        if (!dp) continue;

        points[i].ts = dp->timestamp;

        // Convert int16 temps (x10) back to float, check disconnect flags
        if (dp->flags & DP_FLAG_PIT_DISC)   points[i].pit = NAN;
        else                                 points[i].pit = dp->pitTemp / 10.0f;

        if (dp->flags & DP_FLAG_MEAT1_DISC) points[i].meat1 = NAN;
        else                                 points[i].meat1 = dp->meat1Temp / 10.0f;

        if (dp->flags & DP_FLAG_MEAT2_DISC) points[i].meat2 = NAN;
        else                                 points[i].meat2 = dp->meat2Temp / 10.0f;

        points[i].fan    = dp->fanPct;
        points[i].damper = dp->damperPct;
        points[i].sp     = _setpoint; // current setpoint (per-point sp not stored)
        points[i].lid    = (dp->flags & DP_FLAG_LID_OPEN) != 0;
    }

    float m1t = _alarm ? _alarm->getMeat1Target() : 0;
    float m2t = _alarm ? _alarm->getMeat2Target() : 0;

    size_t msgLen = 0;
    char* msg = bbq_protocol::buildHistoryMessage(points, count, _setpoint, m1t, m2t, &msgLen);
    free(points);

    if (msg) {
        _ws->text(clientId, msg, msgLen);
        free(msg);
    }
#endif
}

void BBQWebServer::handleWebSocketMessage(uint32_t clientId, const char* data, size_t len) {
#ifndef NATIVE_BUILD
    bbq_protocol::ParsedCommand cmd = bbq_protocol::parseCommand(data, len);

    switch (cmd.type) {
        case bbq_protocol::CmdType::SET_SP:
            _setpoint = cmd.setpoint;
            if (_onSetpoint) _onSetpoint(cmd.setpoint);
            Serial.printf("[WS] Client %u set setpoint to %.0f\n", clientId, cmd.setpoint);
            break;

        case bbq_protocol::CmdType::ALARM:
            if (cmd.hasMeat1Target && _onAlarm) _onAlarm("meat1", cmd.meat1Target);
            if (cmd.hasMeat2Target && _onAlarm) _onAlarm("meat2", cmd.meat2Target);
            if (cmd.hasPitBand && _onAlarm)     _onAlarm("pitBand", cmd.pitBand);
            break;

        case bbq_protocol::CmdType::SESSION_NEW:
            if (_onSession) _onSession("new", "");
            // Broadcast session reset to all clients
            {
                char buf[128];
                size_t n = bbq_protocol::buildSessionReset(buf, sizeof(buf), _setpoint);
                broadcastAuthenticated(buf, n);
            }
            break;

        case bbq_protocol::CmdType::SET_FAN_MODE:
            if (_onFanMode) _onFanMode(cmd.fanMode);
            Serial.printf("[WS] Client %u set fan mode to %s\n", clientId, cmd.fanMode);
            broadcastNow();
            break;

        case bbq_protocol::CmdType::SET_LID_ENABLED:
            if (_onLidEnabled) _onLidEnabled(cmd.lidEnabled);
            break; // Main loop applies and broadcasts the new controller state.
        case bbq_protocol::CmdType::SET_LID_TIMEOUT:
            if (_onLidTimeout) _onLidTimeout(cmd.lidTimeoutSeconds);
            break;

        case bbq_protocol::CmdType::OPEN_LID:
            if (_onOpenLid) _onOpenLid();
            break;

        case bbq_protocol::CmdType::RESUME_LID:
            if (_onResumeLid) _onResumeLid();
            break;

        case bbq_protocol::CmdType::SESSION_DOWNLOAD:
            if (_session) {
                String csvData = _session->toCSV();
                size_t envLen = 0;
                char* envelope = bbq_protocol::buildCSVDownloadEnvelope(
                    csvData.c_str(), csvData.length(), &envLen);
                if (envelope) {
                    _ws->text(clientId, envelope, envLen);
                    free(envelope);
                }
            }
            break;

        default:
            Serial.printf("[WS] Unknown message type from client %u\n", clientId);
            break;
    }
#endif
}

void BBQWebServer::onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                           AwsEventType type, void* arg, uint8_t* data, size_t len) {
#ifndef NATIVE_BUILD
    switch (type) {
        case WS_EVT_CONNECT:
            {
                auto* request = static_cast<AsyncWebServerRequest*>(arg);
                const auto token = WebAuth::tokenFromCookie(header(request, "Cookie"));
                if (!_auth.authenticated(token, authNow())) { client->close(1008, "Sign in required"); break; }
                _peers.add(client->id(), token);
            }
            Serial.printf("[WS] Client #%u connected from %s\n",
                          client->id(), client->remoteIP().toString().c_str());
            // Send history if session has data, otherwise send current snapshot
            if (_session && _session->getPointCount() > 0) {
                sendHistory(client->id());
            } else {
                bbq_protocol::DataPayload payload = buildDataPayload();
                char buf[1024];
                size_t n = bbq_protocol::buildDataMessage(buf, sizeof(buf), payload);
                _ws->text(client->id(), buf, n);
            }
            break;

        case WS_EVT_DISCONNECT:
            {
                _peers.remove(client->id());
            }
            Serial.printf("[WS] Client #%u disconnected.\n", client->id());
            break;

        case WS_EVT_DATA:
            {
                std::string token;
                if (!_peers.token(client->id(), token) || !_auth.authenticated(token, authNow())) {
                    client->close(1008, "Sign in required"); break;
                }
            }
            {
                AwsFrameInfo* info = (AwsFrameInfo*)arg;
                if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
                    // Complete text message received
                    handleWebSocketMessage(client->id(), (char*)data, len);
                }
            }
            break;

        case WS_EVT_ERROR:
            Serial.printf("[WS] Client #%u error.\n", client->id());
            break;

        case WS_EVT_PONG:
            break;
    }
#endif
}

#ifndef NATIVE_BUILD
void BBQWebServer::broadcastAuthenticated(const char* data, size_t len) {
    _peers.visit([this, data, len](uint32_t id, const std::string& token) {
        if (_auth.authenticated(token, authNow())) _ws->text(id, data, len);
        else _ws->close(id, 1008, "Sign in required");
    });
}
#endif
