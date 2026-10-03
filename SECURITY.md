# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older releases | No |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer or use [GitHub's private vulnerability reporting](https://github.com/MrMatt57/pitclaw/security/advisories/new)
3. Include steps to reproduce and potential impact
4. Allow reasonable time for a fix before public disclosure

## Scope

This is a hobbyist IoT device for BBQ temperature control. It runs on a local Wi-Fi network and does not handle sensitive personal data. Security concerns are primarily:

- Web UI, API, WebSocket controls and OTA uploads support optional shared-password
  authentication, disabled by default. Enable it in Settings → Access before
  exposing the controller through a reverse proxy.
- Use HTTPS on the public reverse proxy; the device's HTTP port belongs on the
  private LAN. See [proxy and authentication setup](firmware/docs/reverse-proxy.md).
- Configuration and session storage are private and cannot be downloaded as
  static files. Password hashes are salted; login sessions expire and can be revoked.
