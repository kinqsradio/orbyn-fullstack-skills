// Original synthetic boundary, shared by the real screen and deterministic checks.
/** @param {(account: string, signal: AbortSignal) => Promise<any[]>} transport
 * @param {(state: any) => void} publish */
export function createRecoveryController(transport, publish = (_state) => {}) {
  let generation = 0, active = true, abort;
  let state = { account: 'A', status: 'idle', rows: [], error: null };
  const emit = () => publish(state);
  return {
    get state() { return state; },
    async load(account = state.account) {
      if (!active) return;
      const current = ++generation;
      abort?.abort(); abort = new AbortController();
      state = { account, status: 'pending', rows: [], error: null }; emit();
      try {
        const rows = await transport(account, abort.signal);
        if (!active || current !== generation) return;
        state = { account, status: 'ready', rows, error: null }; emit();
      } catch (error) {
        if (!active || current !== generation) return;
        state = { account, status: 'error', rows: [], error: String(error?.message ?? error) }; emit();
      }
    },
    dispose() { active = false; ++generation; abort?.abort(); }
  };
}
export function validItem(value) {
  return typeof value === 'string' && /^[AB]-[0-9]+$/.test(value) ? value : null;
}
export function operationFeedback() {
  let next = 0;
  const operations = new Map();
  return {
    begin(id, surface = 'screen') { const token = ++next; operations.set(id, { token, surface, status: 'pending' }); return token; },
    finish(id, token, status) {
      const op = operations.get(id);
      if (!op || op.token !== token) return false;
      operations.set(id, { ...op, status }); return true;
    },
    remove(id, token) { if (operations.get(id)?.token === token) operations.delete(id); },
    get(id) { return operations.get(id); }
  };
}
// Connector adapter example, deliberately not a production tracker implementation.
export async function reconcileCause(adapter, cause, candidate, actor) {
  if (![cause?.repo, cause?.root, cause?.id, candidate, actor].every(value => typeof value === 'string' && value.trim())) throw new Error('missing scope identity');
  const key = JSON.stringify([cause.repo, cause.root, cause.id]);
  const records = []; const cursors = new Set(); let cursor = null, pages = 0;
  do {
    if (++pages > 100 || cursors.has(cursor)) throw new Error('pagination limit or cycle');
    cursors.add(cursor);
    const page = await adapter.list(key, cursor);
    if (!page.complete || !Array.isArray(page.items)) throw new Error('incomplete inventory');
    records.push(...page.items.filter(item => item.key === key)); cursor = page.next;
  } while (cursor);
  if (records.length > 1) throw new Error('ambiguous duplicate');
  let record = records[0];
  if (record) {
    if (typeof record.id !== 'string' || !record.id) throw new Error('missing remote id');
    record = await adapter.read(record.id); // current authoritative state, not list marker
    if (!record || record.key !== key) throw new Error('readback identity conflict');
    if (record.owner && record.owner !== actor) throw new Error('foreign claim');
    if (record.candidate !== candidate) throw new Error('stale candidate');
  }
  // A lost response propagates. Replay lists and reads before another create.
  if (!record) record = await adapter.create({ key, candidate, owner: actor, status: 'open' });
  const actual = await adapter.read(record.id);
  if (actual.key !== key || actual.candidate !== candidate || actual.owner !== actor) throw new Error('readback conflict');
  return actual;
}
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const match = (a, b, keys) => keys.every(k => nonempty(a?.[k]) && nonempty(b?.[k]) && a[k] === b[k]);
export function otaCompatible(binary, update, mapping) {
  return match(binary, update, ['platform','runtime']) && update.addsNative === false &&
    match(binary, mapping, ['channel']) && match(update, mapping, ['branch']) && mapping.complete === true;
}
export function healthComparison(a, b) {
  const keys = ['platform','runtime','window','denominator'];
  const valid = value => value?.complete === true && keys.every(k => nonempty(value[k])) &&
    Number.isSafeInteger(value.samples) && value.samples > 0 &&
    Number.isSafeInteger(value.failures) && value.failures >= 0 &&
    value.denominator === 'launches' && value.failures <= value.samples;
  // This synthetic adapter models failed-launches / launches, not arbitrary events.
  if (!valid(a) || !valid(b)) return { status: 'unknown' };
  if (!match(a, b, keys)) return { status: 'incomparable' };
  return { status: 'comparable', a: a.failures / a.samples, b: b.failures / b.samples };
}
export function captureApplicable(expected, actual) {
  return match(expected, actual, ['source','binary','screen','fixture','platform']) && actual.status === 'ready';
}
export function reusable(expected, receipt) {
  return receipt.trusted === true && match(expected, receipt, ['skills','harness','scenario','model','effort','processing','tools','sdk','environment']);
}
