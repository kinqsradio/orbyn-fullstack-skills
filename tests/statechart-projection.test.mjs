// Orbyn-authored semantic fixtures for the pinned MIT pstack compiler.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { project } from '../skills/architect/references/upstream/pstack-statechart/compiler/pipeline.ts';
import { walk, bugs } from '../skills/architect/references/upstream/pstack-statechart/compiler/passes/reach.ts';
import { mermaid } from '../skills/architect/references/upstream/pstack-statechart/compiler/backends/mermaid.ts';

import { guardView } from '../skills/architect/scripts/guard-statechart-view.mjs';
import { decodeTrace } from '../skills/architect/examples/leased-job/replay.mjs';

const graph = (nodes, edges) => ({ states: new Map(nodes.map(([id, vars, start = false, breaks = []]) => [id, { vars, start, breaks }])), steps: edges.map(([from, to, action]) => ({ from, to, action })) });
const draw = (g, view, loops = []) => {
  const result = project(g, walk(g), view, [...bugs(g), ...loops]);
  return { ...result, text: mermaid(result.chart) };
};

test('mixed safe/violating concrete labels retain possible violation and rule identity', () => {
  const g = graph([['a', { x: 0 }, true], ['b', { x: 1 }, false, [{ kind: 'invariant', name: 'Fresh' }]]], [['a', 'b', 'Advance'], ['b', 'a', 'Reset']]);
  const { text } = draw(g, { state: () => 'merged' });
  assert.match(text, /mayBreak/); assert.match(text, /Fresh/);
  assert.doesNotMatch(text, /class s\d+ breaks\n/);
});

test('hidden bug path and hidden reachability cannot produce a misleading chart', () => {
  const g = graph([['a', { x: 0 }, true], ['b', { x: 1 }, false, [{ kind: 'invariant', name: 'Safe' }]]], [['a', 'b', 'Advance'], ['b', 'a', 'Reset']]);
  assert.throws(() => draw(g, { state: v => String(v.x), step: () => null }), /path|hides|reachable|step/i);
});

test('cannot hide only some instances of one displayed arrow', () => {
  const g = graph([['a', { x: 0 }, true], ['b', { x: 1 }], ['c', { x: 2 }], ['d', { x: 3 }]], [['a', 'b', 'Prepare'], ['a', 'c', 'Go'], ['b', 'd', 'Go'], ['c', 'a', 'Reset'], ['d', 'b', 'Reset']]);
  assert.doesNotThrow(() => draw(g, { state: v => v.x < 2 ? 'A' : 'B', step: (a, from) => a === 'Go' && from.x === 1 ? null : a }));
  assert.throws(() => draw(g, { ...guardView({ state: v => v.x < 2 ? 'A' : 'B', step: (a, from) => a === 'Go' && from.x === 1 ? null : a }) }), /Partial hidden arrow for Go/);
});

test('fully visible, fully hidden and refined endpoint guards remain usable', () => {
  for (const hidden of [true, false]) {
    const view = guardView({ state: v => v.phase, step: () => hidden ? null : 'go' });
    assert.equal(view.step('Go', { phase: 'A', n: 0 }, { phase: 'B', n: 1 }), hidden ? null : 'go');
    assert.equal(view.step('Go', { phase: 'A', n: 2 }, { phase: 'B', n: 3 }), hidden ? null : 'go');
  }
  const refined = guardView({ state: v => String(v.n), step: (a, from) => from.n === 0 ? null : a });
  assert.equal(refined.step('Go', { n: 0 }, { n: 1 }), null);
  assert.equal(refined.step('Go', { n: 2 }, { n: 3 }), 'Go');
});

test('parallel chart preserves other-region admission guard', () => {
  const g = graph([['a', { online: false, busy: false }, true], ['b', { online: true, busy: false }], ['c', { online: true, busy: true }], ['d', { online: false, busy: true }]], [['a', 'b', 'Connect'], ['b', 'a', 'Disconnect'], ['b', 'c', 'Start'], ['c', 'd', 'Disconnect'], ['d', 'c', 'Connect'], ['c', 'b', 'Stop'], ['d', 'a', 'Stop']]);
  const { text } = draw(g, { state: v => ({ Network: v.online ? 'online' : 'offline', Job: v.busy ? 'busy' : 'idle' }) });
  assert.match(text, /Start.*\[when online\]/);
});

test('correlated region tuples fall back instead of inventing combinations', () => {
  const g = graph([['a', { x: 0 }, true], ['b', { x: 1 }], ['c', { x: 2 }]], [['a', 'b', 'Both'], ['a', 'c', 'Both']]);
  const result = draw(g, { state: v => ({ Left: String(v.x), Right: String(v.x) }) });
  assert.ok(result.chart.lie, 'Fallback reason must be preserved');
  assert.doesNotMatch(result.text, /^\s*--$/m);
});

test('projection cannot invent an escape from an actual temporal lasso', () => {
  const g = graph([['a', { phase: 'wait', key: false }, true], ['b', { phase: 'wait', key: true }], ['c', { phase: 'open', key: true }]], [['a', 'a', 'Wait'], ['a', 'b', 'Enable'], ['b', 'c', 'Open'], ['c', 'a', 'Back']]);
  const loop = { rule: { kind: 'property', name: 'EventuallyOpen' }, start: 'a', path: [{ action: 'Wait', state: 'a', step: g.steps[0] }], loop: 0, stutters: false };
  assert.throws(() => draw(g, { state: v => v.phase }, [loop]), /loop cannot take|draws the step/i);
  assert.match(draw(g, { state: v => `${v.phase}, key ${v.key}` }, [loop]).text, /repeats/);
});

test('invariant and temporal rule identities remain distinct despite equal names', async () => {
  const { ruleKey } = await import('../skills/architect/references/upstream/pstack-statechart/compiler/ir.ts');
  assert.notEqual(ruleKey({ kind: 'invariant', name: 'Same' }), ruleKey({ kind: 'property', name: 'Same' }));
});

test('guard rejects malformed step exports instead of silently replacing them', () => {
  assert.throws(() => guardView({ step: 'not a function' }), /step must be a function/);
});

test('sample trace decoder accepts the CRLF output its state header already allows', () => {
  const trace = ['State 1: <Initial predicate>', '/\\ phase = "ready"', '/\\ generation = 0', '/\\ owner = 0', '/\\ tokens = <<0, 0>>', '/\\ resultGeneration = 0', '/\\ resultWorker = 0', '/\\ publishCount = 0', '/\\ lateCancel = FALSE', ''];
  const lf = [...trace, 'State 2: <Claim line 1>', ...trace.slice(1)].join('\n');
  const crlf = lf.replaceAll('\n', '\r\n');
  assert.deepEqual(decodeTrace(crlf), decodeTrace(lf));
});
