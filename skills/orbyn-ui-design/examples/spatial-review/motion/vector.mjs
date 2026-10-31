// Original code-authored vector/morph renderer. Saved geometry is inert data.
const NS = 'http://www.w3.org/2000/svg';
const arity = { M: 2, L: 2, Q: 4, C: 6, Z: 0 };
const keys = (value, required, optional = []) => {
  if (!value || typeof value !== 'object' || Array.isArray(value) || required.some(k => !Object.hasOwn(value, k)) || Object.keys(value).some(k => ![...required, ...optional].includes(k))) throw Error('Invalid vector fields');
};
const finite = (v, low = -1e6, high = 1e6) => {
  if (typeof v !== 'number' || !Number.isFinite(v) || v < low || v > high) throw Error('Invalid vector number');
  return v;
};
function path(commands) {
  if (!Array.isArray(commands) || !commands.length || commands.length > 1000 || commands[0]?.op !== 'M') throw Error('Path needs a bounded initial move');
  for (const c of commands) {
    keys(c, ['op', 'values']);
    if (!Object.hasOwn(arity, c.op) || !Array.isArray(c.values) || c.values.length !== arity[c.op]) throw Error('Unsupported vector command');
    c.values.forEach(v => finite(v));
  }
  return commands;
}
const color = value => { if (value !== 'none' && !/^#[\da-f]{6}$/i.test(value)) throw Error('Invalid vector color'); };
export function validateVector(spec) {
  keys(spec, ['version', 'width', 'height', 'shapes']);
  if (spec.version !== 1 || !Array.isArray(spec.shapes) || !spec.shapes.length || spec.shapes.length > 200) throw Error('Vector shape budget/version');
  finite(spec.width, 1, 10000); finite(spec.height, 1, 10000);
  const ids = new Set();
  for (const shape of spec.shapes) {
    keys(shape, ['id', 'from', 'fill', 'stroke', 'strokeWidth'], ['to', 'trim', 'fillRule']);
    if (typeof shape.id !== 'string' || !/^[a-z][\w.-]{0,79}$/i.test(shape.id) || ids.has(shape.id)) throw Error('Invalid/duplicate vector part');
    ids.add(shape.id); path(shape.from); color(shape.fill); color(shape.stroke); finite(shape.strokeWidth, 0, 100);
    if (Object.hasOwn(shape, 'to')) {
      path(shape.to);
      if (shape.from.length !== shape.to.length || shape.from.some((c, i) => c.op !== shape.to[i].op)) throw Error('Morph topology mismatch; author compatible paths');
    }
    if (Object.hasOwn(shape, 'trim') && typeof shape.trim !== 'boolean') throw Error('Invalid trim');
    if (Object.hasOwn(shape, 'fillRule') && !['nonzero', 'evenodd'].includes(shape.fillRule)) throw Error('Unsupported fill rule');
  }
  return spec;
}
export function sampleVector(spec, progress) {
  validateVector(spec); finite(progress, 0, 1);
  return {
    width: spec.width, height: spec.height,
    shapes: spec.shapes.map(s => ({
      id: s.id, fill: s.fill, stroke: s.stroke, strokeWidth: s.strokeWidth,
      fillRule: s.fillRule ?? 'nonzero', trim: s.trim ? progress : 1,
      commands: s.from.map((c, i) => ({ op: c.op, values: c.values.map((v, j) => v + ((s.to?.[i].values[j] ?? v) - v) * progress) })),
    })),
  };
}
export const pathData = commands => path(commands).map(c => c.op + c.values.join(' ')).join(' ');
export function drawVector(svg, state) {
  svg.setAttribute('viewBox', `0 0 ${state.width} ${state.height}`);
  const parts = state.shapes.map(s => {
    const el = svg.ownerDocument.createElementNS(NS, 'path');
    for (const [key, value] of Object.entries({ d: pathData(s.commands), fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth, 'fill-rule': s.fillRule, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'pointer-events': 'visiblePainted', pathLength: 1, 'stroke-dasharray': `${s.trim} 1`, 'data-part': s.id })) el.setAttribute(key, String(value));
    return el;
  });
  svg.replaceChildren(...parts);
}
export function vectorComponent() {
  return {
    dependencies: [],
    sample(clip) {
      const { vector, duration = 1, alt = 'Code-authored vector illustration' } = clip.props;
      finite(duration, 1e-6, 3600);
      if (typeof alt !== 'string' || alt.length > 500) throw Error('Invalid vector description');
      const progress = clip.reducedMotion ? 1 : Math.max(0, Math.min(1, clip.localTime / duration));
      return { ...sampleVector(vector, progress), id: clip.id, matrix: clip.worldMatrix, opacity: clip.opacity, zIndex: clip.zIndex, alt };
    },
    mount(host) {
      const svg = host.ownerDocument.createElementNS(NS, 'svg');
      svg.style.position = 'absolute'; svg.style.width = '100%'; svg.style.height = '100%'; svg.style.pointerEvents = 'none';
      svg.setAttribute('role', 'img'); host.append(svg); return svg;
    },
    update(svg, state) {
      drawVector(svg, state); svg.setAttribute('aria-label', state.alt); svg.dataset.component = state.id; svg.dataset.part = state.id;
      svg.style.transformOrigin = '0 0'; svg.style.transform = `matrix(${state.matrix.join(',')})`;
      svg.style.opacity = String(state.opacity); svg.style.zIndex = String(state.zIndex);
    },
    async ready(_svg, signal) { if (signal.aborted) throw Error('Cancelled vector'); },
    dispose(svg) { svg.remove(); },
  };
}

// A mathematical explainer can author geometry directly, without formula strings.
export function plotPath(fn, { from = 0, to = Math.PI * 2, samples = 120, x = 0, y = 0, scaleX = 50, scaleY = -50 } = {}) {
  if (typeof fn !== 'function' || !Number.isInteger(samples) || samples < 2 || samples > 1000 || !(to > from)) throw Error('Invalid trusted plot function/domain');
  [from, to, x, y, scaleX, scaleY].forEach(v => finite(v));
  return Array.from({ length: samples }, (_, i) => {
    const t = from + (to - from) * i / (samples - 1);
    return { op: i ? 'L' : 'M', values: [finite(x + t * scaleX), finite(y + finite(fn(t)) * scaleY)] };
  });
}
