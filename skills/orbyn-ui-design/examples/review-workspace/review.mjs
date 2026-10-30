import { TARGETS, bindManifest, manifestPayload, freshReview, validateReview, parseReview, serializeReview, postPending, submitReview, persistBrowser } from './model.mjs';
const $ = id => document.getElementById(id);
const manifest = await fetch('manifest.json', { cache: 'no-store' }).then(r => { if (!r.ok) throw Error('Source manifest unavailable'); return r.json(); }).catch(e => { $('status').textContent = e.message; throw e; });
const hex = buffer => [...new Uint8Array(buffer)].map(v => v.toString(16).padStart(2, '0')).join('');
async function verifySource() {
  const current = await fetch('manifest.json', { cache: 'no-store' }).then(r => { if (!r.ok) throw Error('Prototype source unavailable/changed'); return r.json(); });
  const computed = hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(manifestPayload(current))));
  if (computed !== manifest.prototype.fingerprint || current.prototype.fingerprint !== computed) throw Error('Prototype source changed; export retained feedback and reconcile versions.');
  for (const [name, expected] of Object.entries(manifest.assets)) {
    const response = await fetch(name, { cache: 'no-store' });
    if (!response.ok || hex(await crypto.subtle.digest('SHA-256', await response.arrayBuffer())) !== expected) throw Error('Prototype asset changed; review source identity is stale.');
  }
}
await verifySource().catch(e => { $('status').textContent = e.message; throw e; }); bindManifest(manifest);
const el = (tag, value = '') => { const node = document.createElement(tag); node.textContent = value; return node; };
let doc = freshReview(), page = location.hash === '#settings' ? 'settings' : 'work', scenario = 'default';
let annotation = false, backend = null, revision = 0, recoveryRaw = null, saving = false;
const status = message => { $('status').textContent = message; };
const currentContext = () => ({ page, state: scenario, theme: doc.settings.theme, density: doc.settings.density, viewport: { width: window.innerWidth, height: window.innerHeight } });
function persist() {
  if (recoveryRaw !== null) { $('draft-status').textContent = 'A different browser recovery draft is retained. Export it; current work can still save to package/export.'; return; }
  $('draft-status').textContent = persistBrowser(doc, () => window.localStorage).message;
}
function visibleTargets() {
  return [...$('prototype').querySelectorAll('[data-review-target]')].filter(n => n.getClientRects().length && !n.closest('[hidden]'));
}
function targetNode(id) { return [...$('prototype').querySelectorAll('[data-review-target]')].find(n => n.dataset.reviewTarget === id); }
function describe(id) { const t = TARGETS.find(t => t.id === id); return t ? `${t.kind} · ${t.component} / ${t.instance}` : id; }
function pick(id) {
  if (doc.state !== 'draft') { status('Submitted review is read-only. Export it for agent reconciliation.'); return; }
  if (doc.pending?.text.trim()) {
    if (doc.pending.targetId !== id) status('Post your current comment before changing target; its text and original context are retained.');
    $('target').value = doc.pending.targetId;
    return;
  }
  doc.pending = { targetId: id, context: currentContext(), text: '' }; validateReview(doc); persist(); render(); $('comment').focus();
}
function pins() {
  $('pins').replaceChildren();
  for (const node of $('prototype').querySelectorAll('.review-selected')) node.classList.remove('review-selected');
  const selected = targetNode(doc.pending?.targetId);
  if (selected?.getClientRects().length) selected.classList.add('review-selected');
  if (!annotation) return; // Ordinary interaction retains unobstructed controls; comments remain in the panel.
  const canvas = $('canvas').getBoundingClientRect(), offsets = new Map();
  doc.comments.forEach((c, index) => {
    const target = targetNode(c.targetId); if (!target || !target.getClientRects().length || target.closest('[hidden]')) return;
    const rect = target.getBoundingClientRect(), offset = offsets.get(c.targetId) ?? 0; offsets.set(c.targetId, offset + 25);
    const pin = el('button', String(index + 1)); pin.type = 'button'; pin.className = 'pin';
    const control = TARGETS.find(t => t.id === c.targetId)?.kind === 'control';
    pin.style.top = `${Math.max(0, Math.min(canvas.height - 28, rect.top - canvas.top + (control ? -30 : 3)))}px`;
    pin.style.left = `${Math.max(0, Math.min(canvas.width - 28, rect.right - canvas.left - 24 - offset))}px`;
    pin.setAttribute('aria-label', `Comment ${index + 1}: ${describe(c.targetId)}; recorded ${c.context.theme}, ${c.context.state}`);
    pin.onclick = () => { $('comments').children[index]?.scrollIntoView({ block: 'nearest' }); $('comments').children[index]?.querySelector('button')?.focus(); };
    $('pins').append(pin);
  });
}
function render() {
  $('work-page').hidden = page !== 'work'; $('settings-page').hidden = page !== 'settings';
  $('error-panel').hidden = scenario !== 'error'; $('scenario').value = scenario;
  $('page-title').textContent = page === 'work' ? 'Work queue' : 'Preferences';
  for (const n of document.querySelectorAll('[data-route]')) { if (n.dataset.route === page) n.setAttribute('aria-current', 'page'); else n.removeAttribute('aria-current'); }
  $('prototype').dataset.theme = doc.settings.theme; $('prototype').dataset.density = doc.settings.density;
  $('theme').value = doc.settings.theme; $('density').value = doc.settings.density; $('notifications').checked = doc.settings.notifications;
  for (const id of ['theme', 'density', 'notifications', 'apply']) $(id).disabled = doc.state !== 'draft';
  $('canvas').classList.toggle('annotation', annotation); $('mode').setAttribute('aria-pressed', String(annotation));
  $('mode').textContent = annotation ? 'Comment mode on' : 'Comment mode';
  $('review-state').textContent = doc.state === 'submitted' ? 'Submitted' : 'Draft';
  $('save').disabled = saving; $('finish').disabled = saving || doc.state === 'submitted'; $('finish').textContent = doc.state === 'submitted' ? 'Review submitted' : 'Finish review';
  const picker = $('target'); picker.replaceChildren(new Option('Choose a target…', ''));
  const ids = new Set(visibleTargets().map(n => n.dataset.reviewTarget));
  if (doc.pending) ids.add(doc.pending.targetId);
  for (const id of ids) picker.add(new Option(`${describe(id)}${targetNode(id)?.closest('[hidden]') ? ' (other page)' : ''}`, id));
  picker.value = doc.pending?.targetId ?? ''; picker.disabled = doc.state !== 'draft';
  $('comment').disabled = !doc.pending || doc.state !== 'draft'; $('post').disabled = !doc.pending || doc.state !== 'draft';
  if ($('comment').value !== (doc.pending?.text ?? '')) $('comment').value = doc.pending?.text ?? '';
  $('selected-context').textContent = doc.pending ? `${doc.pending.targetId} · captured ${doc.pending.context.theme}/${doc.pending.context.state} · ${doc.pending.context.viewport.width}×${doc.pending.context.viewport.height}` : 'No target selected.';
  $('comment-count').textContent = String(doc.comments.length); $('empty-comments').hidden = !!doc.comments.length;
  $('comments').replaceChildren();
  doc.comments.forEach((c, index) => {
    const li = el('li'), button = el('button', `${index + 1} · ${describe(c.targetId)}`); button.type = 'button';
    button.onclick = () => {
      page = c.context.page; scenario = c.context.state; location.hash = page;
      if (c.targetId === 'work/detail/alpha' || c.targetId === 'work/detail/beta') {
        $('detail-alpha').hidden = c.targetId !== 'work/detail/alpha'; $('detail-beta').hidden = c.targetId !== 'work/detail/beta';
      }
      render(); targetNode(c.targetId)?.scrollIntoView({ block: 'nearest' });
      status(`Comment ${index + 1} targets ${c.targetId}. Recorded ${c.context.theme}/${c.context.density} at ${c.context.viewport.width}×${c.context.viewport.height}; pins follow this live target, not historical pixels.`);
    };
    li.append(button, el('p', c.text), el('small', `${c.disposition} · ${c.context.theme} / ${c.context.state}`)); $('comments').append(li);
  });
  $('recovery').hidden = recoveryRaw === null;
  pins();
}
for (const n of document.querySelectorAll('[data-route]')) n.onclick = () => { page = n.dataset.route; location.hash = page; render(); };
window.addEventListener('hashchange', () => { page = location.hash === '#settings' ? 'settings' : 'work'; render(); });
$('scenario').onchange = () => { scenario = $('scenario').value; render(); };
$('mode').onclick = () => { annotation = !annotation; render(); };
$('target').onchange = () => { if ($('target').value) pick($('target').value); };
for (const event of ['pointerdown', 'click', 'keydown', 'change', 'submit']) {
  $('prototype').addEventListener(event, e => {
    if (!annotation || (event === 'keydown' && ['Tab', 'Escape', 'Shift', 'Control', 'Meta', 'Alt'].includes(e.key))) return;
    const node = e.target.closest('[data-review-target]'); if (!node) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (['pointerdown', 'click', 'keydown'].includes(event)) pick(node.dataset.reviewTarget);
  }, true);
}
$('comment').oninput = () => { if (doc.pending && doc.state === 'draft') { doc.pending.text = $('comment').value; persist(); } };
$('comment-form').onsubmit = e => {
  e.preventDefault(); try { doc = postPending(doc, crypto.randomUUID()); persist(); render(); $('target').focus(); status('Comment retained in draft. Save to package or finish review for repository persistence.'); } catch (e) { status(e.message); }
};
for (const n of $('prototype').querySelectorAll('[data-open]')) n.onclick = () => {
  $('detail-alpha').hidden = n.dataset.open !== 'alpha'; $('detail-beta').hidden = n.dataset.open !== 'beta';
  $('action-result').textContent = `Opened ${n.dataset.open === 'alpha' ? 'Release notes' : 'Research brief'} — synthetic local interaction.`; render();
};
$('retry').onclick = () => { scenario = 'default'; $('action-result').textContent = 'Retry simulated. No remote request.'; render(); };
for (const id of ['theme', 'density', 'notifications']) $(id).onchange = () => {
  if (doc.state !== 'draft') return;
  doc.settings = { theme: $('theme').value, density: $('density').value, notifications: $('notifications').checked }; validateReview(doc); persist(); render();
};
$('apply').onclick = () => status('Preview preferences applied locally. Product tokens are unchanged; use Save to package for durable review data.');
async function savePackage() {
  if (saving) { status('Save is pending; local feedback is retained.'); return false; }
  try { await verifySource(); } catch (e) { status(e.message); return false; }
  if (!backend) { status('Static/export mode: no repository writer. Export JSON and have the agent validate, save and reread the target package.'); return false; }
  const snapshot = serializeReview(doc); saving = true; render();
  try {
    const response = await fetch('/api/review', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Review-Token': backend, 'X-Review-Revision': String(revision) }, body: JSON.stringify({ review: JSON.parse(snapshot) }) });
    const result = await response.json();
    if (!response.ok) throw Error(result.error ?? 'Package save failed');
    if (!result.readback || serializeReview(result.review) !== snapshot) throw Error('Package readback mismatch');
    revision = result.revision;
    if (snapshot !== serializeReview(doc)) { status(`Earlier draft saved at revision ${revision}; newer local changes still need saving.`); return false; }
    status(`${doc.state === 'submitted' ? 'Review submitted and saved' : 'Draft saved'} to package review.json · revision ${revision} · readback verified. Agent reconciliation is next; no design decision or product change was automatically approved.`);
    return true;
  } catch (e) { status(`${e.message} Local feedback retained; export JSON or reconcile the current package before retry.`); return false; }
  finally { saving = false; render(); }
}
$('save').onclick = savePackage;
$('finish').onclick = async () => { if (saving) { status('Wait for the current save; feedback is retained.'); return; } try { doc = submitReview(doc); persist(); render(); if (!await savePackage()) status('Submitted locally, but not saved to repository. Use Save to package to retry or Export JSON. Feedback remains here.'); } catch (e) { status(e.message); } };
function download(raw, name) {
  const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
  const a = el('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  status('JSON download requested. Verify the file; this is not a repository save.');
}
$('export').onclick = () => { try { download(serializeReview(doc), 'export-room-review.json'); } catch (e) { status(e.message); } };
$('recovery').onclick = () => download(recoveryRaw, 'export-room-browser-recovery.json');
$('import').onchange = async () => {
  const file = $('import').files[0]; if (!file) return;
  try {
    if (file.size > 524288) throw Error('Review file too large');
    await verifySource();
    const imported = parseReview(await file.text());
    const changed = serializeReview(doc) !== serializeReview(freshReview());
    if (changed && !window.confirm('Replace the current local review? Export it first if needed. No repository file is changed until Save to package.')) { status('Import cancelled; current feedback retained.'); return; }
    doc = imported; persist(); render(); status('Validated JSON imported locally. Repository package unchanged until explicit save.');
  } catch (e) { status(`Import rejected: ${e.message}. Current feedback retained.`); }
  finally { $('import').value = ''; }
};
window.addEventListener('resize', pins);
new ResizeObserver(pins).observe($('prototype'));
async function initialize() {
  await document.fonts.ready;
  const seen = new Set();
  for (const n of $('prototype').querySelectorAll('[data-review-target]')) {
    const id = n.dataset.reviewTarget;
    if (seen.has(id) || !TARGETS.some(t => t.id === id)) throw Error('Duplicate/stale DOM target'); seen.add(id);
  }
  if (seen.size !== TARGETS.length) throw Error('Missing prototype target');
  let browserRaw = null, browserDoc = null;
  try { browserRaw = window.localStorage.getItem('export-room-review-v1'); if (browserRaw) browserDoc = parseReview(browserRaw); }
  catch { recoveryRaw = browserRaw; $('draft-status').textContent = 'Browser recovery unavailable or invalid; it has not been erased.'; }
  try {
    const response = await fetch('/api/review');
    if (response.ok) {
      const result = await response.json(); backend = result.token; revision = result.revision;
      if (result.review) { doc = validateReview(result.review); if (browserRaw && serializeReview(browserDoc ?? freshReview()) !== serializeReview(doc)) recoveryRaw = browserRaw; }
      else if (browserDoc) doc = browserDoc;
      status(`Repository bridge ready · revision ${revision}. Save/Finish writes only this package's review.json.`);
    } else { if (browserDoc) doc = browserDoc; status('Static/export mode. Browser draft is not a repository save.'); }
  } catch { if (browserDoc) doc = browserDoc; status('Static/export mode: package bridge unavailable. Use versioned JSON export.'); }
  for (const node of document.querySelectorAll('button,input,select')) node.disabled = false;
  render(); document.body.dataset.reviewReady = 'true';
  if (recoveryRaw !== null) persist();
}
await initialize();
