const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../../data/app.js'), 'utf8').replace(/\n\}\)\(\);\s*$/, `
  globalThis.ui = { cacheDom, handleMessage, loadHistory, restoreCookTimer, tickCookTimer,
    state: () => ({chartData, cookTimerStart, latestServerTs, notifyMeat1Fired}),
    enableNotifications: () => { notifyEnabled = true; meat1Target = 203; },
    predictDoneTime, updatePitPrediction };
})();`);
const now = 1790293080;
class FixedDate extends Date { static now() { return now * 1000; } }
function createUI() {
  const nodes = new Map(), storage = new Map();
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {style: {}, classList: {add(){}, remove(){}, toggle(){}},
      setAttribute(){}, textContent: '', value: ''});
    return nodes.get(id);
  }
  const context = vm.createContext({Date: FixedDate, console, window: {}, navigator: {},
    localStorage: {getItem: k => storage.get(k), setItem: (k,v) => storage.set(k,v), removeItem: k => storage.delete(k)},
    document: {readyState:'loading', addEventListener(){}, getElementById:node, querySelector:node}});
  vm.runInContext(source, context); context.ui.cacheDom();
  return {ui: context.ui, node, storage};
}
function sample(ts, pit = 70, meat1 = null) {
  return {type:'data', ts, pit, meat1, meat2:null, fan:0, damper:0, sp:225};
}
{
  const {ui, node, storage} = createUI();
  storage.set('bbq_cook_timer_start', '10000'); ui.restoreCookTimer();
  assert.equal(ui.state().cookTimerStart, null);
  ui.handleMessage(sample(10000, 70, 90)); ui.tickCookTimer();
  assert.equal(ui.state().latestServerTs, now);
  assert.equal(ui.state().cookTimerStart, now);
  assert.equal(node('cookTimer').textContent, '00:00:00');
  ui.handleMessage(sample(now + 2, 71, 91)); ui.tickCookTimer();
  assert.equal(node('cookTimer').textContent, '00:00:02');
  ui.handleMessage(sample(now + 1, 72, 92)); // Clock correction preserves a sorted axis.
  assert.deepEqual(Array.from(ui.state().chartData[0]), [now, now + 1]);
}
{
  const {ui, node} = createUI();
  ui.enableNotifications();
  for (const invalid of [null, -1, 5000, NaN, Infinity, '5000']) {
    ui.handleMessage(sample(now, null, invalid));
    assert.equal(ui.state().chartData[2][0], null);
    assert.equal(ui.state().cookTimerStart, null);
    assert.equal(node('pitPrediction').textContent, '');
    assert.equal(ui.state().notifyMeat1Fired, false);
  }
  ui.loadHistory({data: [sample(10000, 70, 5000), sample(now, 80, 5000), sample(now + 5, 85, 100)]});
  assert.deepEqual(Array.from(ui.state().chartData[0]), [now, now + 5]);
  assert.deepEqual(Array.from(ui.state().chartData[2]), [null, 100]);
  assert.equal(ui.state().cookTimerStart, now + 5);
}
{
  const {ui, node} = createUI();
  for (let i = 0; i < 12; i++) ui.handleMessage(sample(now + i, 70));
  assert.equal(node('pitPrediction').textContent, 'Waiting for temperature rise');
  assert.equal(ui.predictDoneTime(1, 225), null);
  ui.handleMessage(sample(now + 12, 225));
  assert.equal(node('pitPrediction').textContent, '');
}
{
  const {ui, node} = createUI();
  for (let i = 0; i < 10; i++) ui.handleMessage(sample(now + i, 100 + i));
  const prediction = ui.predictDoneTime(1, 225);
  assert.ok(prediction);
  assert.ok(Math.abs(prediction.doneTime - (now + 125)) < 0.001);
  assert.match(node('pitPrediction').textContent, /\(/);
  ui.handleMessage(sample(now + 10, null));
  assert.equal(ui.predictDoneTime(1, 225), null);
  assert.equal(node('pitPrediction').textContent, '');
  ui.handleMessage(sample(now + 11, 110));
  assert.equal(ui.predictDoneTime(1, 225), null); // Old trend must not bridge disconnects.
}
console.log('PASS: device time, invalid live/history readings, clock correction and PIT estimates');
