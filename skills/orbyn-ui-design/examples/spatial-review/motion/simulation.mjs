// Original fixed-tick orchestration and seeded particles; optional Jolt is a pinned MIT dependency.
const clone = value => structuredClone(value);
const id = value => typeof value === 'string' && /^[a-zA-Z][\w.-]{0,79}$/.test(value);
const scalar = (x, lo, hi, name) => { if (typeof x !== 'number' || !Number.isFinite(x) || x < lo || x > hi) throw Error('Invalid ' + name); return x; };
const vec = (x, fallback = [0, 0, 0]) => { const a = x ?? fallback; if (!Array.isArray(a) || a.length !== 3) throw Error('Invalid vector'); return a.map(v => scalar(v, -1e5, 1e5, 'vector')); };
const check = signal => { if (signal?.aborted) throw signal.reason ?? Error('Simulation cancelled'); };

export function seededRandom(seed) {
  if (!Number.isSafeInteger(seed)) throw Error('Integer random seed required');
  let state = seed >>> 0;
  return () => { state = (state + 0x6D2B79F5) | 0; let t = Math.imul(state ^ state >>> 15, 1 | state); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

function bodySpec(body) {
  if (!body || !id(body.id) || !['box', 'sphere'].includes(body.shape?.type) || !['static', 'dynamic'].includes(body.motion ?? 'dynamic')) throw Error('Invalid simulation body');
  const result = clone(body); result.motion ??= 'dynamic'; result.position = vec(body.position); result.rotation = body.rotation ?? [0, 0, 0, 1];
  if (!Array.isArray(result.rotation) || result.rotation.length !== 4 || Math.abs(Math.hypot(...result.rotation) - 1) > 1e-4) throw Error('Unit body quaternion required');
  result.velocity = vec(body.velocity); result.angularVelocity = vec(body.angularVelocity);
  result.friction = scalar(body.friction ?? .3, 0, 1, 'friction'); result.restitution = scalar(body.restitution ?? .3, 0, 1, 'restitution');
  if (body.shape.type === 'sphere') scalar(body.shape.radius, .01, 100, 'sphere radius');
  else { result.shape.halfExtents = vec(body.shape.halfExtents); if (result.shape.halfExtents.some(x => x < .01 || x > 100)) throw Error('Invalid body extents'); }
  return result;
}

export function validateSimulation(spec) {
  if (!spec || spec.version !== 1 || typeof spec.sourceRevision !== 'string' || !spec.sourceRevision || !Number.isInteger(spec.tickRate) || spec.tickRate < 30 || spec.tickRate > 240 || !Number.isInteger(spec.maxTicks) || spec.maxTicks < 1 || spec.maxTicks > 30000 || !Array.isArray(spec.bodies) || spec.bodies.length > 128 || !Array.isArray(spec.events ?? []) || (spec.events ?? []).length > 1000) throw Error('Invalid simulation schema/budget');
  vec(spec.gravity, [0, -9.81, 0]); const live = new Set();
  for (const b of spec.bodies) { bodySpec(b); if (live.has(b.id)) throw Error('Duplicate initial body'); live.add(b.id); }
  let previous = -1;
  for (const event of spec.events ?? []) {
    if (!event || !Number.isInteger(event.tick) || event.tick < previous || event.tick < 0 || event.tick >= spec.maxTicks || !['add', 'remove', 'set', 'gravity', 'impulse'].includes(event.op)) throw Error('Invalid/nonordered simulation event');
    previous = event.tick;
    if (event.op === 'gravity') vec(event.value);
    else if (event.op === 'add') { bodySpec(event.body); if (live.has(event.body.id)) throw Error('Duplicate live body'); live.add(event.body.id); }
    else { if (!live.has(event.id)) throw Error('Event targets missing body'); if (event.op === 'remove') live.delete(event.id); else if (event.op === 'impulse') vec(event.value); else { if (!event.values || Object.keys(event.values).some(k => !['friction', 'restitution', 'velocity', 'angularVelocity', 'position'].includes(k))) throw Error('Unsupported external body mutation'); for (const [k, v] of Object.entries(event.values)) k === 'friction' || k === 'restitution' ? scalar(v, 0, 1, k) : vec(v); } }
    if (live.size > 128) throw Error('Live body budget');
  }
  return spec;
}

export function createJoltWorld(Jolt, { maxBodies = 128 } = {}) {
  if (!Jolt?.JoltInterface || !Jolt?.StateRecorderJS) throw Error('Prepared trusted Jolt module required');
  let jolt, physics, bodies, bodyInterface, disposed = false, gravity = [0, -9.81, 0];
  const destroy = object => { if (object) Jolt.destroy(object); };
  const read3 = object => { try { return [object.GetX(), object.GetY(), object.GetZ()]; } finally { destroy(object); } };
  const read4 = object => { try { return [object.GetX(), object.GetY(), object.GetZ(), object.GetW()]; } finally { destroy(object); } };
  const with3 = (values, fn, R = false) => { const v = R ? new Jolt.RVec3(...values) : new Jolt.Vec3(...values); try { return fn(v); } finally { destroy(v); } };
  function init() {
    const settings = new Jolt.JoltSettings(); settings.mMaxBodies = maxBodies; settings.mMaxBodyPairs = 2048; settings.mMaxContactConstraints = 2048; settings.mMaxWorkerThreads = 0;
    const pairs = new Jolt.ObjectLayerPairFilterTable(2); pairs.EnableCollision(0, 1); pairs.EnableCollision(1, 1);
    const broad = new Jolt.BroadPhaseLayerInterfaceTable(2, 2), a = new Jolt.BroadPhaseLayer(0), b = new Jolt.BroadPhaseLayer(1);
    broad.MapObjectToBroadPhaseLayer(0, a); broad.MapObjectToBroadPhaseLayer(1, b); destroy(a); destroy(b);
    settings.mObjectLayerPairFilter = pairs; settings.mBroadPhaseLayerInterface = broad; settings.mObjectVsBroadPhaseLayerFilter = new Jolt.ObjectVsBroadPhaseLayerFilterTable(broad, 2, pairs, 2);
    try { jolt = new Jolt.JoltInterface(settings); } finally { destroy(settings); }
    physics = jolt.GetPhysicsSystem(); bodyInterface = physics.GetBodyInterface(); bodies = new Map(); with3(gravity, v => physics.SetGravity(v));
  }
  function alive() { if (disposed) throw Error('Jolt world disposed'); }
  function remove(identity) { alive(); const entry = bodies.get(identity); if (!entry) throw Error('Missing body'); bodyInterface.RemoveBody(entry.body.GetID()); bodyInterface.DestroyBody(entry.body.GetID()); bodies.delete(identity); }
  function add(raw, engineId) {
    alive(); const definition = bodySpec(raw); if (bodies.has(definition.id) || bodies.size >= maxBodies) throw Error('Duplicate/body budget');
    let shape, extents, position, rotation, settings, engineIdentity;
    try {
      if (definition.shape.type === 'box') { extents = new Jolt.Vec3(...definition.shape.halfExtents); shape = new Jolt.BoxShape(extents, Math.min(.05, ...definition.shape.halfExtents) / 2); }
      else shape = new Jolt.SphereShape(definition.shape.radius);
      position = new Jolt.RVec3(...definition.position); rotation = new Jolt.Quat(...definition.rotation);
      settings = new Jolt.BodyCreationSettings(shape, position, rotation, definition.motion === 'static' ? Jolt.EMotionType_Static : Jolt.EMotionType_Dynamic, definition.motion === 'static' ? 0 : 1);
      settings.mFriction = definition.friction; settings.mRestitution = definition.restitution;
      let body;
      if (engineId === undefined) body = bodyInterface.CreateBody(settings);
      else { engineIdentity = new Jolt.BodyID(engineId); body = bodyInterface.CreateBodyWithID(engineIdentity, settings); }
      if (!body || !Jolt.getPointer(body)) throw Error('Jolt body allocation failed');
      bodyInterface.AddBody(body.GetID(), Jolt.EActivation_Activate); bodies.set(definition.id, { body, definition });
      if (definition.motion === 'dynamic') { with3(definition.velocity, v => bodyInterface.SetLinearVelocity(body.GetID(), v)); with3(definition.angularVelocity, v => bodyInterface.SetAngularVelocity(body.GetID(), v)); }
    } finally { destroy(engineIdentity); destroy(settings); destroy(position); destroy(rotation); destroy(extents); }
  }
  function mutate(identity, values) {
    alive(); const e = bodies.get(identity); if (!e) throw Error('Missing body');
    for (const [key, value] of Object.entries(values)) {
      if (key === 'friction' || key === 'restitution') { scalar(value, 0, 1, key); bodyInterface[key === 'friction' ? 'SetFriction' : 'SetRestitution'](e.body.GetID(), value); }
      else if (key === 'velocity' || key === 'angularVelocity') with3(vec(value), v => bodyInterface[key === 'velocity' ? 'SetLinearVelocity' : 'SetAngularVelocity'](e.body.GetID(), v));
      else if (key === 'position') with3(vec(value), v => bodyInterface.SetPosition(e.body.GetID(), v, Jolt.EActivation_Activate), true);
      else throw Error('Unsupported Jolt mutation');
      e.definition[key] = clone(value);
    }
  }
  function poses() { alive(); return [...bodies].map(([identity, e]) => ({ id: identity, position: read3(e.body.GetPosition()), quaternion: read4(e.body.GetRotation()), velocity: read3(e.body.GetLinearVelocity()), angularVelocity: read3(e.body.GetAngularVelocity()), friction: e.body.GetFriction(), restitution: e.body.GetRestitution() })).sort((a, b) => a.id.localeCompare(b.id)); }
  function record(readBytes) {
    const recorder = new Jolt.StateRecorderJS(); let cursor = 0, failed = false; const chunks = [];
    recorder.WriteBytes = (ptr, length) => { if (length < 0 || chunks.reduce((sum, c) => sum + c.length, 0) + length > 8 * 1024 * 1024) throw Error('Physics checkpoint exceeds budget'); chunks.push(Jolt.HEAPU8.slice(ptr, ptr + length)); };
    recorder.ReadBytes = (ptr, length) => { if (!readBytes || cursor + length > readBytes.length) { failed = true; throw Error('Truncated physics checkpoint'); } Jolt.HEAPU8.set(readBytes.subarray(cursor, cursor + length), ptr); cursor += length; };
    recorder.IsEOF = () => !readBytes || cursor >= readBytes.length; recorder.IsFailed = () => failed;
    return { recorder, chunks };
  }
  function snapshot() {
    alive(); const { recorder, chunks } = record(); try { physics.SaveState(recorder); } finally { destroy(recorder); }
    const bytes = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0)); let cursor = 0; for (const c of chunks) { bytes.set(c, cursor); cursor += c.length; }
    return { version: 1, profile: 'jolt-physics@1.1.1/wasm-compat/single-thread', gravity: clone(gravity), bodies: [...bodies].map(([, e]) => ({ definition: clone(e.definition), engineId: e.body.GetID().GetIndexAndSequenceNumber() })), engineState: [...bytes] };
  }
  function restore(value) {
    alive(); if (!value || value.version !== 1 || value.profile !== 'jolt-physics@1.1.1/wasm-compat/single-thread' || !Array.isArray(value.bodies) || value.bodies.length > maxBodies || !Array.isArray(value.engineState) || value.engineState.length > 8 * 1024 * 1024 || value.engineState.some(x => !Number.isInteger(x) || x < 0 || x > 255)) throw Error('Incompatible physics checkpoint');
    const ids = new Set(), engineIds = new Set();
    for (const entry of value.bodies) { bodySpec(entry.definition); if (!Number.isInteger(entry.engineId) || entry.engineId < 0 || entry.engineId > 0xffffffff || (entry.engineId & 0x7fffff) >= maxBodies || ids.has(entry.definition.id) || engineIds.has(entry.engineId)) throw Error('Invalid checkpoint identity'); ids.add(entry.definition.id); engineIds.add(entry.engineId); }
    destroy(jolt); gravity = vec(value.gravity); init();
    for (const entry of value.bodies) add(entry.definition, entry.engineId);
    const { recorder } = record(Uint8Array.from(value.engineState)); try { if (!physics.RestoreState(recorder)) throw Error('Physics state restore refused'); } finally { destroy(recorder); }
  }
  init();
  return { add, remove, set: mutate, poses, snapshot, restore,
    setGravity(value) { alive(); gravity = vec(value); with3(gravity, v => physics.SetGravity(v)); },
    impulse(identity, value) { alive(); const e = bodies.get(identity); if (!e) throw Error('Missing body'); with3(vec(value), v => bodyInterface.AddImpulse(e.body.GetID(), v)); },
    step(delta) { alive(); scalar(delta, 1 / 1000, .1, 'physics tick'); jolt.Step(delta, 1); },
    dispose() { if (disposed) return; disposed = true; destroy(jolt); bodies.clear(); },
    get size() { return bodies.size; }
  };
}

export function createSimulation(spec, world, { checkpointEvery = 120, checkpointLimit = 16 } = {}) {
  validateSimulation(spec); spec = clone(spec); if (!Number.isInteger(checkpointEvery) || checkpointEvery < 1 || !Number.isInteger(checkpointLimit) || checkpointLimit < 2 || checkpointLimit > 64) throw Error('Checkpoint budget');
  let tick = 0, cursor = 0, disposed = false; const checkpoints = new Map();
  world.setGravity(vec(spec.gravity, [0, -9.81, 0])); for (const body of spec.bodies) world.add(body);
  checkpoints.set(0, { state: world.snapshot(), cursor: 0 });
  function advance(event) { if (event.op === 'add') world.add(event.body); else if (event.op === 'remove') world.remove(event.id); else if (event.op === 'set') world.set(event.id, event.values); else if (event.op === 'gravity') world.setGravity(event.value); else world.impulse(event.id, event.value); }
  return {
    seek(targetTick, { signal } = {}) {
      if (disposed || !Number.isInteger(targetTick) || targetTick < 0 || targetTick > spec.maxTicks) throw Error('Invalid/disposed simulation seek'); check(signal);
      if (targetTick < tick) { const start = Math.max(...[...checkpoints.keys()].filter(n => n <= targetTick)); const checkpoint = checkpoints.get(start); world.restore(clone(checkpoint.state)); cursor = checkpoint.cursor; tick = start; }
      for (; tick < targetTick;) { check(signal); while (cursor < (spec.events ?? []).length && spec.events[cursor].tick === tick) advance(spec.events[cursor++]); world.step(1 / spec.tickRate); tick++; if (tick % checkpointEvery === 0 && !checkpoints.has(tick)) { checkpoints.set(tick, { state: world.snapshot(), cursor }); if (checkpoints.size > checkpointLimit) checkpoints.delete([...checkpoints.keys()].find(n => n !== 0)); } }
      return { sourceRevision: spec.sourceRevision, tick, time: tick / spec.tickRate, bodies: world.poses() };
    },
    seekTime(time, options) { scalar(time, 0, spec.maxTicks / spec.tickRate, 'simulation time'); return this.seek(Math.floor(time * spec.tickRate + 1e-8), options); },
    checkpoint() { if (disposed) throw Error('Simulation disposed'); return { version: 1, sourceRevision: spec.sourceRevision, tickRate: spec.tickRate, tick, cursor, state: world.snapshot() }; },
    restore(checkpoint) { if (disposed || checkpoint?.version !== 1 || checkpoint.sourceRevision !== spec.sourceRevision || checkpoint.tickRate !== spec.tickRate || !Number.isInteger(checkpoint.tick) || checkpoint.tick < 0 || checkpoint.tick > spec.maxTicks || !Number.isInteger(checkpoint.cursor) || checkpoint.cursor < 0 || checkpoint.cursor > (spec.events ?? []).length) throw Error('Incompatible simulation checkpoint'); world.restore(clone(checkpoint.state)); tick = checkpoint.tick; cursor = checkpoint.cursor; },
    dispose() { if (!disposed) { disposed = true; checkpoints.clear(); world.dispose(); } }
  };
}

export function sampleParticles(spec, time) {
  if (!spec || !Number.isInteger(spec.seed) || !Number.isInteger(spec.capacity) || spec.capacity < 1 || spec.capacity > 10000) throw Error('Invalid particle specification');
  scalar(time, 0, 3600, 'particle time'); const start = scalar(spec.start ?? 0, 0, 3600, 'emission start'), duration = scalar(spec.duration, .01, 120, 'emission duration'), rate = scalar(spec.rate, .1, 10000, 'emission rate'), life = scalar(spec.life, .01, 120, 'particle life');
  const origin = vec(spec.origin), velocity = vec(spec.velocity, [0, 3, 0]), gravity = vec(spec.gravity, [0, -9.81, 0]), spread = scalar(spec.spread ?? 1, 0, 100, 'spread');
  const end = Math.min(Math.ceil(duration * rate), Math.floor(Math.max(0, time - start) * rate) + 1), first = Math.max(0, Math.floor((time - start - life) * rate) + 1); const particles = [];
  if (time < start) return particles;
  for (let index = Math.max(first, end - spec.capacity); index < end; index++) { const age = time - start - index / rate; if (age < 0 || age >= life) continue; const random = seededRandom((spec.seed ^ Math.imul(index + 1, 2654435761)) >>> 0), v = velocity.map(x => x + (random() * 2 - 1) * spread); particles.push({ id: `particle-${index}`, age, opacity: 1 - age / life, position: origin.map((x, i) => x + v[i] * age + .5 * gravity[i] * age * age) }); }
  return particles;
}

export function createParticleCloud(THREE, scene, spec, { color = '#dda35b', size = .07, renderMode = 'points' } = {}) {
  sampleParticles(spec, 0); if (!['points', 'meshes'].includes(renderMode)) throw Error('Invalid particle rendering mode');
  if (renderMode === 'meshes') {
    const object = new THREE.Group(), geometry = new THREE.SphereGeometry(size / 2, 6, 4), materials = [], meshes = [];
    for (let i = 0; i < spec.capacity; i++) { const material = new THREE.MeshStandardMaterial({ color, transparent: true, roughness: .6, depthWrite: false }), mesh = new THREE.Mesh(geometry, material); mesh.visible = false; materials.push(material); meshes.push(mesh); object.add(mesh); }
    scene.add(object); let disposed = false;
    return { object, sample(time) { if (disposed) throw Error('Particle cloud disposed'); const points = sampleParticles(spec, time); meshes.forEach((mesh, index) => { const p = points[index]; mesh.visible = Boolean(p); if (p) { mesh.position.fromArray(p.position); mesh.material.opacity = p.opacity; mesh.userData.particleId = p.id; } }); object.updateMatrixWorld(true); return points; }, dispose() { if (!disposed) { disposed = true; scene.remove(object); geometry.dispose(); materials.forEach(m => m.dispose()); } } };
  }
  const geometry = new THREE.BufferGeometry(), positions = new Float32Array(spec.capacity * 3); geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3)); const material = new THREE.PointsMaterial({ color, size, transparent: true, depthWrite: false }); const object = new THREE.Points(geometry, material); scene.add(object); let disposed = false;
  return { object, sample(time) { if (disposed) throw Error('Particle cloud disposed'); const points = sampleParticles(spec, time); points.forEach((p, i) => positions.set(p.position, i * 3)); geometry.setDrawRange(0, points.length); geometry.attributes.position.needsUpdate = true; geometry.computeBoundingSphere(); return points; }, dispose() { if (!disposed) { disposed = true; scene.remove(object); geometry.dispose(); material.dispose(); } } };
}
