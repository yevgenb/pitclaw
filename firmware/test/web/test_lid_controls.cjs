const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const src = fs.readFileSync(path.join(__dirname,'../../data/app.js'),'utf8').replace(/\n\}\)\(\);\s*$/,`
  globalThis.ui={cacheDom,initControls,wsConnect,applyLidState,
    prediction: values=>{chartData[0]=values.map((_,i)=>i);chartData[2]=values;updateSinglePrediction(2,203,dom.meat1Prediction);}};
})();`);
const html = fs.readFileSync(path.join(__dirname, '../../data/index.html'), 'utf8');
assert.doesNotMatch(html, /btnResumeLid|Resume now|btnSettingsLidAction/);
const nodes = new Map(), sockets = [], sent = [];
function node(id) {
  if(!nodes.has(id)) nodes.set(id,{id,style:{},hidden:false,disabled:false,checked:false,events:{},
    classList:{add(){},remove(){},toggle(){}},setAttribute(k,v){this[k]=v;},addEventListener(type,fn){this.events[type]=fn;}});
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
context.ui.applyLidState({lidEnabled:true,lid:true,lidRemaining:83,lidManual:false});
assert.equal(node('lidBanner').hidden,false); assert.match(node('lidStatus').textContent,/1:23/);
assert.equal(node('btnLidAction').disabled,false);
node('btnLidAction').events.click();
assert.deepEqual(sent.pop(),{type:'lid',action:'resume'});
node('lidEnabled').checked=false; node('lidEnabled').events.change.call(node('lidEnabled'));
assert.deepEqual(sent.pop(),{type:'config',lidEnabled:false});
assert.equal(node('lidEnabled').checked,true); // Not an optimistic/local-only toggle.
context.ui.applyLidState({lidEnabled:false,lid:false,lidRemaining:0,lidManual:false});
assert.equal(node('lidEnabled').checked,false); assert.equal(node('lidBanner').hidden,true);
assert.equal(node('btnLidAction').textContent,'Open lid');
assert.equal(node('btnLidAction').disabled,false); // Manual works with detection Off.
node('btnLidAction').events.click(); assert.deepEqual(sent.pop(),{type:'lid',action:'open'});
context.ui.applyLidState({lidEnabled:false,lid:true,lidRemaining:120,lidManual:true});
assert.match(node('lidStatus').textContent,/manual pause/);
assert.equal(node('btnLidAction').textContent,'Close lid');
assert.equal(node('btnLidAction')['aria-pressed'],'true');
node('btnLidAction').events.click(); assert.deepEqual(sent.pop(),{type:'lid',action:'resume'});
context.ui.applyLidState({lidEnabled:true,lid:true,lidRemaining:120,lidManual:false}); // Touchscreen change syncs.
node('btnLidAction').events.click(); assert.deepEqual(sent.pop(),{type:'lid',action:'resume'});
context.ui.applyLidState({lidEnabled:true,lid:false,lidManual:false,lidTimeoutSeconds:180});
assert.equal(node('lidTimeoutSeconds').value,'180');
assert.equal(node('lidTimeoutSeconds').disabled,false);
node('lidTimeoutSeconds').value='300'; node('lidTimeoutSeconds').events.change.call(node('lidTimeoutSeconds'));
assert.deepEqual(sent.pop(),{type:'config',lidTimeoutSeconds:300});
for(const invalid of ['', '0', '29', '31', '601', '90.5', 'bad']) {
  node('lidTimeoutSeconds').value=invalid; node('lidTimeoutSeconds').events.change.call(node('lidTimeoutSeconds'));
  assert.equal(sent.length,0); assert.equal(node('lidTimeoutSeconds').value,'180');
}
context.document.activeElement=node('lidTimeoutSeconds'); node('lidTimeoutSeconds').value='60';
context.ui.applyLidState({lidEnabled:true,lid:false,lidManual:false,lidTimeoutSeconds:300});
assert.equal(node('lidTimeoutSeconds').value,'60'); // Updates do not overwrite ongoing typing.
context.document.activeElement=null; node('lidTimeoutSeconds').events.change.call(node('lidTimeoutSeconds'));
assert.deepEqual(sent.pop(),{type:'config',lidTimeoutSeconds:60});
context.ui.applyLidState({lidEnabled:true,lid:false,lidManual:false,lidTimeoutSeconds:60});
assert.equal(node('lidTimeoutSeconds').value,'60');
sockets[0].readyState=3; sockets[0].onclose();
assert.equal(node('btnLidAction').disabled,true); assert.equal(node('lidEnabled').disabled,true);
assert.equal(node('lidTimeoutSeconds').disabled,true);
node('btnLidAction').events.click(); assert.equal(sent.length,0);
context.ui.wsConnect(); sockets[1].onopen(); assert.equal(node('lidEnabled').disabled,true);
context.ui.applyLidState({lidEnabled:false,lid:false,lidRemaining:0,lidManual:false}); assert.equal(node('lidEnabled').checked,false);
context.ui.applyLidState({lidEnabled:true,lid:false,lidRemaining:0});
assert.equal(node('btnLidAction').disabled,true); // Old server supports resume but not manual Open.
context.ui.applyLidState({lid:true}); assert.equal(node('btnLidAction').disabled,true);
assert.equal(node('lidTimeoutSeconds').disabled,true); // Older firmware.
node('meat1Prediction').textContent='Stale estimate'; context.ui.prediction([150,160,null]);
assert.equal(node('meat1Prediction').textContent,'');
context.ui.prediction([150]); assert.equal(node('meat1Prediction').textContent,'Calculating...');
console.log('PASS: web single lid toggle events, countdown, shared state, disconnect and reconnect');
