const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../../data',name),'utf8');
const app=read('app.js').replace(/\n\}\)\(\);\s*$/,`
  globalThis.ui={cacheDom,init,initAuth,fetchVersion,authRequest,openSettings,closeSettings,initControls,wsConnect,maybeReloadUi};
})();`);
const build=read('app.js').match(/var UI_BUILD = '([^']+)'/)[1];
assert.match(read('index.html'),new RegExp('src="app.js\\?v='+build+'"'));
assert.match(fs.readFileSync(path.join(__dirname,'../../src/config.h'),'utf8'),new RegExp('WEB_UI_BUILD\\s+"'+build+'"'));

function page({bucket=new Map(),missing=false}={}) {
  const nodes=new Map(),reloads=[],replaces=[],requests=[],sockets=[],sent=[];
  let version={version:'dev',releaseUpdatesEnabled:false,uiBuild:build};
  const node=id=>{
    if(missing&&id==='btnUseControllerValues') return null;
    if(!nodes.has(id))nodes.set(id,{get value(){return this._value||'';},set value(v){this._value=String(v);},hidden:true,style:{display:'none'},events:{},
      classList:{add(){},remove(){},toggle(){}},addEventListener(t,f){this.events[t]=f;},setAttribute(){}});
    return nodes.get(id);
  };
  class Socket {
    static OPEN=1;static CONNECTING=0;
    constructor(){this.readyState=1;this.bufferedAmount=0;sockets.push(this);}
    send(message){sent.push(JSON.parse(message));} close(){this.readyState=3;}
  }
  const context=vm.createContext({URL,URLSearchParams,WebSocket:Socket,
    console:{warn(){},log(){}},navigator:{},setTimeout(){return 1;},clearTimeout(){},
    sessionStorage:{getItem:k=>bucket.get(k),setItem:(k,v)=>bucket.set(k,v),removeItem:k=>bucket.delete(k)},
    window:{location:{href:'https://example.com/newbbq/',reload:()=>reloads.push(true),replace:u=>replaces.push(u)}},
    document:{baseURI:'https://example.com/newbbq/',activeElement:null,readyState:'loading',addEventListener(){},
      getElementById:node,querySelector:node,body:{style:{},classList:{add(){},remove(){}},setAttribute(){}}},
    fetch:async(resource,options)=>{
      requests.push({resource,options});
      return {ok:true,status:200,json:async()=>resource==='api/version'?version:{enabled:false,authenticated:true}};
    }});
  vm.runInContext(app,context);context.ui.cacheDom();node('authScreen').hidden=true;
  return {ui:context.ui,node,context,reloads,replaces,requests,bucket,sockets,sent,version:v=>{version=v;}};
}
async function clientUpdates() {
  const next={version:'dev',uiBuild:'next',releaseUpdatesEnabled:false};
  let p=page();p.version(next);await p.ui.fetchVersion();assert.equal(p.reloads.length,1);
  await p.ui.fetchVersion();assert.equal(p.reloads.length,1,'A stale fallback cannot cause an automatic reload loop');
  assert.equal(p.requests[0].options.cache,'no-store');
  const retry=page({bucket:p.bucket});retry.version(next);await retry.ui.fetchVersion();
  assert.equal(retry.reloads.length,0,'The one-attempt limit survives a document reload');
  p.version({version:'dev',uiBuild:build});await p.ui.fetchVersion();assert.equal(p.node('uiUpdateNotice').hidden,true);
  for(const display of ['', 'flex']) {
    p=page();p.node('updateOverlay').style.display=display;p.version(next);await p.ui.fetchVersion();
    assert.equal(p.reloads.length,0,'Production OTA visibility blocks automatic reload');
  }
  p=page();p.ui.initControls();p.ui.wsConnect();p.ui.openSettings();p.version(next);await p.ui.fetchVersion();
  assert.equal(p.reloads.length,0);p.ui.closeSettings();assert.equal(p.reloads.length,1);
  p=page();p.ui.initControls();p.ui.openSettings();p.node('pitSpInput').value='7';
  p.node('pitSpInput').events.input();p.context.document.activeElement={tagName:'INPUT'};
  p.version(next);await p.ui.fetchVersion();assert.equal(p.reloads.length,0,'Raw typing defers reload');
  p=page();p.ui.initAuth();p.node('newPassword').events.input();p.version(next);await p.ui.fetchVersion();
  assert.equal(p.reloads.length,0,'Credential edits defer reload');
  p=page();p.ui.initControls();p.ui.wsConnect();p.sockets[0].onopen();
  p.ui.openSettings();p.node('pitSpUp').events.click();p.version(next);await p.ui.fetchVersion();p.ui.closeSettings();
  assert.deepEqual(p.sent,[{type:'set',sp:230}]);
  assert.equal(p.reloads.length,0,'Closing after a dispatch does not interrupt retained editor intent');
  p=page();p.ui.wsConnect();p.sockets[0].bufferedAmount=20;p.version(next);await p.ui.fetchVersion();
  assert.equal(p.reloads.length,0,'Buffered socket messages defer automatic reload');
  p=page({missing:true});p.ui.init();assert.equal(p.replaces.length,1);
  assert.equal(new URL(p.replaces[0]).searchParams.get('ui'),build,'Mixed legacy HTML/JS gets one fresh document URL');
}

async function workerFailures() {
  const handlers={},stored=new Map(),pendingTimers=new Map();
  let nextTimer=0,putFails=false,openFails=false,mode='online';
  const scope='https://example.com/newbbq/';
  const context=vm.createContext({URL,Request,AbortController,
    self:{registration:{scope},addEventListener:(k,f)=>handlers[k]=f},
    setTimeout:f=>{const id=++nextTimer;pendingTimers.set(id,f);return id;},clearTimeout:id=>pendingTimers.delete(id),
    caches:{open:async()=>{
      if(openFails)throw Error('Storage unavailable');
      return {match:async r=>stored.get(typeof r==='string'?r:r.url)?.clone(),put:async(r,response)=>{if(putFails)throw Error('Quota');stored.set(typeof r==='string'?r:r.url,response);}};
    }},
    fetch:async(_request,options)=>{
      if(mode==='offline')throw Error('Offline');
      if(mode==='hang')return new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(Error('Timed out'))));
      return new Response(mode==='error'?'HTTP error':'FRESH code',{status:mode==='error'?500:200});
    }});
  vm.runInContext(read('sw.js'),context);
  async function get(resource='app.js') {
    const waits=[];let response;
    handlers.fetch({request:{method:'GET',url:scope+resource},respondWith:p=>response=p,waitUntil:p=>waits.push(p)});
    if(mode==='hang'){await Promise.resolve();[...pendingTimers.values()].forEach(f=>f());}
    const result=await response;await Promise.all(waits);return result&&result.text();
  }
  stored.set(scope+'app.js',new Response('OLD cached code'));putFails=true;
  assert.equal(await get(),'FRESH code','Cache write failure cannot mask a successful fresh response');
  openFails=true;assert.equal(await get(),'FRESH code','Cache open failure cannot block network access');
  openFails=false;mode='offline';assert.equal(await get(),'OLD cached code');
  mode='error';assert.equal(await get(),'OLD cached code');
  mode='hang';assert.equal(await get(),'OLD cached code','Bounded fetch uses available offline fallback');
  mode='online';putFails=false;assert.equal(await get('?ui=5'),'FRESH code');
  mode='offline';assert.equal(await get('?ui=5'),'FRESH code','Migration document URLs retain offline fallback');
}
async function failedInstall() {
  const handlers={};let skipped=0;
  const context=vm.createContext({URL,Request,
    self:{registration:{scope:'https://example.com/newbbq/'},skipWaiting:async()=>skipped++,addEventListener:(k,f)=>handlers[k]=f},
    caches:{open:async()=>({addAll:async()=>{throw Error('CDN unavailable');}})}});
  vm.runInContext(read('sw.js'),context);
  let install;handlers.install({waitUntil:p=>install=p});
  await assert.rejects(install,/CDN unavailable/);
  assert.equal(skipped,0,'Failed coherent precaching retains the previous installed worker');
}
(async()=>{await clientUpdates();await workerFailures();await failedInstall();console.log('PASS: executing-build migration, safe reload deferral/one-attempt limit, fresh code despite cache failures, bounded offline fallback and atomic shell install');})()
  .catch(error=>{console.error(error);process.exitCode=1;});
