// Inspection of the captured page. inspectPage runs in the browser; motionOnly runs in Node and
// decides what may be written for someone else's page.

const STYLE_PROPS = ['opacity', 'transform', 'transition', 'animation', 'will-change', 'color', 'background-color', 'background-image', 'font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing', 'border-radius', 'box-shadow', 'filter', 'backdrop-filter', 'clip-path', 'overflow', 'position', 'display', 'gap', 'padding', 'mask-image'];
const EMPTY_VALUES = ['none', 'normal', 'auto', 'static', 'visible', '0px', 'all', 'all 0s ease 0s', 'rgba(0, 0, 0, 0)'];

/** Runs after the motion, so getAnimations() has seen everything that still has an effect. */
export function inspectPage({ selector, styleProps, emptyValues }) {
  const describe = (el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : '') + (el.classList.length ? `.${[...el.classList].slice(0, 4).join('.')}` : '');
  const root = selector ? document.querySelector(selector) : document.body;
  const box = (r) => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  const canvases = [...document.querySelectorAll('canvas')].map((c) => ({ el: describe(c), size: [c.width, c.height], css: box(c.getBoundingClientRect()) }));
  const keyframes = [];
  for (const sheet of document.styleSheets) {
    let rules;
    try { rules = sheet.cssRules; } catch { keyframes.push({ unreadable: sheet.href }); continue; }
    const walk = (list) => { for (const rule of list) { if (rule.type === 7) keyframes.push({ name: rule.name, css: rule.cssText }); else if (rule.cssRules) walk(rule.cssRules); } };
    walk(rules);
  }
  const animations = (root ? root.getAnimations({ subtree: true }) : document.getAnimations()).slice(0, 200).map((animation) => {
    const effect = animation.effect;
    const target = effect && effect.target;
    let frames = [];
    try {
      frames = effect.getKeyframes().slice(0, 24).map((frame) => {
        const copy = {};
        for (const [name, value] of Object.entries(frame)) if (name !== 'computedOffset' && name !== 'composite') copy[name] = value;
        return copy;
      });
    } catch {}
    return {
      kind: animation.constructor.name, name: animation.animationName || animation.transitionProperty || animation.id || '',
      target: target ? describe(target) : null, timing: effect ? effect.getTiming() : null, keyframes: frames, playState: animation.playState,
    };
  });
  const nodes = [];
  if (root) {
    for (const el of [root, ...root.querySelectorAll('*')].slice(0, 150)) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const computed = getComputedStyle(el);
      const style = {};
      for (const prop of styleProps) {
        const value = computed.getPropertyValue(prop);
        if (value && !emptyValues.includes(value) && !(prop === 'opacity' && value === '1') && !(prop === 'transform' && value === 'matrix(1, 0, 0, 1, 0, 0)')) style[prop] = value;
      }
      nodes.push({ el: describe(el), rect: box(r), text: el.childElementCount === 0 ? (el.textContent || '').trim().slice(0, 60) : undefined, style, src: el.currentSrc || el.src || undefined });
    }
  }
  const rect = root ? root.getBoundingClientRect() : null;
  return {
    url: location.href, viewport: [innerWidth, innerHeight], scrollY, devicePixelRatio, canvases,
    fonts: [...new Set([...document.fonts].filter((font) => font.status === 'loaded').map((font) => `${font.family.replace(/"/g, '')} ${font.weight} ${font.style}`))],
    target: selector ? { selector, found: !!root, rect: rect && box(rect) } : null,
    animations, keyframes, nodes,
  };
}

export const inspectArgument = (selector) => ({ selector: selector ?? null, styleProps: STYLE_PROPS, emptyValues: EMPTY_VALUES });

const NUMBER = '[-+]?(?:\\d+\\.?\\d*|\\.\\d+)(?:e[-+]?\\d+)?(?:%|px|deg|rad|turn|em|rem|vh|vw)?';
const NUMBERS = `${NUMBER}(?:[\\s,]+${NUMBER})*`;
const EASING = /^(?:linear|ease(?:-in|-out|-in-out)?|step-(?:start|end)|cubic-bezier\([-\d.,\s]+\)|steps\(\d+(?:,\s*[a-z-]+)?\)|linear\([-\d.,%\s]+\))$/;
const TRANSFORM = new RegExp(`^(?:none|(?:(?:matrix3d|matrix|translate3d|translate[XYZ]?|scale3d|scale[XYZ]?|rotate3d|rotate[XYZ]?|skew[XY]?|perspective)\\(${NUMBERS}\\)\\s*)+)$`, 'i');
const LENGTHS = new RegExp(`^(?:none|${NUMBERS})$`, 'i');
const KINDS = ['Animation', 'CSSAnimation', 'CSSTransition'];
const STATES = ['idle', 'pending', 'running', 'paused', 'finished'];
const FILLS = ['none', 'forwards', 'backwards', 'both', 'auto'];
const DIRECTIONS = ['normal', 'reverse', 'alternate', 'alternate-reverse'];

const number = (value) => (typeof value === 'number' && Number.isFinite(value) ? value : undefined);
const matches = (pattern) => (value) => (typeof value === 'string' && value.length < 300 && pattern.test(value) ? value : undefined);
const among = (names) => (value) => (names.includes(value) ? value : undefined);

const TIMING_FIELDS = {
  delay: number, endDelay: number, iterations: number, duration: (value) => (value === 'auto' ? value : number(value)),
  easing: matches(EASING), fill: among(FILLS), direction: among(DIRECTIONS),
};
const FRAME_FIELDS = {
  offset: (value) => (value === null ? null : number(value)), easing: matches(EASING), opacity: (value) => number(value) ?? matches(LENGTHS)(value),
  transform: matches(TRANSFORM), translate: matches(LENGTHS), scale: matches(LENGTHS), rotate: matches(LENGTHS),
};

/** Keep a field only when its value has the right shape: the page can write these values. */
function checked(source, fields) {
  const kept = {};
  for (const [name, check] of Object.entries(fields)) {
    const value = check(source?.[name]);
    if (value !== undefined) kept[name] = value;
  }
  return kept;
}

const numbers = (list) => (Array.isArray(list) ? list.map(number).filter((value) => value !== undefined) : []);

/**
 * The written record for someone else's page: timing, easing, order and distance. Both names and
 * values are allowlisted, so text, fonts, colours, class names, sources and stylesheet code are
 * never written, and a field added to inspectPage later stays out until it is added here.
 */
export function motionOnly(raw) {
  return {
    scope: 'motion-only: timing, easing, order and distance',
    viewport: numbers(raw.viewport),
    target: raw.target ? { found: raw.target.found === true, rect: numbers(raw.target.rect) } : null,
    animations: (Array.isArray(raw.animations) ? raw.animations : []).map((animation, index) => ({
      index,
      kind: among(KINDS)(animation?.kind) ?? 'Animation',
      timing: checked(animation?.timing, TIMING_FIELDS),
      keyframes: (Array.isArray(animation?.keyframes) ? animation.keyframes : []).map((frame) => checked(frame, FRAME_FIELDS)),
      playState: among(STATES)(animation?.playState) ?? 'idle',
    })),
  };
}

/** Track samples are read back from the page, so only finite numbers and matrices survive. */
export function cleanSamples(samples, selectors) {
  const box = (element) => {
    if (!element || typeof element !== 'object') return null;
    const kept = {};
    for (const name of ['x', 'y', 'w', 'h', 'opacity']) kept[name] = number(element[name]) ?? 0;
    kept.transform = matches(TRANSFORM)(element.transform) ?? 'none';
    return kept;
  };
  return (Array.isArray(samples) ? samples : []).filter((sample) => number(sample?.t) !== undefined).map((sample) => ({
    t: sample.t, scrollY: number(sample.scrollY) ?? 0, els: Object.fromEntries(selectors.map((selector) => [selector, box(sample.els?.[selector])])),
  }));
}
