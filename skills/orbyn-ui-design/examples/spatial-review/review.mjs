import { canonical, parseJSONStrict, parseReview, validate, fresh } from './review-model.mjs';
const $ = id => document.getElementById('review-' + id);
const node = (tag, value) => { const n = document.createElement(tag); n.textContent = value; return n; };
const hex = bytes => [...new Uint8Array(bytes)].map(v => v.toString(16).padStart(2, '0')).join('');
export async function mountReview(api) {
  const status = message => { $('status').textContent = message; $('summary').textContent = message; };
  const manifest = parseJSONStrict(await fetch('manifest.json', { cache: 'no-store' }).then(r => { if (!r.ok) throw Error('Manifest unavailable'); return r.text(); }));
  async function verifySource() {
    const current = parseJSONStrict(await fetch('manifest.json', { cache: 'no-store' }).then(r => { if (!r.ok) throw Error('Source unavailable'); return r.text(); }));
    if (canonical(current) !== canonical(manifest)) throw Error('Source changed; retain feedback and start a new round');
    const { fingerprint, ...prototype } = manifest.prototype;
    const digest = async raw => hex(await crypto.subtle.digest('SHA-256', raw));
    if (await digest(new TextEncoder().encode(canonical({ prototype, targets: manifest.targets, assets: manifest.assets }))) !== fingerprint) throw Error('Manifest digest differs');
    if (Object.keys(manifest.assets).length > 100) throw Error('Asset limit');
    for (const [name, expected] of Object.entries(manifest.assets)) {
      if (!/^[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:\/[A-Za-z0-9_.-]+)*$/.test(name) || name.split('/').some(p => p.startsWith('.'))) throw Error('Unsafe asset path');
      const r = await fetch(name, { cache: 'no-store' }); if (!r.ok || await digest(await r.arrayBuffer()) !== expected) throw Error('Stale source asset: ' + name);
    }
  }
  await verifySource(); await document.fonts.ready;
  const capture = () => { const context = { modelRevision: manifest.assets['engine-data.json'], ...api.capture() }; if (['film', 'gallery'].includes(context.animation.scenario)) context.filmRevision = manifest.assets[context.animation.scenario === 'gallery' ? 'film-gallery.json' : 'film.mjs']; return context; };
  let doc = fresh(manifest, capture()), annotation = false, revision = 0, token = null, saving = false, recovery = null, hadBrowserDraft = false;
  const storageKey = 'spatial-review-v2';
  const download = (raw, name) => { const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); };
  try { const raw = localStorage.getItem(storageKey); if (raw !== null) { try { doc = parseReview(raw, manifest); hadBrowserDraft = true; } catch { recovery = raw; } } } catch { $('draft').textContent = 'Browser draft storage unavailable; use repo save or export.'; }
  try {
    const r = await fetch('api/review', { cache: 'no-store' }); if (!r.ok) throw Error('Repo bridge unavailable');
    const body = parseJSONStrict(await r.text()); if (!Number.isInteger(body.revision) || typeof body.token !== 'string') throw Error('Invalid bridge response');
    revision = body.revision; token = body.token;
    if (body.review) { const saved = validate(body.review, manifest); if (hadBrowserDraft && canonical(doc) !== canonical(saved)) { recovery = JSON.stringify(doc); } doc = saved; }
    status(body.review ? `Reopened repo review revision ${revision}; preview restored paused.` : 'Ready. Save review to repo also persists settings with zero comments.');
  } catch (error) { status(`${error.message}. Static export/import remains available; no repository save yet.`); }
  api.restore(doc.settings);
  if (recovery !== null) { $('recovery').hidden = false; $('recovery').onclick = () => download(recovery, 'unvalidated-spatial-recovery.json'); }
  function persist() {
    if (recovery !== null) { $('draft').textContent = 'Different browser draft retained for recovery; current work can still save/export.'; return; }
    try { const raw = JSON.stringify(validate(doc, manifest)); localStorage.setItem(storageKey, raw); if (localStorage.getItem(storageKey) !== raw) throw Error('Draft readback failed'); $('draft').textContent = 'Browser draft only; repository save is separate.'; } catch (e) { $('draft').textContent = `Browser draft failed: ${e.message}. Export or save to repo.`; }
  }
  function render() {
    $('mode').textContent = annotation ? 'Comment mode on' : 'Comment mode'; $('mode').setAttribute('aria-pressed', String(annotation));
    $('text').disabled = doc.state === 'submitted'; $('post').disabled = doc.state === 'submitted'; $('finish').disabled = saving || doc.state === 'submitted'; $('save').disabled = saving;
    $('target').value = doc.pending?.targetId ?? '';
    $('text').value = doc.pending?.text ?? '';
    $('context').textContent = doc.pending ? `${doc.pending.targetId} · ${doc.pending.context.animation.scene} / ${doc.pending.context.animation.time.toFixed(2)}s · yaw ${doc.pending.context.camera.yaw}° · captured viewport ${doc.pending.context.viewport.width}×${doc.pending.context.viewport.height}` : `${doc.state} · ${doc.comments.length} comments · current camera/time/layers saved as settings`;
    $('comments').replaceChildren();
    for (const c of doc.comments) {
      const li = node('li', ''), title = node('strong', `${c.targetId} · ${c.context.animation.scene} at ${c.context.animation.time.toFixed(2)}s · ${c.disposition}`), words = node('p', c.text), button = node('button', 'Restore paused review context');
      button.onclick = async () => { try { if (doc.pending?.text.trim()) throw Error('Post pending text before restoring another context'); status('Checking source before restoring paused context…'); await verifySource(); api.restore(c.context); status(`Restored ${c.context.partId}, model ${c.context.modelRevision}, yaw ${c.context.camera.yaw}°, layers and ${c.context.animation.time}s paused. Viewport is recorded, not resized.`); } catch (e) { status(e.message); } };
      li.append(title, words, button); $('comments').append(li);
    }
    for (const p of document.querySelectorAll('#stage [data-name]')) { p.classList.toggle('review-part', annotation); p.classList.toggle('review-anchor', doc.pending?.targetId === 'part/' + p.dataset.name); }
  }
  function pick(id) {
    if (doc.state !== 'draft') { status('Submitted review is immutable; preserve it and start an explicit new round.'); return; }
    if (doc.pending?.text.trim()) { $('target').value = doc.pending.targetId; status('Post pending text before changing anchor; original context retained.'); return; }
    api.pause(); if (id.startsWith('part/')) api.focusPart(id.slice(5)); const context = capture();
    doc.pending = { targetId: id, context, text: '' }; validate(doc, manifest); persist(); render(); $('text').focus();
  }
  for (const t of manifest.targets) { const option = node('option', t.id); option.value = t.id; $('target').append(option); }
  $('target').onchange = () => { if ($('target').value) pick($('target').value); };
  $('text').oninput = () => { if (!doc.pending || doc.state !== 'draft') return; doc.pending.text = $('text').value; persist(); };
  $('post').onclick = () => { try { if (!doc.pending?.text.trim()) throw Error('Choose a target and write feedback'); const c = structuredClone(doc.pending); doc.comments.push({ ...c, id: crypto.randomUUID(), disposition: 'unresolved', decision: '' }); doc.pending = null; validate(doc, manifest); persist(); render(); $('target').focus(); } catch (e) { status(e.message); } };
  $('mode').onclick = () => { annotation = !annotation; if (annotation) api.pause(); render(); };
  const prototype = document.querySelector('main');
  function intercept(e) {
    if (!annotation || e.target.closest('#review-panel')) return;
    if (e.type === 'keydown' && ['Tab', 'Escape'].includes(e.key)) return;
    const part = e.target.closest('#stage [data-name]'), control = e.target.closest('[id]');
    const target = part ? 'part/' + part.dataset.name : control && manifest.targets.find(t => ['control/' + control.id, 'surface/' + control.id].includes(t.id))?.id;
    if (!target) { if (e.target.closest('#stage')) { e.preventDefault(); e.stopImmediatePropagation(); } return; }
    e.preventDefault(); e.stopImmediatePropagation();
    if (e.type === 'click' || (e.type === 'keydown' && ['Enter', ' '].includes(e.key))) pick(target);
  }
  for (const type of ['pointerdown', 'pointermove', 'pointerup', 'click', 'keydown', 'input', 'change']) prototype.addEventListener(type, intercept, true);
  api.onChange(() => { if (doc.state === 'draft') { const next = capture(); if (canonical(next) !== canonical(doc.settings)) { doc.settings = next; if (!saving) status('Preview changed; current settings need repo saving.'); } } });
  for (const id of ['crank', 'orbit', 'speed', 'guides', 'rods', 'story-time', 'story-scenario']) document.getElementById(id).addEventListener('change', () => { if (doc.state === 'draft') { doc.settings = capture(); persist(); if (!saving) status('Preview changed; current settings need repo saving.'); } });
  async function save() {
    if (saving) return false; saving = true; status('Saving snapshot to repo; readback pending…'); render();
    try { api.pause(); if (doc.state === 'draft') doc.settings = capture(); const snapshot = structuredClone(validate(doc, manifest)); await verifySource(); if (!token) throw Error('No repo bridge; export JSON, then validate/write/reread it in the repo');
      const r = await fetch('api/review', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Review-Token': token, 'X-Review-Revision': String(revision) }, body: JSON.stringify({ review: snapshot }) });
      const result = parseJSONStrict(await r.text()); if (!r.ok) throw Error(result.error || 'Repo save rejected'); if (canonical(result.review) !== canonical(snapshot) || result.readback !== true) throw Error('Repo readback differs'); revision = result.revision;
      status(canonical(snapshot) === canonical(doc) ? `${doc.state === 'submitted' ? 'Submitted review' : 'Review settings and feedback'} saved to repo and reread: revision ${revision}.` : `Earlier snapshot saved revision ${revision}; newer draft edits still need saving.`); return true;
    } catch (e) { status(`Not saved to repo: ${e.message}. Local feedback retained.`); return false; } finally { saving = false; render(); }
  }
  $('save').onclick = save;
  $('finish').onclick = async () => { try { if (doc.pending?.text.trim()) throw Error('Post pending feedback first'); api.pause(); doc.settings = capture(); doc.pending = null; doc.state = 'submitted'; validate(doc, manifest); persist(); render(); await save(); } catch (e) { status(e.message); } };
  $('export').onclick = () => { if (doc.state === 'draft') doc.settings = capture(); download(JSON.stringify(validate(doc, manifest), null, 2), 'spatial-review.json'); status('Export requested; this is not proof of a repo write.'); };
  $('import').onchange = async () => { try { const file = $('import').files[0]; if (!file || file.size > 524288) throw Error('Import size'); await verifySource(); const next = parseReview(await file.text(), manifest); if ((doc.comments.length || doc.pending) && !confirm('Replace current draft with validated imported feedback?')) return; doc = next; api.restore(doc.settings); persist(); render(); status('Validated import restored paused; save to repo separately.'); } catch (e) { status('Import rejected; current feedback retained: ' + e.message); } finally { $('import').value = ''; } };
  for (const n of document.querySelectorAll('#review-panel [disabled]')) n.disabled = false;
  render(); document.body.dataset.reviewReady = 'true';
}
