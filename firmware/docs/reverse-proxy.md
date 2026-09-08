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

## Manual firmware upload

The bundled ElegantOTA page is available at `/newbbq/update`, but its own
JavaScript calls `/ota/start` and `/ota/upload` at the host root. To use that
page through Nginx, also add this location to the same `server` block:

```nginx
location ^~ /ota/ {
    proxy_pass http://192.168.0.29/ota/;
    proxy_http_version 1.1;
    proxy_request_buffering off;
    proxy_read_timeout 300s;
    client_max_body_size 8m;
}
```

This reserves `/ota/` on that hostname for this controller. If another app
already uses it, use the controller's direct LAN `/update` URL or a dedicated
hostname for manual uploads. GitHub update checks remain disabled for dev builds.

## Deploying the web changes

These files live in LittleFS, separately from `firmware.bin`. Deploy the updated
`data/` assets to the device's filesystem; a firmware-only upload does not change
the dashboard. Preserve the existing `config.json` and session files when
building a filesystem image, since uploading one replaces the whole filesystem.

## Checks

Run from the firmware directory:

```sh
node test/web/test_release_updates.cjs
node test/web/test_reverse_proxy.cjs
```

Through Nginx, `/newbbq` should redirect to `/newbbq/`,
`/newbbq/api/version` should return JSON, and the browser's Network panel should
show a `101 Switching Protocols` response for `/newbbq/ws` with continuing data.
