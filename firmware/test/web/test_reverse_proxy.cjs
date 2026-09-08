// Run with: node test/web/test_reverse_proxy.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '../../data', name), 'utf8');

const app = read('app.js').replace(/\n\}\)\(\);\s*$/, `
  globalThis.ui = { cacheDom, wsConnect, fetchVersion, uploadFirmwareOTA,
    notify: function () { notifyEnabled = true; sendNotification('Test', 'Body'); }
  };
})();`);

async function checkPage(base, directory) {
  const requests = [], sockets = [], notifications = [], registrations = [];
  class Socket {
    static OPEN = 1;
    static CONNECTING = 0;
    constructor(url) { sockets.push(url); }
  }
  class Notification {
    static permission = 'granted';
    constructor(title, options) { notifications.push(options); }
  }
  const nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, { style: {}, textContent: '', disabled: true });
    return nodes.get(id);
  };
  const context = vm.createContext({
    URL, WebSocket: Socket, Notification,
    window: { Notification }, navigator: {},
    document: {
      baseURI: base, readyState: 'loading', addEventListener() {},
      getElementById: node, querySelector: node
    },
    fetch: async (url, options) => {
      requests.push({ url: new URL(url, base), method: options?.method || 'GET' });
      return { ok: true, json: async () => ({ version: 'dev', releaseUpdatesEnabled: false }) };
    }
  });
  vm.runInContext(app, context);
  context.ui.cacheDom();
  context.ui.wsConnect();
  await context.ui.fetchVersion();
  // Verify upload routing with mocked responses; never write to a device.
  await context.ui.uploadFirmwareOTA(new ArrayBuffer(8));
  context.ui.notify();

  const origin = new URL(base).origin;
  assert.equal(sockets[0], origin.replace(/^http/, 'ws') + directory + 'ws');
  assert.deepEqual(requests.map(r => r.url.pathname), [
    directory + 'api/version', directory + 'ota/start', directory + 'ota/upload'
  ]);
  assert.ok(requests.every(r => r.url.origin === origin));
  assert.equal(requests[2].method, 'POST');
  assert.equal(notifications[0].icon, origin + directory + 'favicon.svg');

  const html = read('index.html');
  const localAssets = [...html.matchAll(/(?:src|href)="([^"]+)"/g)]
    .map(match => match[1]).filter(url => !url.startsWith('https://'));
  assert.ok(localAssets.length >= 5);
  for (const asset of localAssets) {
    assert.equal(new URL(asset, base).pathname, directory + path.basename(asset));
  }
  context.navigator.serviceWorker = {
    register: url => { registrations.push(new URL(url, base).href); return Promise.resolve(); }
  };
  for (const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(script[1], context);
  }
  assert.deepEqual(registrations, [origin + directory + 'sw.js']);
  const manifest = JSON.parse(read('manifest.json'));
  const manifestURL = origin + directory + 'manifest.json';
  assert.equal(new URL(manifest.start_url, manifestURL).href, origin + directory);
  assert.equal(new URL(manifest.scope, manifestURL).href, origin + directory);
  assert.equal(new URL(manifest.icons[0].src, manifestURL).href, origin + directory + 'favicon.svg');
}

async function checkWorker(scope) {
  const handlers = {}, stores = new Map(), deleted = [], openedWindows = [];
  let offline = false;
  const store = name => {
    if (!stores.has(name)) stores.set(name, new Map());
    return stores.get(name);
  };
  const clients = {
    claim: async () => {},
    matchAll: async () => [{ url: scope === 'https://example.com/'
      ? 'https://another.example/' : 'https://example.com/unrelated/', visibilityState: 'visible',
      focus() { assert.fail('Must not focus another app'); } }],
    openWindow: async url => openedWindows.push(url)
  };
  const context = vm.createContext({
    URL, clients,
    self: { registration: { scope }, clients, skipWaiting: async () => {},
      addEventListener: (name, callback) => { handlers[name] = callback; } },
    caches: {
      keys: async () => [...stores.keys()],
      delete: async name => { deleted.push(name); return stores.delete(name); },
      open: async name => ({
        addAll: async urls => urls.forEach(url => store(name).set(url, new Response('cached ' + url))),
        match: async request => store(name).get(request.url),
        put: async (request, response) => store(name).set(request.url, response)
      })
    },
    fetch: async () => {
      if (offline) throw new Error('Offline');
      return new Response('fresh');
    }
  });
  vm.runInContext(read('sw.js'), context);
  async function lifecycle(name, extra = {}) {
    const pending = [];
    handlers[name]({ ...extra, waitUntil: promise => pending.push(promise) });
    await Promise.all(pending);
  }
  await lifecycle('install');
  const current = [...stores.keys()][0];
  assert.ok(store(current).has(scope + 'app.js'));
  assert.ok(store(current).has(scope));
  assert.ok(!store(current).has('https://example.com/app.js') || scope === 'https://example.com/');
  const previous = current.replace(/v\d+$/, 'v0');
  store(previous);
  store('unrelated-app');
  store('pitclaw:https://example.com/otherbbq/:v0');
  await lifecycle('activate');
  assert.deepEqual(deleted, [previous], 'Other apps and installations keep their caches');

  async function get(url, method = 'GET') {
    const pending = [];
    let response;
    handlers.fetch({ request: { url, method },
      respondWith: promise => { response = promise; },
      waitUntil: promise => pending.push(promise)
    });
    const result = response && await response;
    await Promise.all(pending);
    return result;
  }
  offline = true;
  assert.equal(await (await get(scope + 'app.js')).text(), 'cached ' + scope + 'app.js');
  assert.equal(await get(scope + 'api/version'), undefined, 'API stays on the network');
  assert.equal(await get(scope + 'ota/start'), undefined, 'OTA start is never cached');
  assert.equal(await get(scope + 'ota/upload', 'POST'), undefined);
  offline = false;
  await get(scope + 'style.css');
  offline = true;
  assert.equal(await (await get(scope + 'style.css')).text(), 'fresh', 'Background refresh persists');
  await lifecycle('notificationclick', { notification: { close() {} } });
  assert.deepEqual(openedWindows, [scope]);
}

(async () => {
  for (const [base, directory] of [
    ['http://192.168.0.29/', '/'],
    ['https://bbq.example.com/', '/'],
    ['http://eugene-home.ddns.net/newbbq/', '/newbbq/'],
    ['https://example.com:8443/newbbq/index.html?view=live', '/newbbq/'],
    ['https://example.com/devices/smoker/', '/devices/smoker/']
  ]) await checkPage(base, directory);
  await checkWorker('https://example.com/newbbq/');
  await checkWorker('https://example.com/');
  console.log('PASS: root/prefix HTTP/HTTPS URLs, assets, API/OTA routing, WS, and scoped offline cache.');
})().catch(error => { console.error(error); process.exitCode = 1; });
