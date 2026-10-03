const assert = require('node:assert/strict');
const net = require('node:net');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const [binary, assets, directory] = process.argv.slice(2);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  const reservation = net.createServer();
  reservation.listen(0, '127.0.0.1'); await once(reservation, 'listening');
  const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve));
  const base = `http://127.0.0.1:${port}`;
  let process;
  async function start() {
    process = spawn(binary, [String(port), assets], { cwd: directory, stdio: ['ignore', 'pipe', 'inherit'] });
    await once(process.stdout, 'data');
  }
  async function stop() { process.kill('SIGTERM'); await once(process, 'exit'); }
  async function request(resource, values, cookie = '', headers = {}) {
    return fetch(base + resource, { headers: { Cookie: cookie, ...headers },
      ...(values === undefined ? {} : { method: 'POST', body: new URLSearchParams(values) }) });
  }
  async function socket(cookie = '', origin = base) {
    const client = net.connect(port, '127.0.0.1');
    client.on('error', () => {});
    const chunks = [];
    let closed = false;
    client.on('data', chunk => chunks.push(chunk)); client.on('close', () => { closed = true; });
    await once(client, 'connect');
    client.write(`GET /ws HTTP/1.1\r\nHost: 127.0.0.1:${port}\r\nOrigin: ${origin}\r\nCookie: ${cookie}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n`);
    await once(client, 'data');
    return { client, chunks, get closed() { return closed; } };
  }
  try {
    await start();
    assert.equal((await request('/api/version')).status, 200);
    const legacyProxy = await socket('', 'https://proxy.example');
    assert.match(legacyProxy.chunks[0].toString(), /101 Switching Protocols/, 'An anonymous legacy proxy keeps working while auth is off');
    legacyProxy.client.destroy();
    const password = 'passw0rd'; // Exactly eight characters must work through the real HTTP adapter.
    assert.equal((await request('/api/auth/settings', { enabled: 'true', password }, '', { Origin: 'https://evil.example' })).status, 403);
    assert.equal((await request('/api/auth/settings', { password })).status, 400);
    assert.equal((await request('/api/auth/settings', { enabled: 'true', password: '1234567' })).status, 400);
    assert.equal((await request('/api/auth/settings', { enabled: 'true', password: 'é'.repeat(7) })).status, 400);
    assert.equal((await request('/api/auth/settings', { enabled: 'true', password: 'x'.repeat(129) })).status, 400);
    assert.equal((await request('/api/auth/settings', { enabled: 'true', password })).status, 200);
    const cfg = JSON.parse(fs.readFileSync(path.join(directory, 'sim-auth.json'), 'utf8'));
    assert.equal(cfg.iterations, 20000);
    assert.equal(cfg.hash, crypto.pbkdf2Sync(password, Buffer.from(cfg.salt, 'hex'), cfg.iterations, 32, 'sha256').toString('hex'));
    assert.ok(!JSON.stringify(cfg).includes(password));
    for (const resource of ['/api/version', '/api/servo', '/update', '/ota/start', '/config.json', '/sim-auth.json'])
      assert.equal((await request(resource)).status, 401, resource);
    assert.equal((await request('/ota/upload', { file: 'untrusted firmware' })).status, 401);
    assert.equal((await request('/api/auth/login', { password: 'wrong' })).status, 401);
    assert.equal((await request('/api/auth/login', { password }, '', { Origin: 'null' })).status, 403);
    assert.equal((await request('/api/auth/login', { password: 'x'.repeat(2048) })).status, 413);
    const denied = await socket();
    assert.match(denied.chunks[0].toString(), /401/); denied.client.destroy();
    const login = await request('/api/auth/login', { password }, '', { 'X-Forwarded-Proto': 'https' });
    assert.equal(login.status, 200);
    assert.match(login.headers.get('set-cookie'), /HttpOnly; SameSite=Strict/);
    assert.match(login.headers.get('set-cookie'), /Secure/);
    const cookie = login.headers.get('set-cookie').split(';')[0];
    assert.equal((await request('/api/version', undefined, cookie)).status, 200);
    assert.equal((await request('/config.json', undefined, cookie)).status, 404);
    assert.equal((await request('/api/auth/settings', { enabled: 'false' }, 'pitclaw_session=forged')).status, 401);
    assert.equal((await request('/ota/start', undefined, cookie, { Origin: 'https://evil.example' })).status, 403);
    const forbidden = await socket(cookie, 'https://evil.example');
    assert.match(forbidden.chunks[0].toString(), /403/); forbidden.client.destroy();
    const ws = await socket(cookie);
    assert.match(ws.chunks[0].toString(), /101 Switching Protocols/);
    await pause(80);
    assert.match(Buffer.concat(ws.chunks).toString(), /"type":"data"/);
    const command = Buffer.from('{"type":"set","sp":250}');
    const mask = Buffer.from([1, 2, 3, 4]);
    const frame = Buffer.alloc(6 + command.length); frame[0] = 0x81; frame[1] = 0x80 | command.length; mask.copy(frame, 2);
    command.forEach((byte, i) => { frame[6 + i] = byte ^ mask[i % 4]; }); ws.client.write(frame);
    await pause(80); assert.match(Buffer.concat(ws.chunks).toString(), /"sp":250/);
    assert.equal((await request('/api/auth/logout', {}, cookie)).status, 200);
    await pause(100); assert.equal(ws.closed, true, 'Logout closes established sockets');
    assert.equal((await request('/api/version', undefined, cookie)).status, 401);
    let response = await request('/api/auth/login', { password });
    const renewed = response.headers.get('set-cookie').split(';')[0];
    await stop();
    const legacy = { enabled: true, salt: cfg.salt,
      hash: crypto.pbkdf2Sync(password, Buffer.from(cfg.salt, 'hex'), 600000, 32, 'sha256').toString('hex') };
    fs.writeFileSync(path.join(directory, 'sim-auth.json'), JSON.stringify(legacy));
    await start();
    assert.equal((await request('/api/version')).status, 401, 'Authentication survives restart');
    assert.equal((await request('/api/version', undefined, renewed)).status, 401, 'Sessions do not survive restart');
    response = await request('/api/auth/login', { password });
    assert.equal(response.status, 200);
    const migrated = JSON.parse(fs.readFileSync(path.join(directory, 'sim-auth.json'), 'utf8'));
    assert.equal(migrated.iterations, 20000, 'Legacy credentials migrate on successful login');
    assert.notEqual(migrated.salt, legacy.salt);
    assert.equal(migrated.hash, crypto.pbkdf2Sync(password, Buffer.from(migrated.salt, 'hex'), migrated.iterations, 32, 'sha256').toString('hex'));
    await stop(); await start();
    response = await request('/api/auth/login', { password });
    assert.equal(response.status, 200, 'The same password works after migration and reboot');
    const fresh = response.headers.get('set-cookie').split(';')[0];
    const beforeDisable = await socket(fresh);
    assert.equal((await request('/api/auth/settings', { enabled: 'false' }, fresh)).status, 200);
    await pause(100); assert.equal(beforeDisable.closed, true, 'Settings changes force clients to refresh auth status');
    assert.equal((await request('/api/version')).status, 200);
    assert.equal((await request('/sim-auth.json')).status, 404);
    console.log('PASS: production HTTP/WS adapter, protected uploads, PBKDF2 vectors and legacy migration across reboot, private files, CSRF and logout');
  } finally { if (process && process.exitCode === null) await stop(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
