// Original teaching model: no runtime, transport, upload or effect implementation.
export class Composer {
  constructor(scope) {
    if (typeof scope !== 'string' || !scope.trim()) throw new Error('scope required');
    this.scope = scope;
    this.draft = '';
    this.revision = 0;
    this.sequence = 0;
    this.pending = null;
    this.retired = false;
    this.status = 'idle';
    this.readOnly = false;
    this.attachments = [];
    this.attachmentSequence = 0;
    this.epoch = 0;
  }

  edit(text) {
    if (this.retired || this.readOnly || typeof text !== 'string' || text.length > 8000) {
      throw new Error('invalid draft');
    }
    this.draft = text;
    this.revision += 1;
  }

  setReadOnly(value) { this.readOnly = Boolean(value); }

  addAttachment(name) {
    if (this.retired || this.readOnly || this.attachments.length >= 3 ||
        typeof name !== 'string' || !name.trim() || name.length > 160) return null;
    const attachment = Object.freeze({ id: ++this.attachmentSequence, name, state: 'pending', epoch: this.epoch });
    this.attachments.push(attachment);
    return attachment;
  }

  updateAttachment(token, state, deliveryEpoch = token?.epoch) {
    if (this.retired || deliveryEpoch !== this.epoch || !['ready', 'error', 'pending'].includes(state)) return false;
    const index = this.attachments.indexOf(token);
    if (index < 0) return false;
    // A repeated owner notification does not create a new attachment version.
    // Preserve the admitted snapshot so its acknowledgement can still clear it.
    if (token.state === state) return true;
    this.attachments[index] = Object.freeze({ ...token, state });
    return true;
  }

  removeAttachment(id) {
    if (this.retired || this.readOnly) return false;
    const index = this.attachments.findIndex(item => item.id === id);
    if (index < 0) return false;
    this.attachments.splice(index, 1);
    return true;
  }

  canSubmit() {
    return !this.retired && !this.readOnly && !this.pending &&
      (Boolean(this.draft.trim()) || this.attachments.length > 0) &&
      this.attachments.every(item => item.state === 'ready');
  }

  submit({ composing = false } = {}) {
    if (composing || !this.canSubmit()) return null;
    const request = Object.freeze({
      scope: this.scope,
      epoch: this.epoch,
      id: ++this.sequence,
      revision: this.revision,
      text: this.draft,
      attachments: Object.freeze([...this.attachments]),
    });
    this.pending = request;
    this.status = 'sending';
    return request;
  }

  settle(request, outcome, deliveryEpoch = request?.epoch) {
    if (this.retired || deliveryEpoch !== this.epoch || !this.pending || request !== this.pending) return false;
    if (!['sent', 'failed', 'unknown'].includes(outcome)) throw new Error('bad outcome');
    this.status = outcome;
    // Unknown keeps the operation fenced until its owner reconciles the result.
    if (outcome === 'unknown') return true;
    if (outcome === 'sent') {
      if (this.revision === request.revision) this.draft = '';
      // Only acknowledge the exact attachment snapshots admitted with this send.
      this.attachments = this.attachments.filter(item => !request.attachments.includes(item));
    }
    this.pending = null;
    return true;
  }

  fenceDelivery() {
    this.epoch += 1;
    if (this.pending) this.status = 'unknown';
    this.attachments = this.attachments.map(item => item.state === 'pending'
      ? Object.freeze({ ...item, epoch: this.epoch, state: 'error' }) : item);
  }

  retire() {
    this.retired = true;
    if (this.pending) this.status = 'unknown';
    // The draft remains available to the owning scope; no late callback can clear it.
  }
}

export function enterAction({ key, shiftKey, isComposing }) {
  return key === 'Enter' && !shiftKey && !isComposing ? 'submit' : 'native';
}

export function projectPart(part) {
  if (part?.type === 'text' && part.version === 1 && typeof part.text === 'string') {
    return { kind: 'text', text: part.text.slice(0, 16000) };
  }
  if (part?.type === 'status' && part.version === 1 &&
      ['pending', 'complete', 'failed'].includes(part.state)) {
    return { kind: 'status', text: `Response ${part.state}` };
  }
  return { kind: 'unsupported', text: 'This content type is not supported in this view.' };
}

export function scrollPolicy({ atEnd, cause }) {
  if (cause === 'jump') return 'follow';
  if (cause === 'prepend') return 'preserve-anchor';
  return atEnd ? 'follow' : 'preserve-position';
}

export const sampleTokens = Object.freeze({
  page: '#f4f5f7', panel: '#ffffff', text: '#18212d', muted: '#465365',
  action: '#243d59', actionText: '#ffffff', focus: '#075985', border: '#748092',
});

export function validateTokens(input) {
  const keys = Object.keys(sampleTokens);
  if (!input || typeof input !== 'object' || Array.isArray(input) ||
      Object.keys(input).length !== keys.length ||
      keys.some(key => typeof input[key] !== 'string' || !/^#[0-9a-f]{6}$/i.test(input[key]))) {
    throw new Error('Provide exactly the eight semantic roles as six-digit hex colours.');
  }
  return Object.fromEntries(keys.map(key => [key, input[key]]));
}
