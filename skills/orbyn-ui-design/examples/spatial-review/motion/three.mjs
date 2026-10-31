// Original Orbyn scene adapter. Optional Three modules are trusted code dependencies.
// JSON supplies inert scene data only; it cannot name imports, scripts or shaders.
const finite = (x, label, lo = -1e5, hi = 1e5) => {
  if (typeof x !== 'number' || !Number.isFinite(x) || x < lo || x > hi) throw Error(`Invalid ${label}`);
  return x;
};
const identifier = x => typeof x === 'string' && /^[a-zA-Z][\w.-]{0,79}$/.test(x);
const vector = (v, label, fallback = [0, 0, 0]) => {
  const a = v ?? fallback;
  if (!Array.isArray(a) || a.length !== 3) throw Error(`Invalid ${label}`);
  return a.map(x => finite(x, label));
};
const check = signal => { if (signal?.aborted) throw signal.reason ?? Error('Graphics operation aborted'); };
function waitSignal(promise, signal) {
  check(signal); if (!signal) return promise;
  return new Promise((resolve, reject) => {
    const abort = () => { signal.removeEventListener('abort', abort); reject(signal.reason ?? Error('Graphics operation aborted')); };
    signal.addEventListener('abort', abort, { once: true });
    promise.then(value => { signal.removeEventListener('abort', abort); resolve(value); }, error => { signal.removeEventListener('abort', abort); reject(error); });
  });
}
const localPath = p => typeof p === 'string' && /^[\w./ -]{1,200}$/.test(p) && !p.startsWith('/') && !p.split('/').some(s => s === '..' || s === '.') && !p.includes('//');
const colours = c => typeof c === 'string' && /^#[\da-f]{6}$/i.test(c);
export class GraphicsUnavailable extends Error { constructor(message) { super(message); this.name = 'GraphicsUnavailable'; } }
export function synchronizeGraphicsAnchor(select, partId, pending) {
  const target = pending?.targetId ?? 'part/' + partId;
  if (![...select.options].some(option => option.value === target)) throw Error('Selected graphics review anchor is not mapped');
  select.value = target; return target;
}

// One owner creates a resource once. Concurrent waiters never receive the
// half-initialized handle; disposal also settles a late successful creation.
export function createAsyncResource(factory, dispose) {
  let flight = null, resource = null, disposed = false, released = false, disposal = null;
  async function release(value) { if (!released) { released = true; await dispose(value); } }
  return {
    get(signal) {
      if (disposed) return Promise.reject(Error('Async graphics resource disposed'));
      if (!flight) flight = Promise.resolve().then(factory).then(async value => { if (disposed) { await release(value); throw Error('Async graphics resource disposed during initialization'); } resource = value; return value; }).catch(error => { if (!disposed) flight = null; throw error; });
      return waitSignal(flight, signal);
    },
    dispose() { if (!disposal) { disposed = true; disposal = (async () => { if (flight) { try { await flight; } catch {} } if (resource) await release(resource); })(); } return disposal; }
  };
}

export function validateScene(spec) {
  if (!spec || spec.version !== 1 || typeof spec.sourceRevision !== 'string' || !spec.sourceRevision || spec.sourceRevision.length > 200 || !Array.isArray(spec.parts) || spec.parts.length > 256 || !spec.camera) throw Error('Invalid scene schema/budget');
  const ids = new Set();
  for (const part of spec.parts) {
    if (!identifier(part.id) || ids.has(part.id) || !['box', 'sphere', 'cylinder', 'plane', 'asset', 'custom'].includes(part.geometry?.type)) throw Error('Invalid/duplicate scene part');
    ids.add(part.id); vector(part.position, 'position'); vector(part.rotation, 'rotation'); vector(part.scale, 'scale', [1, 1, 1]);
    if (part.geometry.type === 'asset' && !localPath(part.geometry.path)) throw Error('Invalid local scene asset');
    for (const x of part.geometry.args ?? []) finite(x, 'geometry argument', .001, 1000);
    if (part.material && (typeof part.material !== 'object' || Array.isArray(part.material) || Object.keys(part.material).some(k => !['color', 'roughness', 'metalness', 'opacity', 'transparent', 'wireframe'].includes(k)))) throw Error('Invalid material fields');
    if (part.material?.color !== undefined && !colours(part.material.color)) throw Error('Invalid material colour');
    for (const k of ['transparent', 'wireframe']) if (part.material?.[k] !== undefined && typeof part.material[k] !== 'boolean') throw Error('Invalid material flag');
    for (const k of ['roughness', 'metalness', 'opacity']) if (part.material?.[k] !== undefined) finite(part.material[k], k, 0, 1);
    for (const track of part.motion ?? []) {
      if (!['position', 'rotation', 'scale'].includes(track.property)) throw Error('Invalid part motion property');
      vector(track.from, 'motion start'); vector(track.to, 'motion end'); finite(track.start, 'motion start time', 0, 3600); finite(track.end, 'motion end time', track.start + 1e-6, 3600);
    }
  }
  for (const p of spec.parts) if (p.parent && (!ids.has(p.parent) || p.parent === p.id)) throw Error('Invalid scene parent');
  const byId = new Map(spec.parts.map(p => [p.id, p]));
  for (const p of spec.parts) { const seen = new Set([p.id]); let parent = p.parent; while (parent) { if (seen.has(parent)) throw Error('Cyclic scene parent'); seen.add(parent); parent = byId.get(parent).parent; } }
  const assets = spec.assets ?? [];
  if (!Array.isArray(assets) || assets.length > 128 || new Set(assets.map(a => a.path)).size !== assets.length) throw Error('Invalid asset closure');
  for (const asset of assets) if (!localPath(asset.path) || !/^[\da-f]{64}$/.test(asset.sha256)) throw Error('Asset requires local path and SHA-256');
  for (const p of spec.parts) if (p.geometry.type === 'asset' && !assets.some(a => a.path === p.geometry.path)) throw Error('Missing asset closure entry');
  validateCamera(spec.camera); if (spec.background !== undefined && !colours(spec.background)) throw Error('Invalid background');
  if (!Array.isArray(spec.lights ?? []) || (spec.lights ?? []).length > 16) throw Error('Light budget');
  for (const light of spec.lights ?? []) { if (!['ambient', 'directional', 'point'].includes(light.type) || !colours(light.color)) throw Error('Invalid light'); finite(light.intensity, 'light intensity', 0, 100); vector(light.position, 'light position'); }
  return spec;
}
function validateCamera(c) {
  if (!['perspective', 'orthographic'].includes(c.type ?? 'perspective')) throw Error('Invalid camera type');
  vector(c.position, 'camera position', [5, 3, 6]); vector(c.target, 'camera target');
  finite(c.near ?? .1, 'camera near', .001, 100); finite(c.far ?? 1000, 'camera far', (c.near ?? .1) + .001, 1e6);
  finite(c.fov ?? 45, 'camera fov', 1, 150); finite(c.span ?? 8, 'orthographic span', .01, 1e4);
}

export function sampleScene(spec, time) {
  validateScene(spec); finite(time, 'scene time', 0, 3600);
  return { sourceRevision: spec.sourceRevision, time, camera: structuredClone(spec.camera), parts: spec.parts.map(p => {
    const result = { id: p.id, position: vector(p.position, 'position'), rotation: vector(p.rotation, 'rotation'), scale: vector(p.scale, 'scale', [1, 1, 1]) };
    for (const track of p.motion ?? []) { const t = Math.max(0, Math.min(1, (time - track.start) / (track.end - track.start))); result[track.property] = track.from.map((x, i) => x + (track.to[i] - x) * t); }
    return result;
  }) };
}

export async function localAssetResolver(root, declarations, signal) {
  const base = new URL(root, globalThis.location?.href);
  if (!['http:', 'https:', 'file:'].includes(base.protocol) || (base.protocol !== 'file:' && !['localhost', '127.0.0.1', '[::1]'].includes(base.hostname))) throw Error('Invalid local asset base');
  const allowed = new Map(declarations.map(a => [a.path, a]));
  return async path => {
    check(signal); const declaration = allowed.get(path); if (!declaration || !localPath(path)) throw Error('Asset outside declared closure');
    const url = new URL(path, base); if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) throw Error('Asset escapes local root');
    const response = await fetch(url, { signal, credentials: 'same-origin', redirect: 'error' });
    if (!response.ok || Number(response.headers.get('content-length') ?? 0) > 32 * 1024 * 1024) throw Error('Asset load failed/budget');
    const data = await response.arrayBuffer(); if (data.byteLength > 32 * 1024 * 1024) throw Error('Asset exceeds budget');
    const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))].map(x => x.toString(16).padStart(2, '0')).join('');
    if (sha256 !== declaration.sha256) throw Error('Scene asset digest mismatch');
    return { data, mimeType: response.headers.get('content-type') ?? 'application/octet-stream', sha256, path };
  };
}

function disposeObject(object) {
  const textures = new Set(), geometries = new Set(), materials = new Set();
  object.traverse(node => { if (node.geometry) geometries.add(node.geometry); for (const mat of Array.isArray(node.material) ? node.material : node.material ? [node.material] : []) { materials.add(mat); for (const value of Object.values(mat)) if (value?.isTexture) textures.add(value); } });
  textures.forEach(t => t.dispose()); materials.forEach(m => m.dispose()); geometries.forEach(g => g.dispose());
}

export function createThreeScene({ THREE, GLTFLoader, OrbitControls, canvas, spec, resolveAsset, signal, onTakeover = () => {}, rendererFactory, geometryFactories = {}, width = 960, height = 540, pixelRatio = 1 }) {
  validateScene(spec); spec = structuredClone(spec); check(signal); finite(width, 'width', 1, 4096); finite(height, 'height', 1, 4096); finite(pixelRatio, 'pixel ratio', .25, 2); if (!THREE?.Scene || !canvas) throw Error('Trusted Three module and canvas required');
  const scene = new THREE.Scene(), parts = new Map(), owned = new AbortController(), urls = new Set(); let disposed = false, lost = false, renderer, controls;
  const abort = () => owned.abort(signal?.reason ?? Error('Owner cancelled')); signal?.addEventListener('abort', abort, { once: true }); if (signal?.aborted) abort();
  scene.background = new THREE.Color(spec.background ?? '#edf1ea');
  const c = spec.camera; let cameraSpec = structuredClone(c), viewportWidth = width, viewportHeight = height;
  const camera = c.type === 'orthographic' ? new THREE.OrthographicCamera(-4, 4, 4, -4, c.near ?? .1, c.far ?? 1000) : new THREE.PerspectiveCamera(c.fov ?? 45, width / height, c.near ?? .1, c.far ?? 1000);
  const raycaster = new THREE.Raycaster(); const resources = [];
  try { renderer = rendererFactory ? rendererFactory({ canvas, alpha: false, antialias: true }) : new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false }); }
  catch (error) { signal?.removeEventListener('abort', abort); throw new GraphicsUnavailable('WebGL2 renderer unavailable: ' + error.message); }
  function alive() { if (disposed) throw Error('Three scene disposed'); check(owned.signal); if (lost) throw new GraphicsUnavailable('WebGL context lost'); }
  function setCamera(value) { alive(); const next = { ...cameraSpec, ...structuredClone(value) }; validateCamera(next); if ((next.type ?? 'perspective') !== (c.type ?? 'perspective')) throw Error('Camera type changes require a new scene owner'); cameraSpec = next; camera.position.fromArray(vector(next.position, 'camera position', [5, 3, 6])); camera.lookAt(...vector(next.target, 'camera target')); camera.near = next.near ?? .1; camera.far = next.far ?? 1000; if (camera.isPerspectiveCamera) camera.fov = next.fov ?? 45; else { const span = next.span ?? 8; camera.left = -span * viewportWidth / viewportHeight / 2; camera.right = span * viewportWidth / viewportHeight / 2; camera.top = span / 2; camera.bottom = -span / 2; } camera.updateProjectionMatrix(); if (controls) { controls.target.fromArray(vector(next.target, 'camera target')); controls.update(); } camera.updateMatrixWorld(true); }
  function resize(w, h, dpr = pixelRatio) { alive(); finite(w, 'width', 1, 4096); finite(h, 'height', 1, 4096); finite(dpr, 'pixel ratio', .25, 2); viewportWidth = w; viewportHeight = h; renderer.setPixelRatio(dpr); renderer.setSize(w, h, false); if (camera.isPerspectiveCamera) camera.aspect = w / h; else { const span = cameraSpec.span ?? 8; camera.left = -span * w / h / 2; camera.right = span * w / h / 2; camera.top = span / 2; camera.bottom = -span / 2; } camera.updateProjectionMatrix(); }
  const contextLost = event => { event.preventDefault(); lost = true; onTakeover({ reason: 'context-lost' }); };
  const takeover = () => onTakeover({ reason: 'orbit' });
  canvas.addEventListener?.('webglcontextlost', contextLost);
  if (OrbitControls) { controls = new OrbitControls(camera, canvas); controls.enableDamping = false; controls.addEventListener('start', takeover); }
  resize(width, height); setCamera(c);
  for (const l of spec.lights ?? [{ type: 'ambient', color: '#ffffff', intensity: 2 }]) { const C = l.type === 'ambient' ? THREE.AmbientLight : l.type === 'point' ? THREE.PointLight : THREE.DirectionalLight; const light = new C(l.color, l.intensity); light.position.fromArray(vector(l.position, 'light position', [3, 5, 4])); scene.add(light); }
  async function load() {
    try {
      const assets = new Map();
      if ((spec.assets ?? []).length && !resolveAsset) throw Error('Declared assets require a verified local resolver');
      for (const a of spec.assets ?? []) { check(owned.signal); const result = await resolveAsset(a.path, { signal: owned.signal }); check(owned.signal); if (!(result.data instanceof ArrayBuffer) || result.data.byteLength > 32 * 1024 * 1024) throw Error('Unverified/oversized asset result'); const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', result.data))].map(x => x.toString(16).padStart(2, '0')).join(''); if (digest !== a.sha256) throw Error('Scene asset digest mismatch'); assets.set(a.path, { ...result, sha256: digest }); }
      for (const p of spec.parts) {
        alive(); let object;
        if (p.geometry.type === 'asset') {
          if (!GLTFLoader) throw Error('Trusted local GLTFLoader missing');
          const manager = new THREE.LoadingManager();
          manager.setURLModifier(url => {
            if (url.startsWith('blob:')) return url; // GLTFLoader creates these from already verified embedded GLB images.
            const normal = url.replace(/^\.\//, ''); const asset = assets.get(normal);
            if (!asset) throw Error('glTF dependency outside declared local asset closure: ' + normal);
            const blob = URL.createObjectURL(new Blob([asset.data], { type: asset.mimeType })); urls.add(blob); return blob;
          });
          const asset = assets.get(p.geometry.path), loader = new GLTFLoader(manager);
          const text = /\.gltf$/i.test(p.geometry.path) ? new TextDecoder().decode(asset.data) : asset.data;
          const gltf = await loader.parseAsync(text, p.geometry.path.includes('/') ? p.geometry.path.slice(0, p.geometry.path.lastIndexOf('/') + 1) : '');
          object = gltf.scene; if (disposed || owned.signal.aborted) { disposeObject(object); check(owned.signal); throw Error('Scene disposed during asset load'); }
        } else {
          const geometry = p.geometry.type === 'custom' ? (Object.hasOwn(geometryFactories, p.geometry.factory) ? geometryFactories[p.geometry.factory](THREE, structuredClone(p.geometry.args ?? [])) : null) : p.geometry.type === 'box' ? new THREE.BoxGeometry(...(p.geometry.args ?? [1, 1, 1])) : p.geometry.type === 'sphere' ? new THREE.SphereGeometry(...(p.geometry.args ?? [.6, 24, 16])) : p.geometry.type === 'cylinder' ? new THREE.CylinderGeometry(...(p.geometry.args ?? [.5, .5, 1, 24])) : new THREE.PlaneGeometry(...(p.geometry.args ?? [1, 1]));
          if (!geometry?.isBufferGeometry) throw Error('Trusted geometry factory unavailable/invalid');
          const material = new THREE.MeshStandardMaterial({ color: '#d19b65', ...p.material }); object = new THREE.Mesh(geometry, material);
        }
        object.name = p.id; object.traverse(child => { child.userData.partId = p.id; child.userData.sourceRevision = spec.sourceRevision; }); parts.set(p.id, object); resources.push(object); scene.add(object);
      }
      for (const p of spec.parts) if (p.parent) parts.get(p.parent).add(parts.get(p.id));
      apply(0); if (renderer.compileAsync) await renderer.compileAsync(scene, camera); else renderer.compile?.(scene, camera); alive();
    } catch (error) { for (const object of resources) disposeObject(object); throw error; }
  }
  function apply(time, overrides = {}) { alive(); const state = sampleScene(spec, time); for (const p of state.parts) { const object = parts.get(p.id); if (!object) continue; const pose = overrides[p.id] ?? p; object.position.fromArray(pose.position ?? p.position); object.rotation.fromArray(pose.rotation ?? p.rotation); object.scale.fromArray(pose.scale ?? p.scale); if (pose.quaternion) object.quaternion.fromArray(pose.quaternion); } scene.updateMatrixWorld(true); return state; }
  const initialized = load(); initialized.catch(() => {});
  return {
    scene, camera, renderer, controls, parts,
    async ready(signal) { await waitSignal(initialized, signal); alive(); check(signal); },
    sample: apply,
    async render(time, overrides) { await initialized; alive(); const state = apply(time, overrides); renderer.render(scene, camera); return state; },
    pick(x, y) { alive(); finite(x, 'pick x', -1, 1); finite(y, 'pick y', -1, 1); scene.updateMatrixWorld(true); camera.updateMatrixWorld(true); raycaster.setFromCamera({ x, y }, camera); const hit = raycaster.intersectObjects([...parts.values()], true).find(h => h.object.userData.partId); return hit ? { partId: hit.object.userData.partId, sourceRevision: spec.sourceRevision, point: hit.point.toArray(), distance: hit.distance } : null; },
    setCamera, resize,
    dispose() { if (disposed) return; disposed = true; owned.abort(Error('Three scene disposed')); signal?.removeEventListener('abort', abort); canvas.removeEventListener?.('webglcontextlost', contextLost); controls?.removeEventListener('start', takeover); controls?.dispose(); for (const object of resources) disposeObject(object); scene.clear(); renderer.dispose(); for (const url of urls) URL.revokeObjectURL(url); urls.clear(); },
    get status() { return disposed ? 'disposed' : lost ? 'context-lost' : 'active'; }
  };
}

export function threeComponent(dependencies, sceneSpec, options = {}) {
  return { dependencies: ['three@0.186.1', ...((sceneSpec.assets ?? []).map(a => `${a.path}:${a.sha256}`))], sample: clip => ({ ...clip, sceneTime: clip.localTime }),
    mount(host, state) { const canvas = host.ownerDocument.createElement('canvas'); canvas.style.width = '100%'; canvas.style.height = '100%'; canvas.dataset.part = state.id; host.append(canvas); try { return { canvas, scene: createThreeScene({ ...dependencies, ...options, canvas, spec: sceneSpec }), time: state.sceneTime }; } catch (error) { canvas.remove(); throw error; } },
    update(handle, state) { handle.time = state.sceneTime; handle.canvas.style.opacity = String(state.opacity); handle.canvas.style.zIndex = String(state.zIndex); if (state.worldMatrix) handle.canvas.style.transform = `matrix(${state.worldMatrix.join(',')})`; },
    async ready(handle, signal) { await handle.scene.ready(signal); check(signal); await handle.scene.render(handle.time); check(signal); },
    dispose(handle) { handle.scene.dispose(); handle.canvas.remove(); }
  };
}
