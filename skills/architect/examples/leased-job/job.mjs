// Synthetic serialized service boundary, not a database/distributed-lock implementation.
export class LeasedJob {
  constructor({ brokenCompletion = false } = {}) {
    this.brokenCompletion = brokenCompletion;
    this.phase = 'ready'; this.generation = 0; this.owner = 0;
    this.tokens = [0, 0]; this.result = null; this.published = [];
    this.lateCancel = false;
  }
  claim(worker) {
    if (![1, 2].includes(worker)) throw new Error('Unknown worker');
    if (this.phase !== 'ready' || this.tokens[worker - 1] || this.generation >= 2) return false;
    this.generation += 1; this.owner = worker; this.phase = 'leased';
    this.tokens[worker - 1] = this.generation;
    return true;
  }
  expire() {
    if (this.phase !== 'leased' || this.generation >= 2) return false;
    this.phase = 'ready'; this.owner = 0;
    return true;
  }
  complete(worker) {
    if (![1, 2].includes(worker)) throw new Error('Unknown worker');
    const token = this.tokens[worker - 1];
    if (!token) return false;
    // The deliberately broken variant removes this actual generation/owner fence.
    const accepted = this.phase === 'leased' && (this.brokenCompletion ||
      (this.owner === worker && token === this.generation));
    this.tokens[worker - 1] = 0; // delivery is consumed even when rejected
    if (!accepted) return false;
    this.result = { worker, generation: token, payload: `worker-${worker}-generation-${token}` };
    this.phase = 'done'; this.owner = 0;
    return true;
  }
  cancel() {
    if (!['ready', 'leased'].includes(this.phase)) return false;
    this.phase = 'cancelled'; this.owner = 0;
    return true;
  }
  cancelAfterCommit() {
    if (this.phase !== 'done' || this.lateCancel) return false;
    this.lateCancel = true; // acknowledged as too late; durable result remains
    return true;
  }
  publish() {
    if (this.phase !== 'done') return false;
    if (!this.published.length) this.published.push({ key: 'job-1', ...this.result });
    return true; // repeat delivery is idempotent for this one job
  }
  terminal() { return this.phase === 'cancelled' || this.published.length === 1; }
  snapshot() {
    return { phase: this.phase, generation: this.generation, owner: this.owner,
      tokens: [...this.tokens], result: this.result && { ...this.result },
      published: this.published.map(row => ({ ...row })), lateCancel: this.lateCancel };
  }
}
