// Run with: node test/web/test_release_updates.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Expose the real updater inside its closure without initializing unrelated UI.
const source = fs.readFileSync(path.join(__dirname, '../../data/app.js'), 'utf8');
const instrumented = source.replace(/\n\}\)\(\);\s*$/, `
  globalThis.updater = { cacheDom, fetchVersion, checkForUpdate, performUpdate };
})();`);
assert.notEqual(instrumented, source);

function fixture(versionInfo, { versionFails = false, releaseFails = false } = {}) {
  const nodes = new Map();
  const requests = [];
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {
      textContent: '', disabled: true, style: { display: 'none' }
    });
    return nodes.get(id);
  }
  const context = vm.createContext({
    document: {
      readyState: 'loading', addEventListener() {},
      getElementById: node, querySelector: node
    },
    console: { warn() {} },
    fetch: async url => {
      requests.push(url);
      if (url === 'api/version') {
        return { ok: !versionFails, status: 500, json: async () => versionInfo };
      }
      assert.match(url, /^https:\/\/api\.github\.com\/repos\/.*\/releases\/latest$/);
      return {
        ok: !releaseFails, status: 503,
        json: async () => ({ tag_name: 'v0.3.0', assets: [] })
      };
    }
  });
  vm.runInContext(instrumented, context);
  context.updater.cacheDom();
  return { ...context.updater, requests, node };
}

async function main() {
  const pending = fixture({ version: '0.2.0', releaseUpdatesEnabled: true });
  pending.checkForUpdate(true);
  pending.performUpdate();
  assert.equal(pending.requests.length, 0, 'No update requests before capabilities arrive');

  for (const info of [
    { version: '0.2.0', releaseUpdatesEnabled: false },
    { version: '0.2.0' }, // Older firmware without the capability stays opted out.
    { version: 'dev', releaseUpdatesEnabled: true },
    { version: '0.2.0-dev', releaseUpdatesEnabled: true },
    { version: '0.2.0-rc.1', releaseUpdatesEnabled: true },
    { version: '0.2.0', board: 'simulator', releaseUpdatesEnabled: false }
  ]) {
    const ui = fixture(info);
    await ui.fetchVersion();
    await ui.checkForUpdate(true);
    ui.performUpdate();
    assert.deepEqual(ui.requests, ['api/version']);
    assert.equal(ui.node('btnCheckUpdate').disabled, true);
    assert.equal(ui.node('btnCheckUpdate').textContent, 'Updates disabled');
    assert.equal(ui.node('updateBanner').style.display, 'none');
  }

  const enabled = fixture({ version: '0.2.0', releaseUpdatesEnabled: true });
  await enabled.fetchVersion();
  assert.equal(enabled.requests.length, 2, 'Enabled stable build checks automatically');
  assert.equal(enabled.node('btnCheckUpdate').disabled, false);
  assert.equal(enabled.node('updateBanner').style.display, '');
  await enabled.checkForUpdate(true);
  assert.equal(enabled.requests.length, 3, 'Manual check uses the same path');
  assert.equal(enabled.node('btnCheckUpdate').textContent, 'v0.3.0 available');

  const current = fixture({ version: '0.3.0', releaseUpdatesEnabled: true });
  await current.fetchVersion();
  await current.checkForUpdate(true);
  assert.equal(current.node('btnCheckUpdate').textContent, 'Up to date');
  assert.equal(current.node('updateBanner').style.display, 'none');

  const unavailable = fixture({}, { versionFails: true });
  await unavailable.fetchVersion();
  unavailable.checkForUpdate(true);
  assert.deepEqual(unavailable.requests, ['api/version']);
  assert.equal(unavailable.node('btnCheckUpdate').disabled, true);

  const failed = fixture({ version: '0.2.0', releaseUpdatesEnabled: true }, { releaseFails: true });
  await failed.fetchVersion();
  await failed.checkForUpdate(true);
  assert.equal(failed.node('btnCheckUpdate').textContent, 'Check failed');
  assert.equal(failed.node('updateBanner').style.display, 'none');
  console.log('PASS: release update opt-in, dev/simulator gates, manual checks, and failures.');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
