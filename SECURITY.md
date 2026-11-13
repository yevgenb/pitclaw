# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older releases | No |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer or use [GitHub's private vulnerability reporting](https://github.com/yevgenb/pitclaw/security/advisories/new)
3. Include steps to reproduce and potential impact
4. Allow reasonable time for a fix before public disclosure

## Scope

This is a hobbyist IoT device for BBQ temperature control. It stores network
credentials, shared-password hashes, calibration, cook history and diagnostic
events. Security concerns are primarily:

- Web UI, API, WebSocket controls and OTA uploads support optional shared-password
  authentication, disabled by default. Enable it in Settings → Access before
  exposing the controller through a reverse proxy.
- Use HTTPS on the public reverse proxy; the device's HTTP port belongs on the
  private LAN. See [proxy and authentication setup](firmware/docs/reverse-proxy.md).
- Configuration and session storage are private and cannot be downloaded as
  static files. Password hashes are salted; login sessions expire and can be revoked.
- The Wi-Fi diagnostic endpoint follows the same authentication policy. Logs
  include network addresses, signal readings and event/reason codes, but omit
  SSIDs, passwords and notification keys. Raw checkpoint files remain private;
  factory reset clears the log along with configuration and cook history.
- The current factory-reset routine does not erase WiFiManager station credentials
  held in ESP32 NVS; those are separate from LittleFS configuration.
