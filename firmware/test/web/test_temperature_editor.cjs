const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '../../data/app.js'), 'utf8').replace(/\n\}\)\(\);\s*$/, `
  globalThis.ui = {cacheDom, initControls, wsConnect, handleMessage, updateTemperatures, loadHistory, handleSessionReset, openSettings, closeSettings, lockDashboard,
    useControllerTemperatures: typeof useControllerTemperatures === 'function' ? useControllerTemperatures : undefined,
    units: value => { currentUnits = value; refreshAllDisplayValues(); }};
})();`);

function createUI() {
  const nodes = new Map(), timers = new Map(), sockets = [], sent = [];
  let clock = 0, nextTimer = 1;
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, {get value(){return this._value || '';},set value(v){this._value=String(v);},textContent:'',style:{},events:{},
      classList:{add(){},remove(){},toggle(){}},setAttribute(){},
      addEventListener(type, fn) { this.events[type] = fn; },
      dispatchEvent(event) { this.events[event.type]?.call(this, event); }});
    return nodes.get(id);
  };
  class Socket {
    static OPEN = 1; static CONNECTING = 0;
    constructor() { this.readyState = 1; sockets.push(this); }
    send(message) { sent.push(JSON.parse(message)); }
    close() { this.readyState = 3; }
  }
  class Clock extends Date { static now() { return clock; } }
  const context = vm.createContext({URL,Date:Clock,WebSocket:Socket,Event:class {constructor(type){this.type=type;}},
    console:{log(){},warn(){},error(){}},window:{},navigator:{},localStorage:{removeItem(){},getItem(){return null;},setItem(){}},
    setTimeout(fn, delay) { const id=nextTimer++; timers.set(id,{fn,at:clock+delay}); return id; },
    clearTimeout(id) { timers.delete(id); },
    document:{baseURI:'http://controller/',readyState:'loading',activeElement:null,addEventListener(){},
      getElementById:node,querySelector:node,body:{style:{},classList:{add(){},remove(){}}}}});
  vm.runInContext(source,context); context.ui.cacheDom(); context.ui.initControls();
  context.ui.wsConnect(); sockets[0].onopen();
  function advance(ms) {
    const until=clock+ms;
    while (true) {
      const next=[...timers].filter(([,t])=>t.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];
      if (!next) break;
      clock=next[1].at; timers.delete(next[0]); next[1].fn();
    }
    clock=until;
  }
  function snapshot(sp=225, meat1Target=180, meat2Target=170) {
    context.ui.handleMessage({type:'data',ts:1790293080+Math.floor(clock/1000),pit:null,meat1:null,meat2:null,sp,meat1Target,meat2Target});
  }
  const click = id => { if(!node(id).disabled) node(id).events.click.call(node(id)); };
  const edit = (id,value) => { node(id).value=value; node(id).dispatchEvent({type:'input'}); node(id).dispatchEvent({type:'change'}); };
  return {ui:context.ui,context,node,sockets,sent,advance,snapshot,click,edit};
}

for (const [input,up,down,field,base] of [
  ['pitSpInput','pitSpUp','pitSpDown','sp',225],
  ['meat1TargetInput','meat1TargetUp','meat1TargetDown','meat1Target',180],
  ['meat2TargetInput','meat2TargetUp','meat2TargetDown','meat2Target',170]
]) {
  for (const cadence of [100,450]) {
    const t=createUI(); t.snapshot(); t.ui.openSettings();
    for (let n=1;n<=4;n++) {
      t.click(up); t.advance(cadence); t.snapshot();
      assert.equal(Number(t.node(input).value),base+n*5,'Ordinary pre-dispatch and in-flight snapshots must not undo clicks');
    }
    t.advance(300);
    assert.equal(t.sent.at(-1)[field],base+20);
    t.advance(10000); t.snapshot();
    assert.equal(Number(t.node(input).value),base+20,'No time-based rollback');
    const accepted={sp:225,meat1Target:180,meat2Target:170}; accepted[field]=base+20;
    t.ui.updateTemperatures(accepted); accepted[field]=base+5; t.ui.updateTemperatures(accepted);
    assert.equal(Number(t.node(input).value),base+20,'Telemetry never releases an edited input');
    assert.match(t.node('temperatureEditStatus').textContent,/last requested/);
    assert.equal(t.node('btnUseControllerValues').hidden,false);
    const before=t.sent.length; t.click('btnUseControllerValues');
    assert.equal(Number(t.node(input).value),base+5);
    assert.equal(t.sent.length,before,'Reconciliation never writes to the controller');
    t.click(down); t.ui.closeSettings(); t.ui.openSettings();
    assert.equal(Number(t.node(input).value),base);
  }
}
{
  const t=createUI(); t.snapshot(); t.ui.openSettings();
  t.click('pitSpUp'); t.advance(100); t.ui.closeSettings(); t.ui.openSettings(); t.click('pitSpUp'); t.advance(300);
  assert.deepEqual(t.sent.map(m=>m.sp),[230,235],'Closing flushes once; immediate reopen preserves intent');
  assert.equal(Number(t.node('pitSpInput').value),235);
  t.snapshot(230,195,175);
  assert.equal(Number(t.node('meat1TargetInput').value),195,'Untouched fields follow real controller values');
  assert.equal(t.node('pitSetpoint').textContent,230,'Dashboard stays authoritative');
  t.click('pitSpDown'); t.ui.closeSettings(); t.ui.openSettings(); t.snapshot(225);
  assert.equal(Number(t.node('pitSpInput').value),230,'Returning to a previous value does not infer an ACK');
  t.click('btnUseControllerValues'); assert.equal(Number(t.node('pitSpInput').value),225);
}
for (const input of ['pitSpInput','meat1TargetInput','meat2TargetInput']) {
  const t=createUI(); t.snapshot(); t.context.document.activeElement=t.node(input);
  t.node(input).value='7'; t.node(input).dispatchEvent({type:'input'}); t.snapshot(250,195,190);
  assert.equal(t.node(input).value,'7','Incomplete typing survives snapshots before change');
  t.node(input).dispatchEvent({type:'change'});
  assert.equal(t.sent.length,0,'Invalid typing sends nothing');
  assert.equal(Number(t.node(input).value),input==='pitSpInput'?250:input==='meat1TargetInput'?195:190);
  if(input==='pitSpInput') {
    t.node(input).value='7'; t.click('pitSpUp'); t.advance(300);
    assert.equal(t.sent[0].sp,255,'Step from the last valid value, not invalid raw text');
  }
}
{
  const t=createUI(); t.snapshot(); t.edit('meat1TargetInput',''); t.snapshot();
  assert.equal(t.node('meat1TargetInput').value,'');
  assert.equal(t.node('meat1Target').textContent,180,'Draft clearing does not fake controller state');
  t.advance(300); assert.deepEqual(t.sent[0],{type:'alarm',meat1Target:null});
  t.snapshot(225,null,170); assert.equal(t.node('meat1Target').textContent,'---');
}
for (const action of ['disconnect','auth','reset']) {
  const t=createUI(); t.snapshot(); t.ui.openSettings(); t.click('pitSpUp'); t.click('meat1TargetUp');
  if(action==='disconnect') { t.sockets[0].readyState=3; t.sockets[0].onclose(); }
  if(action==='auth') t.ui.lockDashboard();
  if(action==='reset') t.ui.handleSessionReset({sp:225});
  t.advance(300); assert.equal(t.sent.length,0,'Forced boundaries cancel before closing');
  if(action!=='reset') assert.equal(t.node('pitSpInput').disabled,true);
  if(action==='auth') continue; // A fresh authenticated session is tested by test_auth_ui.cjs.
  t.ui.wsConnect(); t.sockets.at(-1).onopen(); t.snapshot(260,200,190);
  assert.equal(Number(t.node('pitSpInput').value),260);
  assert.equal(Number(t.node('meat1TargetInput').value),200);
}
{
  const t=createUI(); t.snapshot(); t.ui.units('C'); t.ui.openSettings();
  const base=Number(t.node('pitSpInput').value); t.click('pitSpUp'); t.snapshot();
  assert.equal(Number(t.node('pitSpInput').value),base+3); t.ui.units('F'); t.advance(300);
  const desired=Math.round((base+3)*9/5+32);
  assert.equal(Number(t.node('pitSpInput').value),desired);
  assert.deepEqual(t.sent,[{type:'set',sp:desired}],'Units render the edit without another command');
  t.ui.loadHistory({sp:250,meat1Target:195,meat2Target:null,data:[{ts:1790293080,pit:100,meat1:null,meat2:null,sp:225}]});
  assert.equal(t.node('pitSetpoint').textContent,250,'Historical samples cannot replace current settings');
  assert.equal(Number(t.node('pitSpInput').value),desired);
}
console.log('PASS: real data-path temperature ownership, canonical values, native-like input events, close/reopen, reconcile, units and forced cancellation');
