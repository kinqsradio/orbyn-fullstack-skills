import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { validateScene, sampleScene, createThreeScene, GraphicsUnavailable, createAsyncResource, synchronizeGraphicsAnchor } from './three.mjs';
import { createJoltWorld, createSimulation, sampleParticles, seededRandom, validateSimulation } from './simulation.mjs';
import { validateEffects, createProgressiveRenderer } from './effects.mjs';
import { captureRenderCamera } from './graphics-demo.mjs';
const optional = async path => process.env.ORBYN_GRAPHICS_PROFILE ? import(pathToFileURL(resolve(process.env.ORBYN_GRAPHICS_PROFILE, 'node_modules', path)).href) : null;
const THREE = await optional('three/build/three.module.js');
const GLTFLoader = (await optional('three/examples/jsm/loaders/GLTFLoader.js'))?.GLTFLoader;
const JoltFactory = (await optional('jolt-physics/dist/jolt-physics.wasm-compat.js'))?.default;
const sceneSpec = () => ({ version: 1, sourceRevision: 'fixture-1', camera: { position: [0, 0, 5], target: [0, 0, 0] }, parts: [{ id: 'cube', geometry: { type: 'box' }, material: { color: '#bb8844' }, motion: [{ property: 'rotation', from: [0, 0, 0], to: [0, 1, 0], start: 0, end: 2 }] }] });
const canvas = () => ({ addEventListener() {}, removeEventListener() {} });
function unitRenderer() { return { isWebGLRenderer: true, setPixelRatio() {}, setSize() {}, compile() {}, render() {}, dispose() {} }; }
const spec = () => ({ version: 1, sourceRevision: 'physics-fixture', tickRate: 120, maxTicks: 600, bodies: [{ id: 'floor', motion: 'static', shape: { type: 'box', halfExtents: [5, .2, 5] }, position: [0, -.2, 0] }, { id: 'ball', shape: { type: 'sphere', radius: .3 }, position: [0, 2, 0] }], events: [{ tick: 80, op: 'set', id: 'ball', values: { friction: .8, restitution: .6 } }, { tick: 120, op: 'add', body: { id: 'second', shape: { type: 'box', halfExtents: [.2, .2, .2] }, position: [1, 3, 0] } }, { tick: 180, op: 'remove', id: 'second' }, { tick: 240, op: 'gravity', value: [0, -4, 0] }, { tick: 280, op: 'add', body: { id: 'second', shape: { type: 'sphere', radius: .2 }, position: [1, 2, 0] } }] });

test('scene sampling is pure across reverse seeks; malformed/material code input refuses', () => {
  const s = sceneSpec(); assert.deepEqual(sampleScene(s, 1), sampleScene(s, 1)); sampleScene(s, 2); assert.equal(sampleScene(s, 0).parts[0].rotation[1], 0);
  for (const mutate of [s => s.parts.push(s.parts[0]), s => s.parts[0].parent = 'cube', s => s.parts[0].material.onBeforeCompile = 'evil()', s => s.parts[0].position = [NaN, 0, 0], s => s.parts[0].geometry = { type: 'asset', path: 'https://remote/x' }]) { const s = sceneSpec(); mutate(s); assert.throws(() => validateScene(s)); }
});

test('actual Three hierarchy and raycaster identify visible source-bound part; renderer here is a unit double', { skip: !THREE }, async () => {
  const view = createThreeScene({ THREE, canvas: canvas(), spec: sceneSpec(), rendererFactory: unitRenderer }); await view.ready(); await view.render(0);
  assert.equal(view.parts.get('cube').rotation.y, 0); assert.equal(view.pick(0, 0)?.partId, 'cube'); assert.equal(view.pick(0, 0)?.sourceRevision, 'fixture-1');
  await view.render(2); assert.equal(view.parts.get('cube').rotation.y, 1); await view.render(0); assert.equal(view.parts.get('cube').rotation.y, 0);
  view.dispose(); assert.throws(() => view.pick(0, 0), /disposed/);
});

test('actual GLTFLoader parses original hashed local GLB and rejects corrupt closure bytes', { skip: !THREE || !GLTFLoader }, async () => {
  const bytes = await readFile(new URL('./graphics-demo-assets/marker.glb', import.meta.url)), data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), sha = createHash('sha256').update(bytes).digest('hex');
  const s = sceneSpec(); s.assets = [{ path: 'marker.glb', sha256: sha }]; s.parts[0].geometry = { type: 'asset', path: 'marker.glb' };
  const view = createThreeScene({ THREE, GLTFLoader, canvas: canvas(), spec: s, rendererFactory: unitRenderer, resolveAsset: async path => ({ path, data, sha256: sha }) }); await view.ready(); assert.ok(view.parts.get('cube').children.length > 0); view.dispose();
  const bad = createThreeScene({ THREE, GLTFLoader, canvas: canvas(), spec: s, rendererFactory: unitRenderer, resolveAsset: async () => ({ data: new ArrayBuffer(4), sha256: sha }) }); await assert.rejects(bad.ready(), /digest/); bad.dispose();
});

test('missing GPU and cancelled readiness remain explicit, late loading cannot resurrect owner', { skip: !THREE }, async () => {
  assert.throws(() => createThreeScene({ THREE, canvas: canvas(), spec: sceneSpec(), rendererFactory() { throw Error('No context'); } }), GraphicsUnavailable);
  const c = new AbortController(); c.abort(Error('stop')); assert.throws(() => createThreeScene({ THREE, canvas: canvas(), spec: sceneSpec(), signal: c.signal, rendererFactory: unitRenderer }), /stop/);
});

test('Jolt WASM physics replays exact checkpoint state across parameter, gravity and body-membership edits', { skip: !JoltFactory }, async () => {
  const J = await JoltFactory(), input = spec(), sim = createSimulation(input, createJoltWorld(J), { checkpointEvery: 60 });
  const first = sim.seek(360), checkpoint = sim.checkpoint(); sim.seek(40); const again = sim.seek(360); assert.deepEqual(again, first); assert.ok(first.bodies.some(b => b.id === 'second'));
  sim.seek(150); assert.equal(sim.seek(150).bodies.find(b => b.id === 'ball').friction, Math.fround(.8)); sim.seek(220); assert.ok(!sim.seek(220).bodies.some(b => b.id === 'second'));
  sim.restore(checkpoint); assert.deepEqual(sim.seek(360), first); const stale = structuredClone(checkpoint); stale.sourceRevision = 'other'; assert.throws(() => sim.restore(stale), /Incompatible/);
  const cancelled = new AbortController(); cancelled.abort(Error('cancelled physics')); assert.throws(() => sim.seek(500, { signal: cancelled.signal }), /cancelled/); assert.deepEqual(sim.seek(360), first);
  sim.dispose(); assert.throws(() => sim.seek(1), /disposed/);
});

test('simulation refuses event disorder, impossible membership and cancellation', () => {
  const input = spec(); [input.events[0], input.events[1]] = [input.events[1], input.events[0]]; assert.throws(() => validateSimulation(input));
  const missing = spec(); missing.events[0].id = 'none'; assert.throws(() => validateSimulation(missing));
  const random1 = seededRandom(42), random2 = seededRandom(42); assert.deepEqual(Array.from({ length: 8 }, random1), Array.from({ length: 8 }, random2));
});

test('particles are seeded time samples, not delta-clamped forward-only state', () => {
  const input = { seed: 12, capacity: 100, start: 1, duration: 2, rate: 32, life: 1, origin: [0, 0, 0], velocity: [0, 3, 0] };
  assert.deepEqual(sampleParticles(input, .5), []); const first = sampleParticles(input, 1.7); sampleParticles(input, 3.5); assert.deepEqual(sampleParticles(input, 1.7), first); assert.ok(first.length <= 100); assert.deepEqual(sampleParticles(input, 4), []);
  assert.notDeepEqual(sampleParticles({ ...input, seed: 13 }, 1.7), first); assert.throws(() => sampleParticles({ ...input, seed: Math.random() }, 1.7));
});

test('effect graph requires explicit supported ordering/options', () => {
  validateEffects({ version: 1, effects: [{ id: 'bloom', type: 'bloom', options: { intensity: .3 } }, { id: 'tone', type: 'tone-mapping' }] });
  assert.throws(() => validateEffects({ version: 1, effects: [{ id: 'tone', type: 'tone-mapping' }, { id: 'bloom', type: 'bloom' }] }), /last/);
  assert.throws(() => validateEffects({ version: 1, effects: [{ id: 'shader', type: 'bloom', options: { source: 'main(){}' } }] }), /Unknown/);
});

test('progressive lifecycle unit control resets every frame, counts actual samples and cancels stale queued work', async () => {
  const instances = [];
  class UnitTracer { constructor() { this.samples = 0; this.resets = 0; instances.push(this); } setScene() {} setSceneAsync() { throw Error('No installed BVH worker'); } reset() { this.samples = 0; this.resets++; } renderSample() { this.samples++; } dispose() { this.disposed = true; } }
  const renderer = { isWebGLRenderer: true }, scene = { traverse() {} }, p = createProgressiveRenderer({ PathTracer: UnitTracer, renderer, scene, camera: {}, samples: 3 });
  const a = await p.renderFrame({ key: 'frame0/source1', sample() {} }); assert.equal(a.measuredSamples.min, 3);
  await p.renderFrame({ key: 'frame1/source1', sample() {} }); assert.equal(instances[0].resets, 2);
  const old = p.renderFrame({ key: 'old', sample() {} }), next = p.renderFrame({ key: 'new', sample() {} }); await assert.rejects(old, /Superseded|Stale/); assert.equal((await next).key, 'new');
  const c = new AbortController(); c.abort(Error('owner cancelled')); await assert.rejects(p.renderFrame({ key: 'cancel', sample() {}, signal: c.signal }), /cancelled/); await p.dispose(); assert.equal(instances[0].disposed, true);
});

test('progressive no-progress and incompatible backend fail rather than manufacture qualification', async () => {
  class Stuck { constructor() { this.samples = 0; } setScene() {} reset() {} renderSample() {} dispose() {} }
  const p = createProgressiveRenderer({ PathTracer: Stuck, renderer: { isWebGLRenderer: true }, scene: { traverse() {} }, camera: {}, timeoutMs: 10, yieldTask: () => new Promise(r => setTimeout(r, 4)) });
  await assert.rejects(p.renderFrame({ key: 'timeout', sample() {} }), /deadline/); assert.equal(p.receipt.status, 'failed'); await p.dispose();
  assert.throws(() => createProgressiveRenderer({ PathTracer: Stuck, renderer: {}, backend: 'webgpu' }), GraphicsUnavailable);
});

test('asynchronous graphics creation is single flight and disposal fences late readiness', async () => {
  let complete, creates = 0, releases = 0;
  const resource = createAsyncResource(() => { creates++; return new Promise(resolve => { complete = resolve; }); }, () => { releases++; });
  const a = resource.get(), b = resource.get(); await Promise.resolve(); assert.equal(creates, 1); complete({ ready: true }); assert.equal(await a, await b); await resource.dispose(); assert.equal(releases, 1); await assert.rejects(resource.get(), /disposed/);
  let late;
  const pending = createAsyncResource(() => new Promise(resolve => { late = resolve; }), () => { releases++; }); const ready = pending.get(); await Promise.resolve(); const disposal = pending.dispose(); late({ ready: true }); await assert.rejects(ready, /disposed/); await disposal; assert.equal(releases, 2);
});

test('picked/restored graphics part selects its own review anchor without moving pending feedback', () => {
  const select = { value: 'part/floor', options: [{ value: 'part/floor' }, { value: 'part/ball' }, { value: 'part/marker' }] };
  assert.equal(synchronizeGraphicsAnchor(select, 'ball', null), 'part/ball');
  assert.equal(synchronizeGraphicsAnchor(select, 'marker', null), 'part/marker');
  assert.equal(synchronizeGraphicsAnchor(select, 'marker', { targetId: 'part/ball', text: 'Keep my original context' }), 'part/ball');
  assert.throws(() => synchronizeGraphicsAnchor(select, 'removed', null), /not mapped/);
});


test('backend transition snapshots the actual nondefault camera and transfers it across independently initialized Three views', { skip: !THREE }, async () => {
  class Controls { constructor() { this.target = new THREE.Vector3(); } addEventListener() {} removeEventListener() {} update() {} dispose() {} }
  const make = () => createThreeScene({ THREE, OrbitControls: Controls, canvas: canvas(), spec: sceneSpec(), rendererFactory: unitRenderer });
  const rasterView = make(), gpuView = make(); await Promise.all([rasterView.ready(), gpuView.ready()]);
  const reviewed = { type: 'perspective', position: [8, 4, -3], target: [.7, .5, -.2], fov: 37, near: .2, far: 440 };
  rasterView.setCamera(reviewed);
  const captured = captureRenderCamera(rasterView);
  // Simulate backend initialization yielding while another source view changes.
  await Promise.resolve(); rasterView.setCamera({ position: [-2, 1, 5] });
  gpuView.setCamera(captured); assert.deepEqual(captureRenderCamera(gpuView), reviewed);
  gpuView.setCamera({ position: [4, 6, 2], target: [-.5, 1, 0], fov: 52 });
  const reverse = captureRenderCamera(gpuView); rasterView.setCamera(reverse); assert.deepEqual(captureRenderCamera(rasterView), reverse);
  const explicit = captureRenderCamera(gpuView, reviewed); reviewed.position[0] = 999; assert.equal(explicit.position[0], 8);
  rasterView.dispose(); gpuView.dispose();
});
