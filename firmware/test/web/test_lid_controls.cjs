const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const src = fs.readFileSync(path.join(__dirname,'../../data/app.js'),'utf8').replace(/\n\}\)\(\);\s*$/,`
  globalThis.ui={cacheDom,initControls,wsConnect,applyLidState};
})();`);
const nodes = new Map(), sockets = [], sent = [];
function node(id) {
  if(!nodes.has(id)) nodes.set(id,{id,style:{},hidden:false,disabled:false,checked:false,events:{},
    classList:{add(){},remove(){},toggle(){}},addEventListener(type,fn){this.events[type]=fn;}});
  return nodes.get(id);
}
class Socket {
  static OPEN=1; static CONNECTING=0;
  constructor(){this.readyState=1;sockets.push(this);}
  send(s){sent.push(JSON.parse(s));}
}
const context=vm.createContext({URL,WebSocket:Socket,console,window:{},navigator:{},
  setTimeout(){return 1;},clearTimeout(){},
  document:{baseURI:'http://controller/',readyState:'loading',addEventListener(){},getElementById:node,querySelector:node}});
vm.runInContext(src,context);
context.ui.cacheDom(); context.ui.initControls(); context.ui.wsConnect(); sockets[0].onopen();
assert.equal(node('lidEnabled').disabled,true); // Wait for an authoritative snapshot.
context.ui.applyLidState({lidEnabled:true,lid:true,lidRemaining:83});
assert.equal(node('lidBanner').hidden,false); assert.match(node('lidStatus').textContent,/1:23/);
assert.equal(node('btnResumeLid').disabled,false);
node('btnResumeLid').events.click();
assert.deepEqual(sent.pop(),{type:'lid',action:'resume'});
node('lidEnabled').checked=false; node('lidEnabled').events.change.call(node('lidEnabled'));
assert.deepEqual(sent.pop(),{type:'config',lidEnabled:false});
assert.equal(node('lidEnabled').checked,true); // Not an optimistic/local-only toggle.
context.ui.applyLidState({lidEnabled:false,lid:false,lidRemaining:0});
assert.equal(node('lidEnabled').checked,false); assert.equal(node('lidBanner').hidden,true);
assert.equal(node('btnSettingsResumeLid').hidden,true);
context.ui.applyLidState({lidEnabled:true,lid:true,lidRemaining:120}); // Touchscreen change syncs.
node('btnSettingsResumeLid').events.click(); assert.deepEqual(sent.pop(),{type:'lid',action:'resume'});
sockets[0].readyState=3; sockets[0].onclose();
assert.equal(node('btnResumeLid').disabled,true); assert.equal(node('lidEnabled').disabled,true);
node('btnResumeLid').events.click(); assert.equal(sent.length,0);
context.ui.wsConnect(); sockets[1].onopen(); assert.equal(node('lidEnabled').disabled,true);
context.ui.applyLidState({lidEnabled:false,lid:false,lidRemaining:0}); assert.equal(node('lidEnabled').checked,false);
context.ui.applyLidState({lid:true}); assert.equal(node('btnResumeLid').disabled,true); // Older firmware.
console.log('PASS: web toggle/resume events, countdown, shared state, disconnect and reconnect');
