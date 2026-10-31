import { createThreeScene, localAssetResolver, GraphicsUnavailable, createAsyncResource, synchronizeGraphicsAnchor } from './three.mjs';
import { createJoltWorld, createSimulation, createParticleCloud } from './simulation.mjs';
import { createEffectGraph, createProgressiveRenderer } from './effects.mjs';
const $ = id => document.getElementById(id), metrics = {}, lifetime = new AbortController();
const parameters = { 'ball-color': '#d99a5d', 'ball-roughness': .3, 'ball-metalness': .1, 'key-light': 3 };
let selectedPart = 'ball';
let raster, gpuView, active, simulation, particles, gpuParticles, graph, tracer, time = 0, frame = null, playing = false, previous = 0, mode = 'raster', generation = 0, dependencies, gpuDependencies;
const particleSpec = { seed: 431, capacity: 256, start: 1, duration: 2, rate: 48, life: 1.5, origin: [-1, .3, 0], velocity: [0, 3.4, 0], spread: 1.4 };
const effectSpec = { version: 1, effects: [{ id: 'glow', type: 'bloom', options: { intensity: .6, luminanceThreshold: .7 } }, { id: 'edge', type: 'vignette', options: { offset: .35, darkness: .4 } }, { id: 'display', type: 'tone-mapping' }] };
let sceneSpec, simulationSpec, profileURL, profile, gpuResource, renderTask = Promise.resolve(), renderWidth = 960, renderHeight = 540;
function status(message) { $('status').textContent = message; }
export function captureRenderCamera(view, restoredCamera = null, fallbackTarget = [0, 0, 0]) { if (restoredCamera) return structuredClone(restoredCamera); return { type: view.camera.isOrthographicCamera ? 'orthographic' : 'perspective', position: view.camera.position.toArray(), target: view.controls?.target.toArray() ?? structuredClone(fallbackTarget), near: view.camera.near, far: view.camera.far, ...(view.camera.isOrthographicCamera ? { span: view.camera.top - view.camera.bottom } : { fov: view.camera.fov }) }; }
function cameraContext(view) { return captureRenderCamera(view, null, sceneSpec.camera.target); }
function record() { metrics.time = time; metrics.mode = mode; metrics.parameters = structuredClone(parameters); metrics.camera = active ? cameraContext(active) : null; metrics.selectedSource = sceneSpec?.sourceRevision; $('metrics').textContent = JSON.stringify(metrics, null, 2); }
function pause() { playing = false; cancelAnimationFrame(frame); frame = null; $('play').textContent = 'Play'; }
function takeover() { pause(); tracer?.cancel(Error('Camera took over')); if (active && !tracer) { if (graph) graph.render(0); else active.renderer.render(active.scene, active.camera); } status('Camera control took over. Playback is paused.'); }
function clampTime(value) { if (!Number.isFinite(value) || value < 0 || value > 6) throw Error('Time must be within the authored six seconds'); return value; }
async function loadBundle(filename) {
  if (!['vendor-raster.mjs', 'vendor-webgpu.mjs', 'vendor-jolt.mjs'].includes(filename) || !profile.files[filename]) throw Error('Profile module missing');
  const url = new URL(filename, profileURL), response = await fetch(url, { signal: lifetime.signal, redirect: 'error' }); if (!response.ok) throw Error('Local profile module unavailable');
  const data = await response.arrayBuffer(), expected = profile.files[filename]; if (data.byteLength !== expected.bytes || data.byteLength > 16 * 1024 * 1024) throw Error('Profile module size mismatch');
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))].map(x => x.toString(16).padStart(2, '0')).join(''); if (digest !== expected.sha256) throw Error('Local profile module digest mismatch');
  return import(url.href); // filenames are fixed trusted build products, never imports from scene JSON.
}
function setPose(view, sample) {
  const states = Object.fromEntries(sample.bodies.map(body => [body.id, body])); view.sample(time, states);
  for (const identity of ['ball', 'second']) if (view.parts.has(identity)) view.parts.get(identity).visible = Boolean(states[identity]);
  view.parts.get('ball')?.traverse(object => { if (!object.material) return; for (const material of Array.isArray(object.material) ? object.material : [object.material]) { material.color.set(parameters['ball-color']); material.roughness = parameters['ball-roughness']; material.metalness = parameters['ball-metalness']; } });
  for (const object of view.scene.children) if (object.isDirectionalLight) object.intensity = parameters['key-light'];
}
function render(...args) { renderTask = renderNow(...args); return renderTask; }
async function settledRender() { let task; do { task = renderTask; await task; } while (task !== renderTask); }
async function renderNow(value, selectedMode = mode, restoredCamera = null) {
  if (!['raster', 'effects', 'pathtrace', 'webgpu'].includes(selectedMode)) throw Error('Unsupported graphics backend');
  // Snapshot before asynchronous backend readiness; a new backend must inherit the reviewed/orbited camera.
  const renderCamera = captureRenderCamera(active, restoredCamera, sceneSpec.camera.target);
  pause(); const current = ++generation;
  if (metrics.error) { (metrics.history ??= []).push({ mode: metrics.mode, error: metrics.error, failedRender: metrics.failedRender }); metrics.history = metrics.history.slice(-10); delete metrics.error; delete metrics.failedRender; }
  if (metrics.pathtrace) { metrics.lastCompletedProgressive = metrics.pathtrace; delete metrics.pathtrace; } delete metrics.effects; metrics.currentStatus = 'preparing';
  time = clampTime(value); const selectedTime = time; $('time').value = String(time); $('time-value').value = time.toFixed(3) + ' s'; mode = selectedMode;
  try {
  const sample = simulation.seekTime(time); metrics.simulationTick = sample.tick; metrics.bodyIds = sample.bodies.map(x => x.id);
  const oldTracer = tracer, oldGraph = graph; tracer = null; graph = null; oldGraph?.dispose(); if (oldTracer) await oldTracer.dispose();
  if (current !== generation) return;
  const selectedView = selectedMode === 'webgpu' ? await ensureGPU() : raster;
  if (current !== generation) return;
  active = selectedView;
  active.setCamera(renderCamera);
  $('raster').hidden = active !== raster; $('gpu').hidden = active === raster;
  setPose(active, sample); (active === raster ? particles : gpuParticles).sample(time);
  if (selectedMode === 'effects') { const selectedGraph = createEffectGraph({ ...dependencies, renderer: raster.renderer, scene: raster.scene, camera: raster.camera, spec: effectSpec, width: raster.renderer.domElement.width, height: raster.renderer.domElement.height }); graph = selectedGraph; await selectedGraph.ready(lifetime.signal); if (current !== generation) return; selectedGraph.render(0); metrics.effects = 'bloom + vignette + final ACES tone mapping'; }
  else if (selectedMode === 'pathtrace' || selectedMode === 'webgpu') {
    status(`Accumulating ${selectedMode === 'webgpu' ? 'WebGPU' : 'WebGL'} path-tracing samples…`);
    const selectedTracer = createProgressiveRenderer({ PathTracer: selectedMode === 'webgpu' ? gpuDependencies.WebGPUPathTracer : dependencies.WebGLPathTracer, renderer: active.renderer, scene: active.scene, camera: active.camera, backend: selectedMode === 'webgpu' ? 'webgpu' : 'webgl', samples: 4, timeoutMs: 45000 }); tracer = selectedTracer;
    const receipt = await selectedTracer.renderFrame({ key: `${sceneSpec.sourceRevision}/tick-${sample.tick}/${selectedMode}`, sample: () => setPose(selectedView, sample), signal: lifetime.signal });
    if (current !== generation) return; metrics.pathtrace = receipt;
  } else raster.renderer.render(raster.scene, raster.camera);
  if (current !== generation) return;
  metrics.backend = active.renderer.isWebGPURenderer ? 'WebGPU' : 'WebGL2'; metrics.currentStatus = 'completed'; record(); status(`Ready at ${time.toFixed(3)} s. ${sample.bodies.length} bodies; stable source-bound part picking enabled.`);
  } catch (error) { if (current !== generation) { (metrics.history ??= []).push({ time: selectedTime, mode: selectedMode, error: String(error), renderReceipt: error.renderReceipt }); metrics.history = metrics.history.slice(-10); return; } throw error; }
}
async function ensureGPU() {
  if (!gpuResource) gpuResource = createAsyncResource(async () => {
    if (!navigator.gpu) throw new GraphicsUnavailable('WebGPU API is unavailable on this browser/device');
    const adapter = await navigator.gpu.requestAdapter(); if (!adapter) throw new GraphicsUnavailable('WebGPU adapter is unavailable on this browser/device');
    gpuDependencies = await loadBundle('vendor-webgpu.mjs'); let view;
    try {
      view = createThreeScene({ THREE: gpuDependencies.THREE, GLTFLoader: dependencies.GLTFLoader, OrbitControls: dependencies.OrbitControls, canvas: $('gpu'), spec: sceneSpec, resolveAsset: await localAssetResolver(new URL('./graphics-demo-assets/', import.meta.url), sceneSpec.assets, lifetime.signal), signal: lifetime.signal, onTakeover: takeover, rendererFactory: options => new gpuDependencies.THREE.WebGPURenderer(options), width: renderWidth, height: renderHeight });
      await view.ready(lifetime.signal); if (!view.renderer.backend?.isWebGPUBackend) throw new GraphicsUnavailable('Requested WebGPU backend fell back; not qualified as WebGPU');
      const info = source => source ? Object.fromEntries(['vendor', 'architecture', 'device', 'description'].map(k => [k, source[k] ?? 'unavailable'])) : 'unavailable';
      return { view, particles: createParticleCloud(gpuDependencies.THREE, view.scene, particleSpec, { renderMode: 'meshes' }), info: { preflightAdapter: info(adapter.info), actualDevice: info(view.renderer.backend.device?.adapterInfo), preflightFallbackAdapter: adapter.isFallbackAdapter ?? 'unavailable', hardwareSoftwareQualification: 'Unknown unless independently established; masked vendor alone is insufficient' } };
    } catch (error) { view?.dispose(); throw error; }
  }, result => { result.particles.dispose(); result.view.dispose(); });
  const ready = await gpuResource.get(lifetime.signal); gpuView = ready.view; gpuParticles = ready.particles; if (gpuView.renderer.domElement.width !== renderWidth || gpuView.renderer.domElement.height !== renderHeight) gpuView.resize(renderWidth, renderHeight, 1); metrics.gpu = ready.info; return ready.view;
}
function fail(error) { pause(); metrics.currentStatus = 'failed'; metrics.error = String(error); if (error.renderReceipt) metrics.failedRender = error.renderReceipt; record(); status(error.message); }
function animate(now) { if (!playing) return; const next = Math.min(6, time + (now - previous) / 1000); previous = now; time = next; $('time').value = String(time); $('time-value').value = time.toFixed(3) + ' s'; const sample = simulation.seekTime(time); setPose(raster, sample); particles.sample(time); if (graph) graph.render(1 / 60); else raster.renderer.render(raster.scene, raster.camera); if (time >= 6) { pause(); record(); } else frame = requestAnimationFrame(animate); }
async function init() {
  const value = new URL(location.href).searchParams.get('profile'); if (!value) throw Error('Choose an explicitly prepared local profile using ?profile=/path/to/profile/; no dependency download is automatic.');
  profileURL = new URL(value.endsWith('/') ? value : value + '/', location.href); if (profileURL.origin !== location.origin || profileURL.username || profileURL.password) throw Error('Only same-origin local profiles are accepted');
  profile = await fetch(new URL('profile.json', profileURL), { signal: lifetime.signal }).then(r => { if (!r.ok) throw Error('Profile receipt missing'); return r.json(); });
  if (profile.version !== 1 || profile.status !== 'built; runtime qualification separate') throw Error('Unqualified local profile format');
  [dependencies, sceneSpec, simulationSpec] = await Promise.all([loadBundle('vendor-raster.mjs'), fetch(new URL('./graphics-scene.json', import.meta.url)).then(r => r.json()), fetch(new URL('./graphics-simulation.json', import.meta.url)).then(r => r.json())]);
  const { initJolt } = await loadBundle('vendor-jolt.mjs'), Jolt = await initJolt();
  simulation = createSimulation(simulationSpec, createJoltWorld(Jolt), { checkpointEvery: 120 });
  raster = createThreeScene({ ...dependencies, canvas: $('raster'), spec: sceneSpec, resolveAsset: await localAssetResolver(new URL('./graphics-demo-assets/', import.meta.url), sceneSpec.assets, lifetime.signal), signal: lifetime.signal, onTakeover: takeover, width: 960, height: 540, pixelRatio: Math.min(devicePixelRatio, 1.5) }); await raster.ready(lifetime.signal);
  raster.controls?.addEventListener('change', takeover); particles = createParticleCloud(dependencies.THREE, raster.scene, particleSpec, { renderMode: 'meshes' }); active = raster;
  const gl = raster.renderer.getContext(); metrics.gl = { version: gl.getParameter(gl.VERSION), renderer: gl.getParameter(gl.RENDERER), vendor: gl.getParameter(gl.VENDOR) }; metrics.profile = { lockSha256: profile.lockSha256, bytes: profile.totalBytes, dependencies: profile.dependencies };
  for (const identity of ['play', 'reset', 'time', 'mode', 'cancel', 'save', ...Object.keys(parameters)]) $(identity).disabled = false;
  $('time').oninput = () => render(Number($('time').value)).catch(fail);
  $('reset').onclick = () => render(0, $('mode').value, sceneSpec.camera).catch(fail);
  $('mode').onchange = () => render(time, $('mode').value).catch(fail);
  $('cancel').onclick = () => { pause(); generation++; tracer?.cancel(Error('Stopped by you')); metrics.currentStatus = 'cancelled'; record(); status('Render cancelled; the earlier view and failure receipt are retained.'); };
  $('play').onclick = () => { if (playing) pause(); else if (mode === 'pathtrace' || mode === 'webgpu') status('Progressive render uses explicit sampled frames. Select raster or effects for live playback.'); else { playing = true; previous = performance.now(); $('play').textContent = 'Pause'; frame = requestAnimationFrame(animate); } };
  for (const canvas of [$('raster'), $('gpu')]) canvas.addEventListener('click', event => { if (event.detail !== 1 || !active || metrics.currentStatus !== 'completed') return; const box = canvas.getBoundingClientRect(), hit = active.pick((event.clientX - box.left) / box.width * 2 - 1, -(event.clientY - box.top) / box.height * 2 + 1); $('selection').textContent = hit ? `Selected ${hit.partId} · source ${hit.sourceRevision} · point ${hit.point.map(n => n.toFixed(3)).join(', ')}` : 'No visible part selected.'; if (hit) { selectedPart = hit.partId; const target = $('graphics-review-target'); if (target && !target.disabled) { target.value = 'part/' + hit.partId; target.dispatchEvent(new Event('change')); } } metrics.selection = hit; record(); });
  for (const name of Object.keys(parameters)) $(name).oninput = () => { parameters[name] = name === 'ball-color' ? $(name).value : Number($(name).value); render(time, mode).catch(fail); };
  $('save').onclick = () => { pause(); const state = { version: 1, sourceRevision: sceneSpec.sourceRevision, time, mode, camera: { position: active.camera.position.toArray(), target: active.controls?.target.toArray() ?? sceneSpec.camera.target }, profileLockSha256: profile.lockSha256 }; const url = URL.createObjectURL(new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' })), a = document.createElement('a'); a.href = url; a.download = 'graphics-settings.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); status('Settings export requested; this does not establish a repository save.'); };
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); }, { signal: lifetime.signal });
  await render(0);
  const reviewAdapter = await mountGraphicsReview();
  // Trusted feature API for a local export adapter. JSON cannot supply its implementation.
  globalThis.orbynGraphics = {
    async applyReviewSettings(context) { if (!reviewAdapter) throw Error('A prepared graphics review profile is required to apply frozen settings'); await reviewAdapter.applyReviewSettings(context); },
    async resize(width, height) { if (!Number.isInteger(width) || !Number.isInteger(height) || width < 16 || height < 16 || width > 3840 || height > 3840 || width * height > 8294400) throw Error('Graphics export dimensions exceed the bounded envelope'); pause(); generation++; const old = tracer; tracer = null; if (old) await old.dispose(); graph?.dispose(); graph = null; renderWidth = width; renderHeight = height; raster.resize(width, height, 1); gpuView?.resize(width, height, 1); $('stage').style.aspectRatio = `${width}/${height}`; metrics.currentStatus = 'needs-render'; record(); return { width, height, pixelRatio: 1 }; },
    async renderFrame(frameIndex, fps = 30, selectedMode = 'raster') { if (!Number.isSafeInteger(frameIndex) || frameIndex < 0 || !Number.isFinite(fps) || fps <= 0 || fps > 240) throw Error('Invalid graphics output frame'); const requestedTime = frameIndex / fps; await render(requestedTime, selectedMode); if (metrics.currentStatus !== 'completed' || Math.abs(time - requestedTime) > 1e-8 || mode !== selectedMode) throw Error('Graphics output frame was superseded or cancelled'); return { sourceRevision: sceneSpec.sourceRevision, frameIndex, fps, width: active.renderer.domElement.width, height: active.renderer.domElement.height, metrics: structuredClone(metrics) }; },
    get state() { return { time, mode, metrics: structuredClone(metrics) }; }
  };
}
async function mountGraphicsReview() {
  const statusNode = $('graphics-review-status'), reviewURL = new URL('../api/review', import.meta.url), manifestURL = new URL('../manifest.json', import.meta.url);
  try {
    const response = await fetch(manifestURL, { cache: 'no-store', signal: lifetime.signal }); if (!response.ok) return;
    const manifest = await response.json(); if (manifest.prototype?.id !== 'graphics-review-v1') return;
    const { canonical, parseJSONStrict, fresh, validate, validateContext } = await import('../review-model.mjs');
    const capture = () => { if (metrics.currentStatus !== 'completed') throw Error('Wait for the current graphics frame before capturing a review context'); return { profile: 'graphics-v1', modelRevision: manifest.assets['motion/graphics-scene.json'], partId: selectedPart, camera: cameraContext(active), animation: { time, tick: Math.floor(time * simulationSpec.tickRate + 1e-8), scene: 'graphics-study', mode }, parameters: structuredClone(parameters), viewport: { width: Math.max(160, Math.round(innerWidth)), height: Math.max(160, Math.round(innerHeight)) } }; };
    await settledRender();
    let document = fresh(manifest, capture()), revision = 0, token = null, saving = false;
    const body = parseJSONStrict(await fetch(reviewURL, { cache: 'no-store', signal: lifetime.signal }).then(r => { if (!r.ok) throw Error('Repository bridge unavailable'); return r.text(); }));
    if (!Number.isInteger(body.revision) || typeof body.token !== 'string') throw Error('Invalid repository writer response'); revision = body.revision; token = body.token; if (body.review) document = validate(body.review, manifest);
    async function verifySource() { const now = parseJSONStrict(await fetch(manifestURL, { cache: 'no-store', signal: lifetime.signal }).then(r => r.text())); if (canonical(now) !== canonical(manifest)) throw Error('Source manifest changed; preserve this review and reload'); for (const [path, expected] of Object.entries(manifest.assets)) { const response = await fetch(new URL('../' + path, import.meta.url), { cache: 'no-store', signal: lifetime.signal }); if (!response.ok) throw Error('Source asset unavailable'); const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await response.arrayBuffer()))].map(x => x.toString(16).padStart(2, '0')).join(''); if (digest !== expected) throw Error('Source asset changed: ' + path); } }
    async function restore(context) { pause(); selectedPart = context.partId; Object.assign(parameters, context.parameters); for (const key of Object.keys(parameters)) $(key).value = String(parameters[key]); $('mode').value = context.animation.mode; await render(context.animation.time, context.animation.mode, context.camera); }
    function view() {
      synchronizeGraphicsAnchor($('graphics-review-target'), selectedPart, document.pending);
      const closed = document.state !== 'draft'; for (const key of ['target', 'text', 'post', 'submit']) $('graphics-review-' + key).disabled = closed || saving; $('graphics-review-save').disabled = saving;
      $('graphics-review-comments').replaceChildren();
      for (const comment of document.comments) { const li = globalThis.document.createElement('li'), text = globalThis.document.createElement('p'), button = globalThis.document.createElement('button'); text.textContent = `${comment.targetId} at ${comment.context.animation.time.toFixed(3)} s: ${comment.text} (${comment.disposition})`; button.textContent = 'Restore paused context'; button.onclick = () => { if (document.pending?.text.trim()) { statusNode.textContent = 'Post pending feedback before restoring another context.'; return; } document.pending = null; verifySource().then(() => restore(comment.context)).then(() => { view(); statusNode.textContent = 'Restored camera, materials, light, timeline and selected part; playback is paused.'; }).catch(error => { statusNode.textContent = error.message; }); }; li.append(text, button); $('graphics-review-comments').append(li); }
      $('graphics-review-text').value = document.pending?.text ?? ''; $('graphics-review-context').textContent = document.pending ? `Captured ${document.pending.targetId} at ${document.pending.context.animation.time.toFixed(3)} s; later view changes do not move this comment.` : `${document.state}: ${document.comments.length} feedback items. Settings save also works with zero comments.`;
    }
    for (const target of manifest.targets.filter(t => t.kind !== 'profile')) { const option = globalThis.document.createElement('option'); option.value = target.id; option.textContent = target.id; $('graphics-review-target').append(option); }
    function begin() { if (document.pending?.text.trim()) return; const targetId = $('graphics-review-target').value; if (targetId.startsWith('part/')) selectedPart = targetId.slice(5); pause(); document.pending = { targetId, context: capture(), text: '' }; validate(document, manifest); }
    $('graphics-review-target').onchange = () => { if (document.pending?.text.trim()) { $('graphics-review-target').value = document.pending.targetId; statusNode.textContent = 'Post pending feedback before changing its anchor.'; return; } try { begin(); view(); } catch (error) { statusNode.textContent = error.message; } };
    $('graphics-review-text').oninput = () => { try { if (!document.pending) begin(); document.pending.text = $('graphics-review-text').value; validate(document, manifest); } catch (error) { statusNode.textContent = error.message; } };
    $('graphics-review-post').onclick = () => { try { if (!document.pending?.text.trim()) throw Error('Choose an anchor and write feedback'); document.comments.push({ ...structuredClone(document.pending), id: crypto.randomUUID(), disposition: 'unresolved', decision: '' }); document.pending = null; validate(document, manifest); view(); statusNode.textContent = 'Feedback retained locally; save to repo for durable readback.'; } catch (error) { statusNode.textContent = error.message; } };
    async function save(submit = false) {
      if (saving) return; saving = true; pause();
      try { if (submit && document.pending?.text.trim()) throw Error('Post pending feedback before submission'); await settledRender(); if (document.state === 'draft') document.settings = capture(); if (submit) { document.pending = null; document.state = 'submitted'; } const snapshot = structuredClone(validate(document, manifest)); view(); await verifySource(); const response = await fetch(reviewURL, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Review-Token': token, 'X-Review-Revision': String(revision) }, body: JSON.stringify({ review: snapshot }), signal: lifetime.signal }); const result = parseJSONStrict(await response.text()); if (!response.ok) throw Error(result.error ?? 'Repository write rejected'); if (canonical(result.review) !== canonical(snapshot) || result.readback !== true) throw Error('Repository readback mismatch'); revision = result.revision; statusNode.textContent = `Graphics settings and feedback saved to repo and reread: revision ${revision}.`; }
      catch (error) { statusNode.textContent = `Not saved to repo: ${error.message}. Current feedback is retained locally.`; }
      finally { saving = false; view(); }
    }
    $('graphics-review-save').onclick = () => save(); $('graphics-review-submit').onclick = () => save(true);
    await verifySource(); await restore(document.settings); view(); statusNode.textContent = body.review ? `Reopened repository review revision ${revision}; camera, materials, time and feedback restored paused.` : 'Repository review ready. Save current settings even with zero comments.';
    return { async applyReviewSettings(context) { validateContext(context, manifest); await verifySource(); await restore(structuredClone(context)); view(); return capture(); } };
  } catch (error) { statusNode.textContent = `Repository review unavailable: ${error.message}. The code-driven preview remains usable.`; }
}
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
init().catch(error => { fail(error); $('raster').hidden = true; $('gpu').hidden = true; $('fallback').hidden = false; $('fallback').textContent = 'Graphics initialization is unavailable. The scene and physics input remain readable from the source links below. ' + error.message; });
window.addEventListener('pagehide', () => { pause(); generation++; lifetime.abort(Error('Preview closed')); const cleanup = () => { graph?.dispose(); particles?.dispose(); raster?.dispose(); gpuResource?.dispose(); }; tracer ? tracer.dispose().finally(cleanup) : cleanup(); simulation?.dispose(); }, { once: true });

}
