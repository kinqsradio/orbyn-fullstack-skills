import test from 'node:test';
import assert from 'node:assert/strict';
import {createRecoveryController, validItem, operationFeedback, reconcileCause, otaCompatible, healthComparison, captureApplicable, reusable} from './src/contracts.mjs';
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject}; };
test('screen boundary rejects late account completion even if transport ignores abort', async () => {
  const a=deferred(), b=deferred(), emitted=[];
  const c=createRecoveryController(account => account==='A'?a.promise:b.promise, s=>emitted.push(s));
  const first=c.load('A'); const second=c.load('B'); b.resolve([{id:'B-1'}]); await second;
  a.resolve([{id:'A-1'}]); await first; assert.equal(c.state.account,'B'); assert.equal(c.state.rows[0].id,'B-1');
  assert.ok(!emitted.some(s=>s.status==='ready' && s.account==='A'));
});
test('late error, disposal and offline retry preserve current owner', async () => {
  const a=deferred();let calls=0; const emitted=[];
  const c=createRecoveryController(()=>++calls===1?a.promise:Promise.resolve([{id:'B-2'}]),s=>emitted.push(s));
  const first=c.load('A'); await c.load('B');a.reject(new Error('old failure'));await first;
  assert.equal(c.state.status,'ready'); const n=emitted.length;c.dispose(); await c.load();assert.equal(emitted.length,n);
  let offline=true;const d=createRecoveryController(async()=>{if(offline)throw new Error('offline');return [];});
  await d.load();assert.equal(d.state.status,'error');offline=false;await d.load();assert.equal(d.state.status,'ready');
});
test('invalid route input is not a selected item',()=>{for(const value of [undefined,['A-1'],'../A-1','A-1?x','B'])assert.equal(validItem(value),null);assert.equal(validItem('A-12'),'A-12');});
test('notification stable identity preserves current retry and multiple surfaces',()=>{
 const f=operationFeedback(); const old=f.begin('save','panel'); const now=f.begin('save','panel');const other=f.begin('export','global');
 assert.equal(f.finish('save',old,'success'),false);f.remove('save',old);assert.equal(f.get('save').token,now);assert.equal(f.finish('save',now,'error'),true);assert.equal(f.get('export').token,other);
});
function tracker(){const records=[];let creates=0;return {records,get creates(){return creates;},async list(key){return {items:records.filter(r=>r.key===key),next:null,complete:true};},async create(input){const r={...input,id:'work-'+(++creates)};records.push(r);return r;},async read(id){return records.find(r=>r.id===id);}};}
const cause={repo:'owner/repo',root:'linux',id:'pool-exhaustion'};
test('unknown create result reconciles before replay; routed remains open',async()=>{
 const t=tracker(),create=t.create.bind(t);let lost=true;t.create=async input=>{const r=await create(input);if(lost){lost=false;throw new Error('lost response');}return r;};
 await assert.rejects(reconcileCause(t,cause,'head1','me'),/lost response/);const r=await reconcileCause(t,cause,'head1','me');assert.equal(t.creates,1);assert.equal(r.id,'work-1');r.status='routed';assert.equal((await reconcileCause(t,cause,'head1','me')).status,'routed');
});
test('partial inventory, duplicate, foreign owner, stale candidate and cross repo controls',async()=>{
 const t=tracker();t.list=async()=>({items:[],complete:false});await assert.rejects(reconcileCause(t,cause,'h','me'),/incomplete/);
 const u=tracker();const r=await reconcileCause(u,cause,'h','me');r.owner='other';await assert.rejects(reconcileCause(u,cause,'h','me'),/foreign/);r.owner='me';await assert.rejects(reconcileCause(u,cause,'new','me'),/stale/);
 u.records.push({...r,id:'duplicate'});await assert.rejects(reconcileCause(u,cause,'h','me'),/duplicate/);
 const v=tracker();await reconcileCause(v,cause,'h','me');await reconcileCause(v,{...cause,repo:'another/repo'},'h','me');assert.equal(v.creates,2);
});
test('pagination and changed readback cannot be treated as a completed claim',async()=>{
 const t=tracker();const r=await reconcileCause(t,cause,'h','me');let pages=0;t.list=async(key,cursor)=>{pages++;return cursor?{items:[r],next:null,complete:true}:{items:[],next:'next',complete:true};};
 assert.equal((await reconcileCause(t,cause,'h','me')).id,r.id);assert.equal(pages,2);
 t.read=async()=>({...r,owner:'foreign'});await assert.rejects(reconcileCause(t,cause,'h','me'),/foreign|readback/);
});
test('OTA compatibility uses actual channel to branch mapping and runtime',()=>{
 const binary={platform:'ios',runtime:'r1',channel:'preview'};
 const update={platform:'ios',runtime:'r1',branch:'candidate',addsNative:false};
 const map={channel:'preview',branch:'candidate',complete:true};
 assert.equal(otaCompatible(binary,update,map),true);
 for(const key of ['platform','runtime','branch']) assert.equal(otaCompatible(binary,{...update,[key]:'wrong'},map),false);
 assert.equal(otaCompatible(binary,{...update,addsNative:true},map),false);
 assert.equal(otaCompatible(binary,update,{...map,complete:false}),false);
 assert.equal(otaCompatible({}, {}, {}),false);
});
test('no samples, partial and incomparable health are not zero crashes',()=>{
 const a={complete:true,samples:100,failures:2,platform:'ios',runtime:'r',window:'w',denominator:'launches'};
 assert.equal(healthComparison(a,{...a,samples:0}).status,'unknown');assert.equal(healthComparison(a,{...a,complete:false}).status,'unknown');assert.equal(healthComparison(a,{...a,denominator:'downloads'}).status,'unknown');assert.equal(healthComparison(a,{...a,platform:'android'}).status,'incomparable');assert.equal(healthComparison(a,a).a,.02);
});
test('capture and cache evidence require matching target and trusted complete identity',()=>{
 const e={source:'s',binary:'b',screen:'detail',fixture:'f',platform:'ios'};
 assert.equal(captureApplicable(e,{...e,status:'ready'}),true);for(const status of ['blank','error','dialog'])assert.equal(captureApplicable(e,{...e,status}),false);assert.equal(captureApplicable(e,{...e,screen:'home',status:'ready'}),false);
 const k={skills:'s',harness:'h',scenario:'c',model:'m',effort:'medium',processing:'standard',tools:'t',sdk:'55',environment:'e'};assert.equal(reusable(k,{...k,trusted:true}),true);for(const key of Object.keys(k))assert.equal(reusable(k,{...k,[key]:'wrong',trusted:true}),false);assert.equal(reusable(k,{...k,trusted:false}),false);
});

test('malformed missing capture/cache/health identity cannot pass',()=>{
 assert.equal(captureApplicable({}, {status:'ready'}),false);assert.equal(reusable({}, {trusted:true}),false);
 for(const invalid of [{}, {complete:true}, {complete:true,samples:10,failures:11}, {complete:true,samples:NaN,failures:0}]) assert.equal(healthComparison(invalid,invalid).status,'unknown');
});
test('unknown null rejection keeps visible error instead of formatter crash',async()=>{
 const c=createRecoveryController(()=>Promise.reject(null));await c.load();assert.equal(c.state.status,'error');assert.equal(c.state.error,'null');
});
test('terminal records read current remote state, cursor cycles fail',async()=>{
 const t=tracker();const r=await reconcileCause(t,cause,'h','me');r.status='resolved';let reads=0;t.read=async()=>{reads++;return {...r,owner:'foreign'};};
 await assert.rejects(reconcileCause(t,cause,'h','me'),/foreign|readback/);assert.equal(reads,1);
 const u=tracker();u.list=async()=>({items:[],next:'same',complete:true});await assert.rejects(reconcileCause(u,cause,'h','me'),/cycle/);
});

test('current remote state outranks stale listing markers; missing scope is rejected',async()=>{
 const t=tracker();const r=await reconcileCause(t,cause,'h','me');t.list=async()=>({items:[{...r,candidate:'stale',owner:'old'}],next:null,complete:true});
 assert.equal((await reconcileCause(t,cause,'h','me')).candidate,'h');
 await assert.rejects(reconcileCause(t,{...cause,repo:''},'h','me'),/missing scope/);
});
