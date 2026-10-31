import { Composer, enterAction, projectPart, scrollPolicy, validateTokens } from './chat.mjs';
import { consumerPalettes } from './palettes.mjs';
const byId = id => document.getElementById(id);
const transcript = byId('transcript');
const sessions = new Map();
let active;
let previous;
let composing = false;
let messageId = 0;

function makeSession(thread) {
  return { thread, composer: new Composer(`sample-account/${thread}`), messages: [], scrollTop: 0 };
}
function messageNode(message) {
  const article = document.createElement('article');
  article.dataset.messageId = message.id;
  const role = document.createElement('strong');
  role.textContent = message.author;
  const body = document.createElement('p');
  body.textContent = projectPart(message.part).text;
  article.append(role, body);
  return article;
}
function append(session, author, part) {
  const message = { id: `sample-${++messageId}`, author, part };
  session.messages.push(message);
  if (session !== active) return;
  const atEnd = transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 24;
  const top = transcript.scrollTop;
  transcript.append(messageNode(message));
  transcript.scrollTop = scrollPolicy({ atEnd, cause: 'append' }) === 'follow' ? transcript.scrollHeight : top;
}
function refresh() {
  const composer = active.composer;
  if (byId('draft').value !== composer.draft) byId('draft').value = composer.draft;
  byId('draft').readOnly = composer.readOnly;
  byId('readonly').checked = composer.readOnly;
  byId('attach').disabled = composer.readOnly || composer.attachments.length >= 3;
  byId('send').disabled = !composer.canSubmit();
  byId('previous').disabled = !previous?.composer.pending;
  for (const button of document.querySelectorAll('[data-outcome]')) button.disabled = !composer.pending;
  byId('state').textContent = `Thread: ${active.thread}\nFixture state: ${composer.status}\nDelivery generation: ${composer.epoch}\nDraft revision: ${composer.revision}\nPending snapshot: ${composer.pending ? composer.pending.id : 'none'}`;
  const list = byId('attachments');
  list.replaceChildren();
  for (const item of composer.attachments) {
    const row = document.createElement('li');
    const name = document.createElement('span');
    name.textContent = `${item.name}: ${item.state} `;
    row.append(name);
    for (const [label, action] of [['Mark ready', 'ready'], ['Fail upload', 'error'], ['Remove', 'remove']]) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = label;
      button.setAttribute('aria-label', `${label}: ${item.name}`);
      button.disabled = composer.readOnly;
      button.addEventListener('click', () => {
        if (action === 'remove') composer.removeAttachment(item.id);
        else composer.updateAttachment(item, action, composer.epoch);
        refresh();
        // This explicit replacement removes the focused control; return to the
        // composer only if focus was lost, never steal it from another control.
        if (document.activeElement === document.body) byId('draft').focus({ preventScroll: true });
      });
      row.append(button);
    }
    list.append(row);
  }
}
function activate(thread) {
  if (active) { active.scrollTop = transcript.scrollTop; active.composer.fenceDelivery(); previous = active; }
  if (!sessions.has(thread)) {
    const session = makeSession(thread);
    sessions.set(thread, session);
    append(session, 'Assistant', { type: 'text', version: 1, text: `Welcome to the ${thread} conversation. Drafts and messages belong to this thread.` });
  }
  active = sessions.get(thread);
  composing = false;
  transcript.replaceChildren(...active.messages.map(messageNode));
  transcript.scrollTop = active.scrollTop;
  byId('status').textContent = `Opened ${thread}. Its draft and reading position are restored.`;
  refresh();
}
function settle(session, outcome) {
  const request = session.composer.pending;
  if (!request || !session.composer.settle(request, outcome, session.composer.epoch)) return;
  if (outcome === 'sent') {
    const files = request.attachments.map(item => item.name);
    append(session, 'You', { type: 'text', version: 1, text: [request.text, files.length ? `Attachments: ${files.join(', ')}` : ''].filter(Boolean).join('\n') });
  }
  if (session === active) {
    byId('status').textContent = {
      sent: 'Snapshot acknowledged by the simulated owner. Newer typing is preserved.',
      failed: 'Known send failure. Draft and attachments retained; retry when ready.',
      unknown: 'Outcome unknown. New sends are blocked until reconciliation. Choose a known result to simulate it.',
    }[outcome];
  } else byId('status').textContent = `Resolved ${session.thread} in its own scope. This conversation was not changed.`;
  refresh();
}
byId('thread').addEventListener('change', event => activate(event.target.value));
byId('readonly').addEventListener('change', event => { active.composer.setReadOnly(event.target.checked); refresh(); });
byId('attach').addEventListener('click', () => { active.composer.addAttachment('outline.txt'); refresh(); });
byId('previous').addEventListener('click', () => { if (previous) settle(previous, 'sent'); });
byId('draft').addEventListener('input', event => { active.composer.edit(event.target.value); refresh(); });
byId('draft').addEventListener('compositionstart', () => { composing = true; });
byId('draft').addEventListener('compositionend', () => { composing = false; });
byId('draft').addEventListener('keydown', event => {
  if (enterAction({ key: event.key, shiftKey: event.shiftKey, isComposing: event.isComposing || composing }) === 'submit') {
    event.preventDefault(); byId('composer').requestSubmit();
  }
});
byId('composer').addEventListener('submit', event => {
  event.preventDefault();
  if (!active.composer.submit({ composing })) return;
  if (document.activeElement === byId('send')) byId('draft').focus({ preventScroll: true });
  byId('status').textContent = 'Sending this snapshot in the local simulation. You can keep typing.';
  refresh();
});
for (const button of document.querySelectorAll('[data-outcome]')) button.addEventListener('click', () => settle(active, button.dataset.outcome));
byId('append').addEventListener('click', () => append(active, 'Assistant', {
  type: 'text', version: 1,
  text: 'A simulated response. Scroll up as this conversation grows; new answers preserve your reading position until you choose Jump to latest.',
}));
byId('unknown').addEventListener('click', () => append(active, 'Assistant', { type: 'future-widget', version: 9 }));
byId('jump').addEventListener('click', () => { transcript.scrollTop = transcript.scrollHeight; });
function applyTokens(tokens) {
  const valid = validateTokens(tokens);
  for (const [role, colour] of Object.entries(valid)) document.documentElement.style.setProperty(`--${role}`, colour);
  byId('tokens').value = JSON.stringify(valid, null, 2);
}
for (const [key, palette] of Object.entries(consumerPalettes)) {
  const option = document.createElement('option'); option.value = key; option.textContent = palette.label;
  byId('palette').append(option);
}
byId('palette').addEventListener('change', event => {
  applyTokens(consumerPalettes[event.target.value].tokens);
  byId('token-status').textContent = 'Synthetic consumer mapping applied; no actual product tokens changed.';
});
byId('apply').addEventListener('click', () => {
  try { applyTokens(JSON.parse(byId('tokens').value)); byId('token-status').textContent = 'Preview tokens applied. Verify actual contrast, focus and states separately.'; }
  catch (error) { byId('token-status').textContent = `Tokens not changed: ${error.message}`; }
});
applyTokens(consumerPalettes['harbor-desk'].tokens);
activate('planning');
