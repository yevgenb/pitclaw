# Nginx reverse proxy

The dashboard works at the device root or under a directory such as
`http://eugene-home.ddns.net/newbbq/`. It uses the page's host, port, scheme,
and directory for its assets, API, and WebSocket connection.
The path is not hard-coded in the application; `/newbbq/` is just the example
below. Choose any mount directory in your Nginx configuration.

Include the locations from [nginx-newbbq.conf](nginx-newbbq.conf) inside the
existing Nginx `server` block for `eugene-home.ddns.net`. Change the device IP
if needed, then run `nginx -t` and reload Nginx.

Open `/newbbq`; the redirect adds the required trailing slash. Both the
`location /newbbq/` and `proxy_pass http://192.168.0.29/` trailing slashes matter:
Nginx turns `/newbbq/api/version` into `/api/version` on the device. The Upgrade
headers allow `/newbbq/ws` to carry live readings and controls. See Nginx's
[URI forwarding documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)
and [WebSocket example](https://nginx.org/en/docs/http/websocket.html).

HTTP supports the dashboard. Use HTTPS on Nginx for service worker caching,
PWA installation, and browser notifications; these require a
[secure context](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API).
The dashboard automatically uses `wss://` with HTTPS. The device can remain HTTP.

For the current home deployment, use `https://eugene-home.ddns.net:8443/newbbq/`.
The router forwards WAN TCP **8443** to **192.168.0.139:443** (Nginx Proxy Manager).
WAN 443 remains reserved for router administration; forwarding it intercepted
the router's own local HTTPS interface on this router. The controller upstream
remains `http://192.168.0.29/`. Preserve `$http_host`, including `:8443`, for
authenticated requests. Redirect only `/newbbq` and `/ota/` to HTTPS port 8443;
the hostname also serves other applications.

## Optional authentication

Authentication is off by default. In **Settings → Access**, enter and confirm a
shared password, then select **Enable authentication**. Enable it from the LAN
before making the controller publicly reachable. The simple login screen asks
only for this password. Use at least 8 characters, up to 128 UTF-8 bytes.
Settings also lets you change the password, sign out, or turn authentication off.

When enabled, a session is required for every API, WebSocket, and firmware upload
route. The bundled HTML, scripts, styles, icon, manifest, service worker, and
authentication status/login endpoints stay public so the login can load. Private
LittleFS files, including `config.json`, are never served over HTTP, even to a
signed-in client. The service worker caches only the public shell and never
caches authentication responses or controller data.

Sessions use random tokens in HttpOnly, SameSite=Strict cookies, expire after
12 hours, and end on restart. Logout invalidates that session; changing the
password invalidates all sessions. Existing WebSockets stop receiving data and
commands when their session ends. Five failed logins within a minute cause a
temporary rate limit shared across clients. Passwords are stored as salted
PBKDF2-HMAC-SHA256 hashes with 20,000 iterations, tuned for the ESP32 while the
temperature control task continues running. This embedded-device cost provides
less resistance to offline guessing than the higher costs used on servers.
The cost is stored with each hash. Older 600,000-round credentials keep working:
the first successful login verifies the old hash, then atomically saves a new
salt and hash for the same password. That first login retains the old delay;
later logins use the new cost. If saving fails, the old credential stays valid.

Use **HTTPS on the public Nginx server** to encrypt passwords and session cookies.
The example sets `Host` to `$http_host` so browser Origin checks work, including
nonstandard ports, and overwrites `X-Forwarded-Proto` with `$scheme` so HTTPS
sessions get Secure cookies. Set those headers in every location forwarding to
the controller, including `/ota/`, before enabling authentication through Nginx.
While authentication is off, existing proxy configurations retain anonymous
access. Keep the controller on the private LAN and forward only through this
proxy. Use a separate hostname for each controller:
the session cookie uses `Path=/` so the mounted UI and root `/ota/` route share
the same session. Do not add a shared proxy cache for API or OTA responses.

If you forget the password, **Factory reset** on the physical touchscreen clears
authentication along with the other settings and cook data. The touchscreen and
temperature control continue working without a web login.

For API scripts, POST URL-encoded `password` to `/api/auth/login`, retain the
returned cookie, and send it with subsequent requests. No token is placed in a
WebSocket URL. Authenticated POST `/api/auth/logout` ends the session; POST
`/api/auth/settings` with `enabled=true&password=…` changes the password or with
`enabled=false` turns authentication off. Authentication APIs return JSON with
`Cache-Control: no-store`; denied requests return 401, cross-origin commands 403,
and rate-limited logins 429 with `Retry-After: 60`.

## Manual firmware upload

The bundled ElegantOTA page is available at `/newbbq/update`, but its own
JavaScript calls `/ota/start` and `/ota/upload` at the host root. To use that
page through Nginx, also add this location to the same `server` block:

```nginx
location ^~ /ota/ {
    proxy_pass http://192.168.0.29/ota/;
    proxy_http_version 1.1;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_request_buffering off;
    proxy_read_timeout 300s;
    client_max_body_size 8m;
}
```

This reserves `/ota/` on that hostname for this controller. If another app
already uses it, use the controller's direct LAN `/update` URL or a dedicated
hostname for manual uploads. GitHub update checks remain disabled for dev builds.

## Deploying the web changes

The firmware embeds the `data/` assets. Rebuild and upload `firmware.bin` to
update authentication and its login screen together, preserving LittleFS settings
and session files. Do not upload a fresh filesystem image to update the UI;
it replaces all saved settings, including authentication.

## Checks

Run from the firmware directory:

```sh
node test/web/test_release_updates.cjs
node test/web/test_reverse_proxy.cjs
node test/web/test_auth_ui.cjs
python3 test/auth/run_checks.py
```

Through Nginx, `/newbbq` should redirect to `/newbbq/`,
`/newbbq/api/version` should return JSON, and the browser's Network panel should
show a `101 Switching Protocols` response for `/newbbq/ws` with continuing data.
