// Pit Claw - Service Worker
// Network-first app shell with offline fallback; API/updates are never cached.

var APP_BASE = self.registration.scope;
var CACHE_PREFIX = 'pitclaw:' + APP_BASE + ':';
var CACHE_VERSION = CACHE_PREFIX + 'v14';
var APP_SHELL = [
  './',
  'index.html',
  'app.js',
  'app.js?v=5',
  'style.css',
  'favicon.svg',
  'manifest.json',
  'https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.iife.min.js',
  'https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.min.css'
].map(function (path) { return new URL(path, APP_BASE).href; });

// Install: pre-cache app shell
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      return cache.addAll(APP_SHELL.map(function (url) { return new Request(url, { cache: 'reload' }); }));
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

// Activate: clean up only this installation's old caches.
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) { return cache.match(APP_BASE); }).then(function (shell) {
      if (!shell) return; // Keep older caches if the completed shell is inaccessible.
      return caches.keys().then(function (keys) {
        return Promise.all(keys.filter(function (key) {
          return key.startsWith(CACHE_PREFIX) && key !== CACHE_VERSION;
        }).map(function (key) { return caches.delete(key); }));
      });
    }).catch(function () { /* Cache cleanup must not prevent activation. */ }).then(function () {
      return self.clients.claim();
    })
  );
});

// Notification click: focus or open the app
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      clientList = clientList.filter(function (client) {
        return client.url.startsWith(APP_BASE);
      });
      for (var i = 0; i < clientList.length; i++) {
        if (clientList[i].visibilityState === 'visible') {
          return clientList[i].focus();
        }
      }
      if (clientList.length > 0) {
        return clientList[0].focus();
      }
      return clients.openWindow(APP_BASE);
    })
  );
});

// Fetch: prefer current code online; a cached shell remains usable offline.
self.addEventListener('fetch', function (event) {
  var url = new URL(event.request.url);
  var shellPath = APP_SHELL.some(function (asset) {
    var entry = new URL(asset);
    return entry.origin === url.origin && entry.pathname === url.pathname;
  });
  if (event.request.method !== 'GET' || !shellPath) {
    return;
  }
  // Migration queries bypass a legacy exact-URL cache, but this worker stores
  // the document under its canonical URL so that bookmarking it works offline.
  var cacheKey = event.request;
  if (url.origin === new URL(APP_BASE).origin &&
      (url.pathname === new URL('./', APP_BASE).pathname || url.pathname === new URL('index.html', APP_BASE).pathname)) {
    url.search = ''; cacheKey = url.href;
  }

  // Storage is optional: a quota/cache failure must never hide fresh code.
  var cachePromise = caches.open(CACHE_VERSION).catch(function () { return null; });
  var controller = new AbortController();
  var timeout = setTimeout(function () { controller.abort(); }, 5000);
  var network = fetch(event.request, { signal: controller.signal, cache: 'no-store' })
    .finally(function () { clearTimeout(timeout); });
  event.waitUntil(network.then(function (response) {
    if (!response || response.status !== 200) return;
    var copy = response.clone();
    return cachePromise.then(function (cache) { if (cache) return cache.put(cacheKey, copy); });
  }).catch(function () { /* Storage and network failures preserve available fallback. */ }));
  function fallback() {
    return cachePromise.then(function (cache) { return cache && cache.match(cacheKey); });
  }
  event.respondWith(network.then(function (response) {
    if (response && response.status === 200) return response;
    return fallback().then(function (cached) { return cached || response; });
  }).catch(fallback));
});
