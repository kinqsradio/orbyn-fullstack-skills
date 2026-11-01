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
