import assert from 'node:assert/strict';
import test from 'node:test';
import { Composer, enterAction, projectPart, scrollPolicy, sampleTokens, validateTokens } from './chat.mjs';

test('acknowledged snapshot clears an unchanged draft', () => {
  const c = new Composer('account-a/thread-a');
  c.edit('Hello');
  const request = c.submit();
  assert.equal(request.text, 'Hello');
  assert.equal(c.settle(request, 'sent'), true);
  assert.equal(c.draft, '');
  assert.equal(c.pending, null);
});

test('new typing survives an older acknowledgement even if text changes back', () => {
  const c = new Composer('a/t');
  c.edit('Hello');
  const request = c.submit();
  c.edit('New draft');
  c.edit('Hello');
  c.settle(request, 'sent');
  assert.equal(c.draft, 'Hello');
});

test('double submission is fenced, but known failure permits a deliberate retry', () => {
  const c = new Composer('a/t');
  c.edit('Keep this');
  const first = c.submit();
  assert.equal(c.submit(), null);
  c.settle(first, 'failed');
  assert.equal(c.draft, 'Keep this');
  const next = c.submit();
  assert.notEqual(next.id, first.id);
  assert.equal(c.settle(first, 'sent'), false);
  assert.equal(c.pending, next);
});

test('unknown outcome blocks another send until the same owner reconciles it', () => {
  const c = new Composer('a/t');
  c.edit('Send');
  const request = c.submit();
  c.settle(request, 'unknown');
  assert.equal(c.submit(), null);
  assert.equal(c.draft, 'Send');
  assert.equal(c.settle(request, 'sent'), true);
  assert.equal(c.draft, '');
});

test('retired scope fences late callbacks and retains its draft', () => {
  const old = new Composer('a/t');
  old.edit('Original');
  const pending = old.submit();
  old.retire();
  const current = new Composer('b/t');
  current.edit('Current');
  assert.equal(current.settle(pending, 'sent'), false);
  assert.equal(old.settle(pending, 'sent'), false);
  assert.equal(old.draft, 'Original');
  assert.equal(current.draft, 'Current');
  assert.equal(old.submit(), null);
});

test('forged same-shaped acknowledgement is not the admitted operation', () => {
  const c = new Composer('a/t'); c.edit('Hello'); const p = c.submit();
  assert.equal(c.settle({ ...p }, 'sent'), false);
  assert.equal(c.pending, p);
});

test('IME and multiline preserve native keyboard input', () => {
  assert.equal(enterAction({ key: 'Enter', isComposing: true }), 'native');
  assert.equal(enterAction({ key: 'Enter', shiftKey: true }), 'native');
  assert.equal(enterAction({ key: 'Enter' }), 'submit');
  // WebKit ends composition before this keydown, so only keyCode 229 identifies it.
  assert.equal(enterAction({ key: 'Enter', isComposing: false, keyCode: 229 }), 'native');
  const c = new Composer('a/t'); c.edit('Text');
  assert.equal(c.submit({ composing: true }), null);
});

test('empty and oversized drafts cannot be submitted', () => {
  const c = new Composer('a/t'); c.edit('   '); assert.equal(c.submit(), null);
  assert.throws(() => c.edit('a'.repeat(8001)), /invalid draft/);
});

test('text remains data and unknown parts/versions are non-executable', () => {
  const html = '<img src=x onerror=alert(1)>';
  assert.deepEqual(projectPart({ type: 'text', version: 1, text: html }), { kind: 'text', text: html });
  for (const p of [null, { type: 'text', version: 2, text: 'new' },
    { type: 'script', version: 1, code: 'execute' }, { type: 'status', version: 1, state: 'authorized' }]) {
    assert.equal(projectPart(p).kind, 'unsupported');
  }
  assert.equal(projectPart({ type: 'status', version: 1, state: 'complete' }).text, 'Response complete');
});

test('stream updates preserve reading intent while explicit jump follows', () => {
  assert.equal(scrollPolicy({ atEnd: false, cause: 'append' }), 'preserve-position');
  assert.equal(scrollPolicy({ atEnd: true, cause: 'append' }), 'follow');
  assert.equal(scrollPolicy({ atEnd: false, cause: 'jump' }), 'follow');
  assert.equal(scrollPolicy({ atEnd: true, cause: 'prepend' }), 'preserve-anchor');
});

test('product token mappings are retained; CSS/resource injection is refused', () => {
  const product = { ...sampleTokens, action: '#114433', focus: '#b93815' };
  assert.deepEqual(validateTokens(product), product);
  assert.throws(() => validateTokens({ ...product, panel: 'url(https://example.test)' }));
  assert.throws(() => validateTokens({ ...product, extra: '#000000' }));
  assert.throws(() => validateTokens({ action: '#114433' }));
});

test('pending/error attachments gate send; ready snapshots submit and clear', () => {
  const c = new Composer('a/t');
  const token = c.addAttachment('outline.txt');
  assert.equal(c.submit(), null);
  assert.equal(c.updateAttachment(token, 'error'), true);
  assert.equal(c.submit(), null);
  assert.equal(c.updateAttachment(c.attachments[0], 'ready'), true);
  const request = c.submit();
  assert.equal(request.attachments[0].name, 'outline.txt');
  c.settle(request, 'sent');
  assert.equal(c.attachments.length, 0);
});

test('cancelled attachment completion cannot reinsert the attachment', () => {
  const c = new Composer('a/t'); const token = c.addAttachment('note.txt');
  c.removeAttachment(token.id);
  assert.equal(c.updateAttachment(token, 'ready'), false);
  assert.equal(c.attachments.length, 0);
});

test('new attachment survives acknowledgement and failed send retains snapshot', () => {
  const c = new Composer('a/t'); const first = c.addAttachment('first.txt');
  c.updateAttachment(first, 'ready'); const request = c.submit();
  const next = c.addAttachment('next.txt');
  c.settle(request, 'sent');
  assert.equal(c.attachments.length, 1); assert.equal(c.attachments[0], next);
  c.updateAttachment(next, 'ready'); const retry = c.submit();
  c.settle(retry, 'failed'); assert.equal(c.attachments.length, 1);
});

test('read-only mode prevents new edits/uploads/submits but admits an old known result', () => {
  const c = new Composer('a/t'); c.edit('pending'); const request = c.submit();
  c.setReadOnly(true);
  assert.equal(c.submit(), null); assert.equal(c.addAttachment('x.txt'), null);
  assert.throws(() => c.edit('other'));
  assert.equal(c.settle(request, 'sent'), true); assert.equal(c.draft, '');
  c.setReadOnly(false); c.edit('allowed'); assert.ok(c.submit());
});

test('scope retirement also fences uploads and bounds local attachment count', () => {
  const c = new Composer('a/t'); const first = c.addAttachment('first.txt');
  c.addAttachment('second.txt'); c.addAttachment('third.txt');
  assert.equal(c.addAttachment('fourth.txt'), null);
  c.retire(); assert.equal(c.updateAttachment(first, 'ready'), false);
});

test('A to B to A fences original callbacks even though scope and pending operation repeat', () => {
  const a = new Composer('account-a/thread-a'); a.edit('Draft A');
  const request = a.submit(); const upload = a.addAttachment('late.txt');
  a.fenceDelivery();
  const b = new Composer('account-a/thread-b'); b.edit('Draft B');
  b.fenceDelivery(); // Returning to A uses a new delivery generation.
  assert.equal(a.settle(request, 'sent'), false);
  assert.equal(a.updateAttachment(upload, 'ready'), false);
  assert.equal(a.draft, 'Draft A'); assert.equal(b.draft, 'Draft B');
  assert.equal(a.submit(), null); // Existing unknown outcome remains fenced.
  // Explicit simulated current-owner reconciliation, distinct from old callback.
  assert.equal(a.settle(request, 'sent', a.epoch), true);
  assert.equal(a.draft, ''); assert.equal(b.draft, 'Draft B');
});

test('both synthetic consuming palettes retain their own complete semantic mapping', async () => {
  const { consumerPalettes } = await import('./palettes.mjs');
  for (const palette of Object.values(consumerPalettes)) assert.deepEqual(validateTokens(palette.tokens), palette.tokens);
  assert.notEqual(consumerPalettes['harbor-desk'].tokens.action, consumerPalettes['pine-studio'].tokens.action);
});

test('duplicate ready updates preserve admitted snapshot identity and clear on acknowledgement', () => {
  const c = new Composer('a/t');
  c.edit('Send the outline');
  const selected = c.addAttachment('outline.txt');
  c.updateAttachment(selected, 'ready');
  const ready = c.attachments[0];
  const request = c.submit();
  assert.equal(c.updateAttachment(ready, 'ready'), true);
  assert.equal(c.attachments[0], ready);
  c.settle(request, 'sent');
  assert.equal(c.draft, '');
  assert.equal(c.attachments.length, 0);
});

test('changed or replaced attachment survives an older send acknowledgement', () => {
  for (const change of ['new-upload-generation', 'replacement']) {
    const c = new Composer('a/t');
    const selected = c.addAttachment('outline.txt');
    c.updateAttachment(selected, 'ready');
    const original = c.attachments[0];
    const request = c.submit();
    if (change === 'replacement') {
      c.removeAttachment(original.id);
      const replacement = c.addAttachment('outline.txt');
      c.updateAttachment(replacement, 'ready');
    } else {
      c.updateAttachment(original, 'pending');
      c.updateAttachment(c.attachments[0], 'ready');
    }
    const changed = c.attachments[0];
    assert.notEqual(changed, original);
    c.settle(request, 'sent');
    assert.equal(c.attachments.length, 1);
    assert.equal(c.attachments[0], changed);
  }
});
