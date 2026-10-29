// Conservative Orbyn check around an explicitly trusted view, not a TLC/compiler rewrite.
export function guardView(view) {
  const allowed = ['state', 'step', 'group', 'colors', 'title'];
  for (const key of Object.keys(view)) if (!allowed.includes(key)) throw new Error(`Unknown view export: ${key}`);
  if (view.step !== undefined && typeof view.step !== 'function') {
    throw new Error('View step must be a function');
  }
  const labels = new Map();
  const arrows = new Map();
  const key = value => JSON.stringify(value);
  const label = vars => {
    const id = key(vars);
    if (!labels.has(id)) labels.set(id, typeof view.state === 'function' ? view.state(vars) : id);
    return labels.get(id);
  };
  return { ...view,
    state: typeof view.state === 'function' ? label : view.state,
    step: (action, from, to) => {
      const answer = typeof view.step === 'function' ? view.step(action, from, to) : action;
      const left = label(from), right = label(to);
      if (key(left) !== key(right)) {
        // A null label erases its intended label. Reject ambiguous partial visibility
        // for the same action and displayed endpoints rather than guessing it safe.
        const arrow = key([action, left, right]);
        const hidden = answer === null;
        if (arrows.has(arrow) && arrows.get(arrow) !== hidden) {
          throw new Error(`Partial hidden arrow for ${action}: retain all instances or refine the view labels.`);
        }
        arrows.set(arrow, hidden);
      }
      return answer;
    },
  };
}
