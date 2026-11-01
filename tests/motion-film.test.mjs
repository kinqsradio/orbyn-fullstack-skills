// Cross-package specification and cut-safe frame controls, not a hosted model trial.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
const { DEFAULT_FILM, validateFilm, sampleFilm, subframeTimes, webVTT } = await import(pathToFileURL(join(process.argv[2], 'film.mjs')));
assert.equal(validateFilm(DEFAULT_FILM), DEFAULT_FILM);
const branded = structuredClone(DEFAULT_FILM); branded.palette = {paper:'#ffffff',ink:'#112233',accent:'#f0a000',deep:'#204030'}; branded.font = 'serif'; assert.equal(validateFilm(branded), branded); const badPalette = structuredClone(branded); badPalette.palette.paper = 'url(http://remote)'; assert.throws(() => validateFilm(badPalette));
const decimal = structuredClone(DEFAULT_FILM); decimal.shots[0].to = 4.1; decimal.shots[1].from = 4.1; assert.equal(validateFilm(decimal), decimal);
const unaligned = structuredClone(DEFAULT_FILM); unaligned.shots[0].to = 4.101; unaligned.shots[1].from = 4.101; assert.throws(() => validateFilm(unaligned));
for (let i = 0; i < 360; i++) {
  const time = i / 30, shot = DEFAULT_FILM.shots.find(s => time >= s.from && time < s.to);
  for (const t of subframeTimes(DEFAULT_FILM, i, 4, 1)) assert.ok(t >= shot.from && t < shot.to);
  const before = sampleFilm(DEFAULT_FILM, time); sampleFilm(DEFAULT_FILM, 0); sampleFilm(DEFAULT_FILM, 11.9); assert.deepEqual(sampleFilm(DEFAULT_FILM, time), before);
}
assert.equal(sampleFilm(DEFAULT_FILM, 3).scene, 'motion'); assert.equal(sampleFilm(DEFAULT_FILM, 7).scene, 'detail');
assert.equal(sampleFilm(DEFAULT_FILM, 5, true).typeOffset, 0);
for (const change of [s => s.fps = true, s => s.duration = Infinity, s => s.extra = 1, s => s.shots[1].id = s.shots[0].id, s => s.shots[0].title = '<b>'.repeat(100), s => s.shots[1].from = 4]) { const s = structuredClone(DEFAULT_FILM); change(s); assert.throws(() => validateFilm(s)); }
assert.throws(() => subframeTimes(DEFAULT_FILM, 360)); assert.throws(() => subframeTimes(DEFAULT_FILM, 0, 5));
const captions = webVTT([{ start: 0, end: 4.1, text: '<b>plain</b>\nSecond line' }], 12);
assert.ok(captions.includes('00:00:04.100')); assert.ok(captions.includes('&lt;b&gt;')); assert.ok(captions.startsWith('WEBVTT\n\n'));
assert.throws(() => webVTT([], 12));
// A blank line ends a WebVTT cue, so its second paragraph would become a broken cue.
for (const text of ['one\n\ntwo', 'one\r\n\r\ntwo', 'one\n  \ntwo', 'one\u0000two', '\nlost caption', '\r\nlost caption', '  \nlost caption']) assert.throws(() => webVTT([{ start: 0, end: 4, text }], 12), /Invalid film text|Caption text/);
assert.throws(() => webVTT([{ start: 0, end: 4, text: 'a' }, { start: 3, end: 5, text: 'b' }], 12));
console.log('Motion spec, decimal frame boundaries, deterministic backwards seek, cut-safe subframes and caption controls passed.');

const { readFile } = await import('node:fs/promises');
const { PRIMITIVES } = await import(pathToFileURL(join(process.argv[2], 'film-primitives.mjs')));
const gallery = JSON.parse(await readFile(join(process.argv[2], 'film-gallery.json'))); validateFilm(gallery);
assert.deepEqual(gallery.shots.map(s => s.primitive), PRIMITIVES);
for (const shot of gallery.shots) {
  const a = sampleFilm(gallery, shot.from + .2), b = sampleFilm(gallery, shot.from + 1.8);
  assert.equal(a.primitive.kind, shot.primitive); assert.notDeepEqual(a.primitive, b.primitive);
  sampleFilm(gallery, 0); assert.deepEqual(sampleFilm(gallery, shot.from + .2), a);
}
assert.ok(sampleFilm(gallery, 16.5).primitive.value < sampleFilm(gallery, 17.5).primitive.value);
assert.ok(sampleFilm(gallery, 22.2).primitive.sourceTime > sampleFilm(gallery, 23.8).primitive.sourceTime);
const futureRewind = structuredClone(gallery); futureRewind.shots[11].data.source = 'scene-13'; assert.throws(() => validateFilm(futureRewind));
const recursive = structuredClone(gallery); recursive.shots[12].primitive='rewind'; recursive.shots[12].data={source:'scene-11'}; assert.throws(() => validateFilm(recursive));
for (const url of ['https://remote/p.png','../a.png','media/a.svg','media/a.png?x']) { const bad=structuredClone(gallery); bad.shots[12].data.asset=url; assert.throws(()=>validateFilm(bad)); }
const unknown = structuredClone(gallery); unknown.shots[0].data.script='alert(1)'; assert.throws(()=>validateFilm(unknown));
console.log('All 14 original primitives vary with time; rewind references and raster source paths reject bad controls.');

const { stabilizePrimitive } = await import(pathToFileURL(join(process.argv[2], 'film-primitives.mjs')));
const counterA=sampleFilm(gallery,16.99).primitive, counterB=sampleFilm(gallery,17).primitive;
assert.equal(stabilizePrimitive(counterA,counterB).value,counterB.value);
const wordA=sampleFilm(gallery,.66).primitive, wordB=sampleFilm(gallery,.67).primitive;
assert.equal(stabilizePrimitive(wordA,wordB).word,wordB.word);

const background=structuredClone(DEFAULT_FILM);background.background={asset:'media/gallery.png',alt:'Original scenery study',fit:'cover',focal:{x:.5,y:.5},pan:{from:{x:-.05,y:0},to:{x:.05,y:0}},zoom:{from:1.2,to:1.3},dim:.4};validateFilm(background);
assert.ok(sampleFilm(background,0).background.x < sampleFilm(background,12).background.x); assert.equal(sampleFilm(background,12,true).background.x,-.05);
const uncovered=structuredClone(background);uncovered.background.zoom.from=1;assert.throws(()=>validateFilm(uncovered));

const song={version:1,title:'Synthetic long film',fps:60,bpm:120,duration:9549/60,shots:[{id:'whole',from:0,to:9549/60,composition:'title',title:'LONG',caption:'Synthetic full-length film.'}]};
assert.throws(()=>validateFilm(structuredClone(song)),/./);assert.equal(validateFilm({...structuredClone(song),longForm:true}).longForm,true);
assert.throws(()=>validateFilm({...structuredClone(song),longForm:false}));
assert.throws(()=>validateFilm({...structuredClone(song),longForm:true,duration:901,shots:[{...song.shots[0],to:901}]}));
const manyShots=structuredClone(song);manyShots.longForm=true;manyShots.shots=Array.from({length:25},(_,i)=>({...song.shots[0],id:'shot-'+i,from:i,to:i===24?song.duration:i+1}));assert.equal(validateFilm(manyShots).shots.length,25);

const stream=await import(pathToFileURL(join(process.argv[2],'frame-stream.mjs')));
const {PassThrough,Writable}=await import('node:stream');const {EventEmitter}=await import('node:events');const {mkdtemp,writeFile,symlink,rm}=await import('node:fs/promises');const {tmpdir}=await import('node:os');
assert.deepEqual(stream.angleArgs('darwin'),['--use-angle=metal']);assert.deepEqual(stream.angleArgs('linux'),[]);assert.deepEqual(stream.angleArgs('win32'),[]);
assert.ok(stream.softwareRenderer('ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device))'));assert.ok(!stream.softwareRenderer('ANGLE (Apple, ANGLE Metal Renderer: Apple M3)'));

// An asymmetric card tells every flip apart; a symmetric one would pass them all.
const card=stream.orientationChart(),rows=p=>stream.flipRows(p,card.width,card.height),columns=p=>{const o=new Uint8Array(p.length);for(let y=0;y<card.height;y++)for(let x=0;x<card.width;x++)o.set(p.subarray((y*card.width+x)*4,(y*card.width+x)*4+4),(y*card.width+card.width-1-x)*4);return o;};
const read=p=>stream.classifyOrientation(p,card.width,card.height);
assert.equal(read(card.pixels),'upright');assert.equal(read(rows(card.pixels)),'flipped-vertical');assert.equal(read(columns(card.pixels)),'flipped-horizontal');assert.equal(read(rows(columns(card.pixels))),'rotated-180');
assert.equal(read(new Uint8Array(card.pixels.length)),'unrecognized');assert.equal(read(card.pixels.map((v,i)=>i%4===3?255:v>>1)),'upright');
assert.deepEqual(rows(rows(card.pixels)),card.pixels);

// A full pipe holds the writer until the encoder drains; a dead encoder rejects instead of hanging.
const fakeEncoder=stdin=>Object.assign(new EventEmitter(),{stdin});
const slow=[];const held=new Writable({highWaterMark:4,write(chunk,_,done){slow.push(done);}});const sink=stream.encoderSink(fakeEncoder(held));
await sink.write(Buffer.alloc(2));let drained=false;const blocked=sink.write(Buffer.alloc(8)).then(()=>{drained=true;});await new Promise(r=>setTimeout(r,20));assert.equal(drained,false);
while(slow.length)slow.shift()();await new Promise(r=>setTimeout(r,20));while(slow.length)slow.shift()();await blocked;assert.equal(drained,true);
const dying=fakeEncoder(new Writable({highWaterMark:1,write(){}}));const lost=stream.encoderSink(dying);const pending=lost.write(Buffer.alloc(8));dying.emit('exit',1,null);await assert.rejects(pending,/Encoder exited early: 1/);await assert.rejects(lost.write(Buffer.alloc(1)),/Encoder exited early/);
const done=fakeEncoder(new PassThrough());const finished=stream.encoderSink(done);finished.finish();done.emit('exit',0,null);assert.equal(finished.failure,null);

const dir=await mkdtemp(join(tmpdir(),'frame-stream-'));await writeFile(join(dir,'index.html'),'<!doctype html>');await writeFile(join(dir,'notes.py'),'excluded');await writeFile(join(dir,'.secret.json'),'{}');
const sealed=await stream.sealSource(dir);assert.deepEqual([...sealed.files.keys()],['/index.html']);assert.deepEqual(sealed.excluded,['notes.py']);
const written=[];const host=stream.frameServer({files:sealed.files,frameBytes:4,write:async c=>written.push(c)});const base=await host.listen();
const post=(path,body)=>fetch(new URL(path,base),{method:'POST',body});
const served=await fetch(base+'index.html');assert.equal(served.status,200);assert.match(served.headers.get('content-security-policy'),/^default-src 'self'/);assert.equal((await fetch(base+'notes.py')).status,404);assert.equal((await post('/wrong-token/frame/0',new Uint8Array(4))).status,404);
assert.equal((await post(host.calibrationUrl,new Uint8Array([1,2,3,4]))).status,204);assert.deepEqual([...host.calibration],[1,2,3,4]);assert.equal(written.length,0);assert.equal(host.accepted,0);
assert.equal((await post(host.frameUrl(0),new Uint8Array(4))).status,204);assert.equal(host.accepted,1);assert.equal(host.failure,null);
assert.equal((await post(host.frameUrl(2),new Uint8Array(4))).status,409);assert.match(host.failure.message,/out of order/);
await host.close();
const shortHost=stream.frameServer({files:sealed.files,frameBytes:4,write:async()=>{}});const shortBase=await shortHost.listen();assert.equal((await fetch(new URL(shortHost.frameUrl(0),shortBase),{method:'POST',body:new Uint8Array(3)})).status,413);assert.match(shortHost.failure.message,/Frame size/);await shortHost.close();
await symlink('/etc/hosts',join(dir,'link.json'));await assert.rejects(stream.sealSource(dir),/Frame source link/);await rm(dir,{recursive:true});
