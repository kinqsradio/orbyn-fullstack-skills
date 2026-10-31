// Original Orbyn effect graph and progressive-frame lifecycle; optional engines are injected.
import { GraphicsUnavailable } from './three.mjs';
const check = signal => { if (signal?.aborted) throw signal.reason ?? Error('Render cancelled'); };
const finite = (x, min, max, label) => { if (typeof x !== 'number' || !Number.isFinite(x) || x < min || x > max) throw Error('Invalid ' + label); return x; };

export function validateEffects(spec) {
  if (!spec || spec.version !== 1 || !Array.isArray(spec.effects) || spec.effects.length > 12) throw Error('Invalid effect graph');
  const ids = new Set();
  for (const effect of spec.effects) {
    if (!effect || typeof effect.id !== 'string' || !/^[a-z][\w-]{0,79}$/.test(effect.id) || ids.has(effect.id) || !['bloom', 'vignette', 'brightness-contrast', 'depth-of-field', 'tone-mapping'].includes(effect.type)) throw Error('Invalid/duplicate effect');
    ids.add(effect.id);
    if (effect.enabled !== undefined && typeof effect.enabled !== 'boolean') throw Error('Invalid effect enable flag');
    const allowed = effect.type === 'bloom' ? { intensity: [0, 5], luminanceThreshold: [0, 1], luminanceSmoothing: [0, 1] } : effect.type === 'vignette' ? { offset: [0, 1], darkness: [0, 1] } : effect.type === 'brightness-contrast' ? { brightness: [-1, 1], contrast: [-1, 1] } : effect.type === 'depth-of-field' ? { focusDistance: [0, 1], focalLength: [.001, 1], bokehScale: [0, 5] } : {};
    if (effect.options && (typeof effect.options !== 'object' || Array.isArray(effect.options))) throw Error('Invalid effect options');
    for (const [key, value] of Object.entries(effect.options ?? {})) { if (!Object.hasOwn(allowed, key)) throw Error('Unknown effect option'); finite(value, ...allowed[key], key); }
  }
  const tone = spec.effects.findIndex(e => e.type === 'tone-mapping');
  if (tone !== -1 && tone !== spec.effects.length - 1) throw Error('Tone mapping must be last');
  return spec;
}

export function createEffectGraph({ THREE, postprocessing: P, renderer, scene, camera, spec, width = 960, height = 540 }) {
  validateEffects(spec); if (!P?.EffectComposer || !THREE?.HalfFloatType || !renderer?.isWebGLRenderer) throw new GraphicsUnavailable('Postprocessing requires the qualified WebGL2 raster profile');
  const previousTone = renderer.toneMapping; renderer.toneMapping = THREE.NoToneMapping;
  const composer = new P.EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, multisampling: 0 });
  const effects = [], renderPass = new P.RenderPass(scene, camera); composer.addPass(renderPass); let disposed = false;
  try {
    for (const e of spec.effects.filter(e => e.enabled !== false)) {
      const options = { ...(e.options ?? {}) };
      const effect = e.type === 'bloom' ? new P.BloomEffect(options) : e.type === 'vignette' ? new P.VignetteEffect(options) : e.type === 'brightness-contrast' ? new P.BrightnessContrastEffect(options) : e.type === 'depth-of-field' ? new P.DepthOfFieldEffect(camera, options) : new P.ToneMappingEffect({ mode: P.ToneMappingMode.ACES_FILMIC });
      effects.push(effect);
    }
    if (effects.length) composer.addPass(new P.EffectPass(camera, ...effects));
    composer.setSize(width, height);
  } catch (error) { composer.dispose(); renderer.toneMapping = previousTone; throw error; }
  return { composer, effects,
    async ready(signal) { check(signal); if (disposed) throw Error('Effect graph disposed'); if (renderer.compileAsync) await renderer.compileAsync(scene, camera); check(signal); if (disposed) throw Error('Effect graph disposed'); },
    render(delta = 0) { if (disposed) throw Error('Effect graph disposed'); finite(delta, 0, 1, 'explicit effect delta'); composer.render(delta); },
    resize(w, h) { if (disposed) throw Error('Effect graph disposed'); finite(w, 1, 4096, 'effect width'); finite(h, 1, 4096, 'effect height'); composer.setSize(w, h); },
    dispose() { if (!disposed) { disposed = true; composer.dispose(); renderer.toneMapping = previousTone; } }
  };
}

function inspectScene(scene, maxTriangles) {
  let triangles = 0;
  scene.traverse(object => { if (object.isMesh && object.geometry) triangles += (object.geometry.index?.count ?? object.geometry.attributes.position?.count ?? 0) / 3; });
  if (triangles > maxTriangles) throw Error('Pathtracer scene exceeds triangle budget');
  return triangles;
}

export function createProgressiveRenderer({ PathTracer, renderer, scene, camera, backend = 'webgl', samples = 8, timeoutMs = 30000, maxTriangles = 250000, buildScene = (tracer, scene, camera) => tracer.setScene(scene, camera), yieldTask = () => new Promise(resolve => setTimeout(resolve, 0)) }) {
  if (typeof PathTracer !== 'function' || !['webgl', 'webgpu'].includes(backend) || (backend === 'webgpu' && !renderer?.isWebGPURenderer) || (backend === 'webgl' && !renderer?.isWebGLRenderer)) throw new GraphicsUnavailable('Requested pathtracer backend unavailable');
  if (!Number.isInteger(samples)) throw Error('Integer sample budget'); finite(samples, 1, 256, 'pathtrace samples'); finite(timeoutMs, 10, 300000, 'pathtrace deadline'); finite(maxTriangles, 1, 1000000, 'triangle budget');
  const tracer = new PathTracer(renderer); tracer.stableNoise = true;
  if (backend === 'webgl') { tracer.renderDelay = 0; tracer.fadeDuration = 0; tracer.minSamples = 1; tracer.dynamicLowRes = false; tracer.rasterizeScene = false; tracer.enablePathTracing = true; tracer.pausePathTracing = false; }
  else { tracer.maxSamples = samples; tracer.pause = false; tracer.renderDelay = 0; }
  let generation = 0, controller, tail = Promise.resolve(), disposed = false, loss = null, lastReceipt = null, disposal = null;
  const device = renderer.backend?.device;
  device?.lost?.then(info => { loss = Error('WebGPU device lost: ' + info.message); controller?.abort(loss); }).catch(error => { loss = error; controller?.abort(error); });
  const contextLost = event => { event.preventDefault(); loss = Error('Pathtracer WebGL context lost'); controller?.abort(loss); };
  renderer.domElement?.addEventListener?.('webglcontextlost', contextLost);
  function alive(own, signal) { check(signal); if (disposed || own !== generation) throw Error('Stale/disposed progressive frame'); if (loss) throw loss; }
  async function count() {
    if (backend === 'webgpu') { const measured = await tracer.getSampleCountsAsync(); return { min: measured.min, max: measured.max, avg: measured.avg }; }
    return { min: tracer.samples, max: tracer.samples, avg: tracer.samples };
  }
  return {
    tracer,
    renderFrame({ key, sample, signal }) {
      if (disposed || typeof key !== 'string' || !key || key.length > 300 || typeof sample !== 'function') return Promise.reject(Error('Invalid progressive frame request'));
      const own = ++generation; controller?.abort(Error('Superseded progressive frame')); const ownController = new AbortController(); controller = ownController;
      const externalAbort = () => ownController.abort(signal.reason ?? Error('Frame cancelled')); signal?.addEventListener('abort', externalAbort, { once: true }); if (signal?.aborted) externalAbort();
      const task = async () => {
        const started = performance.now(); const deadline = () => { alive(own, ownController.signal); if (performance.now() - started > timeoutMs) throw Error('Pathtracer frame deadline exceeded'); };
        let receipt = { key, backend, requestedSamples: samples, status: 'preparing', stableNoise: true };
        try {
          deadline(); await sample(); deadline(); receipt.triangles = inspectScene(scene, maxTriangles);
          // Rebuild each authored output pose. This is deliberately conservative:
          // transforms/materials/geometry cannot accidentally reuse the previous frame's BVH.
          // An exposed setSceneAsync method does not prove a local BVH worker is
          // installed. The bounded baseline builds synchronously. A trusted
          // profile with a bundled worker can explicitly replace buildScene.
          await buildScene(tracer, scene, camera);
          deadline(); tracer.reset(); receipt.status = 'sampling'; let measured = { min: 0, max: 0, avg: 0 }, rounds = 0;
          while (measured.min < samples) {
            deadline(); tracer.renderSample();
            if (device?.queue?.onSubmittedWorkDone) await device.queue.onSubmittedWorkDone();
            await yieldTask(); deadline(); measured = await count(); rounds++;
            if (!Number.isFinite(measured.min) || rounds > samples * 1024) throw Error('Pathtracer sample progress unavailable');
          }
          deadline(); receipt = { ...receipt, status: 'completed', measuredSamples: measured, rounds, elapsedMs: performance.now() - started }; lastReceipt = receipt; return receipt;
        } catch (error) { receipt = { ...receipt, status: ownController.signal.aborted ? 'cancelled' : 'failed', error: String(error), elapsedMs: performance.now() - started }; lastReceipt = receipt; throw Object.assign(error, { renderReceipt: receipt }); }
        finally { signal?.removeEventListener('abort', externalAbort); }
      };
      const job = tail.catch(() => {}).then(task); tail = job; return job;
    },
    cancel(reason = Error('Progressive render cancelled')) { generation++; controller?.abort(reason); },
    dispose() { if (!disposal) { disposed = true; generation++; controller?.abort(Error('Progressive renderer disposed')); disposal = (async () => { try { await tail; } catch {} renderer.domElement?.removeEventListener?.('webglcontextlost', contextLost); tracer.dispose(); })(); } return disposal; },
    get receipt() { return lastReceipt ? structuredClone(lastReceipt) : null; }
  };
}
