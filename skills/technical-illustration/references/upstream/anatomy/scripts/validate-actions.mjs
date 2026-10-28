// Validate the entire declared action list before browser creation or earlier actions.
export function validateActions(actions, options) {
  const text = value => typeof value === 'string' && value.trim().length > 0;
  const selector = value => value == null || text(value);
  const finite = Number.isFinite;
  const positive = value => finite(value) && value > 0;
  const fraction = value => finite(value) && value >= 0 && value <= 1;
  const region = value => value == null || (Array.isArray(value) && value.length === 4 && value.every(finite) && value[2] > 0 && value[3] > 0);
  const optionalPositive = value => value == null || positive(value);
  const columns = value => value == null || (Number.isInteger(value) && value > 0);
  if (!Array.isArray(actions)) throw new Error('actions must be an array');
  if (options && (![options.width, options.height].every(n => Number.isInteger(n) && n > 0) || !positive(options.scale) || (options.theme != null && !['dark', 'light'].includes(options.theme)))) throw new Error('Invalid viewport/scale/theme');
  for (const [index, action] of actions.entries()) {
    if (!Array.isArray(action) || !text(action[0])) throw new Error(`Invalid action at ${index}`);
    const [kind, ...a] = action;
    let valid = false;
    switch (kind) {
      case 'wait': valid = a.length === 1 && finite(a[0]) && a[0] >= 0; break;
      case 'scroll': valid = a.length <= 1 && selector(a[0]); break;
      case 'move': valid = a.length === 3 && selector(a[0]) && a.slice(1).every(fraction); break;
      case 'click': valid = a.length >= 1 && a.length <= 3 && selector(a[0]) && a.slice(1).every(v => v == null || fraction(v)); break;
      case 'drag': valid = a.length >= 5 && a.length <= 6 && selector(a[0]) && a.slice(1, 5).every(fraction) && (a[5] == null || (Number.isInteger(a[5]) && a[5] > 0)); break;
      case 'key': valid = a.length >= 1 && a.length <= 3 && typeof a[0] === 'string' && a[0].length > 0 && selector(a[1]) && (a[2] == null || text(a[2])); break;
      case 'slow': valid = a.length === 1 && positive(a[0]); break;
      case 'eval': valid = a.length >= 1 && a.length <= 2 && text(a[0]) && optionalPositive(a[1]); break;
      case 'until': valid = a.length >= 1 && a.length <= 2 && text(a[0]) && optionalPositive(a[1]); break;
      case 'shot': valid = a.length >= 1 && a.length <= 4 && text(a[0]) && selector(a[1]) && optionalPositive(a[2]) && region(a[3]); break;
      case 'lines': valid = a.length <= 3 && (a[0] == null || text(a[0])) && selector(a[1]) && (a[2] == null || (typeof a[2] === 'object' && !Array.isArray(a[2]) && (a[2].tolerance == null || (finite(a[2].tolerance) && a[2].tolerance >= 0)))); break;
      case 'turn': valid = a.length >= 1 && a.length <= 2 && (finite(a[0]) || (a[0] && typeof a[0] === 'object' && !Array.isArray(a[0]) && Object.keys(a[0]).length > 0 && Object.values(a[0]).every(finite))) && (a[1] == null || text(a[1])); break;
      case 'orbit': valid = a.length >= 4 && a.length <= 8 && text(a[0]) && a.slice(1, 4).every(finite) && a[3] !== 0 && (a[3] > 0 ? a[1] <= a[2] : a[1] >= a[2]) && selector(a[4]) && optionalPositive(a[5]) && region(a[6]) && columns(a[7]); break;
      case 'sheet': valid = a.length >= 3 && a.length <= 7 && text(a[0]) && finite(a[1]) && a[1] >= 0 && Number.isInteger(a[2]) && a[2] > 0 && selector(a[3]) && optionalPositive(a[4]) && region(a[5]) && columns(a[6]); break;
      default: throw new Error(`unknown action ${kind}`);
    }
    if (!valid) {
      if (kind === 'orbit') throw new Error('orbit needs numeric from, to and a nonzero step toward its endpoint');
      if (kind === 'sheet') throw new Error('sheet needs a non-negative every and a whole count of at least 1');
      throw new Error(`Invalid ${kind} action at ${index}: malformed, empty or nonfinite arguments`);
    }
  }
}
