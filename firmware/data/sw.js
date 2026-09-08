// Pit Claw - Service Worker
// Cache-first for app shell; data and updates go directly to the network.

var APP_BASE = self.registration.scope;
var CACHE_PREFIX = 'pitclaw:' + APP_BASE + ':';
var CACHE_VERSION = CACHE_PREFIX + 'v4';
var APP_SHELL = [
  './',
  'index.html',
  'app.js',
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
      return cache.addAll(APP_SHELL);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

// Activate: clean up only this installation's old caches.
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) {
          return key.startsWith(CACHE_PREFIX) && key !== CACHE_VERSION;
        }).map(function (key) {
          return caches.delete(key);
        })
      );
    }).then(function () {
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

// Fetch: serve the cached shell immediately and refresh it in the background.
self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET' || APP_SHELL.indexOf(event.request.url) === -1) {
    return;
  }

  var cachePromise = caches.open(CACHE_VERSION);
  var refresh = cachePromise.then(function (cache) {
    return fetch(event.request).then(function (response) {
      if (response && response.status === 200) {
        return cache.put(event.request, response.clone()).then(function () {
          return response;
        });
      }
      return response;
    });
  });

  event.waitUntil(refresh.catch(function () { /* Cached shell still works offline. */ }));
  event.respondWith(
    cachePromise.then(function (cache) {
      return cache.match(event.request);
    }).then(function (cached) {
      return cached || refresh;
    })
  );
});
