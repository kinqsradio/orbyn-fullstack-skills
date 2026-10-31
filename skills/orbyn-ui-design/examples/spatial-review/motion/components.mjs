import {sampleComposition, validateComposition, inert} from './composition.mjs';

// This registry is authored source. Inert project files cannot import components.
export function createRegistry() {
  const entries = new Map();
  return {
    register(id, component) {
      const methods = ['sample', 'mount', 'update', 'ready', 'dispose'];
      if (!/^[a-z][a-z0-9-]{0,79}$/.test(id) || entries.has(id) || !component ||
          methods.some(k => typeof component[k] !== 'function') || !Array.isArray(component.dependencies)) {
        throw Error('Invalid/duplicate trusted component');
      }
      inert(component.dependencies);
      entries.set(id, component);
      return this;
    },
    get(id) {
      if (!entries.has(id)) throw Error('Unregistered component ' + id);
      return entries.get(id);
    },
    ids: () => [...entries.keys()]
  };
}

function untilReady(job, signal) {
  return new Promise((resolve, reject) => {
    const abort = () => reject(Error('Stale/cancelled frame'));
    if (signal.aborted) return abort();
    signal.addEventListener('abort', abort, {once: true});
    Promise.resolve(job).then(resolve, reject).finally(() => signal.removeEventListener('abort', abort));
  });
}

export function createPlayer(host, spec, registry) {
  validateComposition(spec);
  const handles = new Map();
  let generation = 0, controller = null, disposed = false;
  let lifecycle = Promise.resolve(), disposal = null;
  for (const c of spec.clips) registry.get(c.component);
  async function remove(id) {
    const entry = handles.get(id);
    if (entry) {
      handles.delete(id);
      await entry.component.dispose(entry.handle);
    }
  }
  // Serialize mount/unmount ownership, not readiness. A new seek aborts old
  // readiness immediately while awaiting any genuinely asynchronous GPU teardown.
  function serialize(operation) {
    const result = lifecycle.then(operation);
    lifecycle = result.catch(() => {});
    return result;
  }
  return {
    async seek(frame, options = {}) {
      if (disposed) throw Error('Player disposed');
      const version = ++generation;
      controller?.abort();
      const ownController = new AbortController();
      controller = ownController;
      const current = () => {
        if (disposed || version !== generation || ownController.signal.aborted) throw Error('Stale/cancelled frame');
      };
      const snapshot = sampleComposition(spec, frame, options);
      const jobs = await serialize(async () => {
        current();
        const live = new Set(snapshot.active.map(c => c.id));
        for (const id of handles.keys()) if (!live.has(id)) await remove(id);
        current();
        const waiting = [];
        for (const clip of snapshot.active) {
          const component = registry.get(clip.component);
          const state = component.sample(structuredClone(clip));
          inert(state);
          let entry = handles.get(clip.id);
          if (!entry) {
            entry = {component, handle: component.mount(host, state)};
            handles.set(clip.id, entry);
          }
          component.update(entry.handle, state);
          // Attach rejection handling immediately, including when another
          // component fails synchronously during this same preparation pass.
          const ready = untilReady(component.ready(entry.handle, ownController.signal), ownController.signal);
          ready.catch(() => {});
          waiting.push(ready);
        }
        return waiting;
      });
      await Promise.all(jobs);
      current();
      return snapshot;
    },
    dispose() {
      if (disposal) return disposal;
      disposed = true;
      generation++;
      controller?.abort();
      disposal = serialize(async () => {
        const failures = [];
        for (const id of [...handles.keys()]) {
          try { await remove(id); } catch (error) { failures.push(error); }
        }
        if (failures.length) throw new AggregateError(failures, 'Component disposal failed');
      });
      return disposal;
    },
    get generation() { return generation; }
  };
}

export function domTextComponent() {
  return {
    dependencies: [],
    sample: clip => ({...clip, text: String(clip.props.text ?? clip.id)}),
    mount(host) {
      const el = host.ownerDocument.createElement('div');
      el.style.position = 'absolute';
      host.append(el);
      return el;
    },
    update(el, state) {
      el.textContent = state.text;
      el.dataset.part = state.id;
      el.style.transform = `matrix(${state.worldMatrix.join(',')})`;
      el.style.opacity = String(state.opacity);
      el.style.zIndex = String(state.zIndex);
    },
    async ready(_el, signal) { if (signal.aborted) throw Error('Aborted'); },
    dispose: el => el.remove()
  };
}
