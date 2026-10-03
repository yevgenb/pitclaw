const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../../data/app.js'), 'utf8').replace(/\n\}\)\(\);\s*$/, `
  globalThis.ui = {cacheDom, initAuth, refreshAuth};
})();`);
async function check(base) {
  const nodes = new Map(), requests = [], sockets = [], timers = [], classes = new Set(['auth-pending']);
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, {style:{},value:'',hidden:false,classList:{toggle(){},add(){},remove(){}},events:{},
      addEventListener(event, handler) { this.events[event] = handler; }, focus() { this.focused = true; }});
    return nodes.get(id);
  };
  let status = { enabled: true, authenticated: false }, networkFailure = false, loginStatus = 401;
  class Socket {
    static CONNECTING = 0; static OPEN = 1;
    constructor(url) { this.url = url; this.readyState = 1; sockets.push(this); }
    close() { this.readyState = 3; }
  }
  const context = vm.createContext({URL, URLSearchParams, WebSocket:Socket, console:{log(){},warn(){},error(){}},window:{},navigator:{},
    setTimeout(callback) { timers.push(callback); return timers.length; }, clearTimeout(){},
    document: {baseURI:base,readyState:'loading',addEventListener(){},getElementById:node,querySelector:node,
      body:{style:{},classList:{add(...values){values.forEach(v=>classes.add(v));},remove(...values){values.forEach(v=>classes.delete(v));}}}},
    fetch: async (resource, options = {}) => {
      requests.push({url:new URL(resource,base),options});
      if (networkFailure) throw new Error('Offline');
      let code = 200, data = status;
      if (resource === 'api/auth/login') {
        code = loginStatus; data = {error:'Incorrect password'};
        if (code === 200) status = {enabled:true,authenticated:true};
      } else if (resource === 'api/auth/logout' || resource === 'api/auth/settings') {
        status = {enabled:resource === 'api/auth/logout' || options.body.includes('enabled=true'),authenticated:false};
      } else if (resource === 'api/version') data = {version:'dev',releaseUpdatesEnabled:false};
      return {ok:code === 200,status:code,json:async()=>data};
    }
  });
  vm.runInContext(source,context); context.ui.cacheDom(); context.ui.initAuth();
  const settle = () => new Promise(resolve=>setImmediate(resolve));
  await settle();
  assert.equal(sockets.length,0,'A locked dashboard must not open a websocket');
  assert.ok(classes.has('auth-locked')); assert.equal(node('loginForm').hidden,false);
  assert.equal(node('loginPassword').focused,true);
  node('loginPassword').value='wrong'; node('loginForm').events.submit({preventDefault(){}}); await settle();
  assert.equal(node('authMessage').textContent,'Incorrect password'); assert.equal(node('btnLogin').disabled,false);
  loginStatus=200; node('loginPassword').value='the test password'; node('loginForm').events.submit({preventDefault(){}}); await settle();
  assert.equal(node('loginPassword').value,''); assert.equal(node('authScreen').hidden,true);
  assert.equal(sockets.length,1); assert.equal(sockets[0].url,new URL('ws',base).href.replace(/^http/,'ws'));
  assert.ok(!classes.has('auth-locked'));
  const beforeShort=requests.length;
  for (const short of ['1234567','é'.repeat(7),'😀'.repeat(4)]) {
    node('newPassword').value=short; node('confirmPassword').value=short;
    node('authSettingsForm').events.submit({preventDefault(){}}); await settle();
    assert.equal(requests.length,beforeShort); assert.equal(node('authSettingsMessage').textContent,'Use at least 8 characters.');
  }
  node('newPassword').value='12345678'; node('confirmPassword').value='does not match';
  const before=requests.length;
  node('authSettingsForm').events.submit({preventDefault(){}}); await settle();
  assert.equal(requests.length,before); assert.equal(node('authSettingsMessage').textContent,'Passwords do not match.');
  node('confirmPassword').value=node('newPassword').value;
  node('authSettingsForm').events.submit({preventDefault(){}}); await settle();
  assert.equal(node('newPassword').value,''); assert.equal(node('confirmPassword').value,'');
  assert.ok(classes.has('auth-locked')); assert.equal(sockets[0].readyState,3,'Password changes close the existing client');
  status={enabled:true,authenticated:true}; await context.ui.refreshAuth();
  node('btnLogout').events.click(); await settle(); assert.ok(classes.has('auth-locked'));
  networkFailure=true; await context.ui.refreshAuth();
  assert.equal(node('btnAuthRetry').hidden,false); assert.ok(classes.has('auth-locked'));
  networkFailure=false; status={enabled:false,authenticated:true}; await context.ui.refreshAuth();
  assert.equal(node('authScreen').hidden,true); assert.equal(node('btnLogout').hidden,true);
  assert.equal(node('btnDisableAuth').hidden,true);
  for (const request of requests) {
    assert.ok(request.url.pathname.startsWith(new URL('.',base).pathname));
    if (request.url.pathname.includes('/api/auth')) assert.equal(request.options.cache,'no-store');
  }
}
(async()=>{
  for (const base of ['http://controller/', 'https://example.com/newbbq/']) await check(base);
  console.log('PASS: login errors/success, auth startup gate, settings validation, logout, network recovery and prefixed URLs');
})().catch(error=>{console.error(error);process.exitCode=1;});
