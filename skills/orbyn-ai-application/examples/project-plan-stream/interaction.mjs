// Original provider-free teaching fixture. This is NOT an AG-UI wire implementation.
const clone = (value) => structuredClone(value);
function orderedJSON(value) {
  if (Array.isArray(value)) return value.map(orderedJSON);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, orderedJSON(value[key])])
    );
  }
  return value;
}
const canonical = (value) => JSON.stringify(orderedJSON(value));
const bytes = (value) => new TextEncoder().encode(value).byteLength;
const id = (value) => typeof value === "string" && /^[a-z][a-z0-9-]{0,63}$/.test(value);
const fields = (value, names) => {
  if (!value || typeof value !== "object" || Array.isArray(value) || Object.keys(value).sort().join() !== [...names].sort().join()) throw Error("Invalid fields");
};
const text = (value, max) => {
  if (typeof value !== "string" || !value.trim() || value.length > max) throw Error("Invalid text");
};
const SCOPE_KEYS = Object.freeze(["principal", "account", "resource", "thread", "run", "attempt", "connection"]);
function validateScope(scope) {
  fields(scope, SCOPE_KEYS);
  for (const key of SCOPE_KEYS.filter((k) => k !== "connection")) if (!id(scope[key])) throw Error("Invalid scope");
  if (!Number.isSafeInteger(scope.connection) || scope.connection < 1) throw Error("Invalid connection");
  return scope;
}
const scopeKey = (scope) => SCOPE_KEYS.map((k) => scope[k]).join("/");
const operationKey = (scope, operation) => [scope.principal, scope.account, scope.resource, operation].join("/");
const attemptKey = (scope, tool) => [
  scope.principal, scope.account, scope.resource,
  scope.thread, scope.run, scope.attempt, tool
].join("/");
function validatePlan(plan) {
  fields(plan, ["title", "tasks"]);
  text(plan.title, 100);
  if (!Array.isArray(plan.tasks) || plan.tasks.length < 1 || plan.tasks.length > 8) throw Error("Task budget");
  const ids = new Set();
  for (const task of plan.tasks) {
    fields(task, ["id", "title"]);
    if (!id(task.id) || ids.has(task.id)) throw Error("Task identity");
    ids.add(task.id);
    text(task.title, 120);
  }
  return plan;
}
function validateProposal(proposal) {
  fields(proposal, ["operation", "component", "version", "expectedVersion", "plan"]);
  if (!id(proposal.operation)) throw Error("Invalid logical operation");
  if (proposal.component !== "project-plan" || proposal.version !== 1) throw Error("Unsupported component");
  if (!Number.isSafeInteger(proposal.expectedVersion) || proposal.expectedVersion < 1) throw Error("Invalid record version");
  validatePlan(proposal.plan);
  return proposal;
}
// Simulated server owner: its grants, pending decisions and receipts are separate
// from delivery/UI state. Nothing survives process/page death or reaches a service.
function createEffectOwner({ principal = "person-a", account = "account-a", resource = "project-a", plan } = {}) {
  const initial = plan ?? { title: "Existing project", tasks: [{ id: "read", title: "Read the brief" }] };
  validatePlan(initial);
  const grants = new Set([principal]);
  const pending = new Map();
  const receipts = new Map();
  const executionBindings = new Map();
  let record = { version: 1, plan: clone(initial) }, writes = 0;
  function authorize(scope) {
    validateScope(scope);
    if (!grants.has(scope.principal) || scope.account !== account || scope.resource !== resource) throw Error("Denied current authority");
  }
  function entry(scope, tool, operation) {
    authorize(scope);
    if (!id(tool) || !id(operation)) throw Error("Invalid tool/operation identity");
    const key = operationKey(scope, operation), item = pending.get(key);
    if (!item) throw Error("No current logical operation");
    if (item.admitted !== attemptKey(scope, tool)) throw Error("Attempt not admitted");
    return { key, item };
  }
  return {
    registerPending(scope, tool, proposal) {
      authorize(scope);
      validateProposal(proposal);
      if (!id(tool)) throw Error("Invalid tool identity");
      const key = operationKey(scope, proposal.operation);
      const execution = attemptKey(scope, tool);
      const priorBinding = executionBindings.get(execution);
      const old = pending.get(key);
      // Keep this association after an attempt is replaced. A retired execution
      // must not become a second logical operation through producer mistakes.
      if (priorBinding !== undefined && priorBinding !== key) {
        throw Error("Execution already bound to another logical operation");
      }
      if (old && canonical(old.proposal) !== canonical(proposal)) {
        throw Error("Logical operation proposal conflict");
      }
      if (!old && pending.size >= 8) throw Error("Pending budget");
      if (priorBinding === undefined && executionBindings.size >= 64) {
        throw Error("Execution admission budget");
      }
      // All checks precede mutation, including failed retry admission.
      executionBindings.set(execution, key);
      if (old) {
        // Trusted synthetic producer admission, never a replayed event.
        old.admitted = execution;
        return;
      }
      pending.set(key, {
        proposal: clone(proposal),
        admitted: execution,
        status: "pending",
        runState: "waiting"
      });
    },
    grant(actor, allowed) {
      if (!id(actor) || typeof allowed !== "boolean") throw Error("Invalid simulated grant");
      allowed ? grants.add(actor) : grants.delete(actor);
    },
    canRead(scope) {
      authorize(scope);
      return true;
    },
    closeRun(scope, tool, operation) {
      entry(scope, tool, operation).item.runState = "closed";
    },
    resume(scope, tool, proposal) {
      validateProposal(proposal);
      const { key, item } = entry(scope, tool, proposal.operation);
      if (canonical(proposal) !== canonical(item.proposal)) throw Error("Proposal changed");
      if (item.status !== "pending") return { status: "answered", receipt: clone(receipts.get(key)) };
      if (item.runState !== "waiting" || proposal.expectedVersion !== record.version) throw Error("Stale or closed pending decision");
      return { status: "pending" };
    },
    decide(scope, tool, choice, proposal) {
      validateProposal(proposal);
      const { key, item } = entry(scope, tool, proposal.operation);
      if (!["accept", "reject"].includes(choice)) throw Error("Invalid decision");
      // Manual plan edits are allowed, but target/renderer/base version are not changed.
      if (proposal.expectedVersion !== item.proposal.expectedVersion || proposal.component !== item.proposal.component || proposal.version !== item.proposal.version) throw Error("Changed approval consequence");
      const payload = canonical({ choice, proposal });
      if (receipts.has(key)) {
        const old = receipts.get(key);
        if (old.payload !== payload) throw Error("Answered call payload conflict");
        return { ...clone(old), duplicate: true };
      }
      if (item.runState !== "waiting" || record.version !== proposal.expectedVersion) throw Error("Stale effect version");
      if (choice === "accept") {
        record = { version: record.version + 1, plan: clone(proposal.plan) };
        writes++;
      }
      item.status = "answered";
      const receipt = { operation: key, choice, version: record.version, payload };
      receipts.set(key, receipt);
      return clone(receipt);
    },
    outcome(scope, tool, operation) {
      const { key } = entry(scope, tool, operation);
      return receipts.has(key) ? clone(receipts.get(key)) : null;
    },
    concurrentEdit(plan2) {
      validatePlan(plan2);
      record = { version: record.version + 1, plan: clone(plan2) };
      writes++;
    },
    inspect() {
      return { record: clone(record), writes, answered: receipts.size };
    }
  };
}
const TYPES = new Set(["run-start", "progress", "snapshot", "delta", "args-start", "args-delta", "args-end", "tool-result", "run-end"]);
function decodeEvent(raw) {
  if (typeof raw !== "string" || bytes(raw) > 8192) throw Error("Event byte budget");
  const e = JSON.parse(raw);
  fields(e, ["id", "seq", "scope", "type", "payload"]);
  if (!id(e.id) || !Number.isSafeInteger(e.seq) || e.seq < 1 || !TYPES.has(e.type)) throw Error("Event envelope");
  validateScope(e.scope);
  return e;
}
function createSession(scope, owner, { history = false } = {}) {
  validateScope(scope);
  let current = clone(scope), disposed = false, generation = 0, seen = new Map();
  function fresh() {
    return { mode: history ? "history" : "live", transport: "open", run: "not-started", nextSeq: 1, synced: true, repair: null, revision: null, projection: null, progress: "", call: null, draft: null, dirty: false, conflict: false, activeDecision: false, business: "none", trace: [] };
  }
  let state = fresh();
  function note(type, reason) {
    state.trace.push({ type, reason, thread: current.thread, run: current.run, sequence: state.nextSeq });
    state.trace = state.trace.slice(-32);
  }
  function fail(reason) {
    state.synced = false;
    state.repair = reason;
    state.activeDecision = false;
    note("repair-required", reason);
  }
  function ensure() {
    if (disposed) throw Error("Disposed session");
  }
  function projection(plan, revision) {
    validatePlan(plan);
    if (!Number.isSafeInteger(revision) || revision < 1) throw Error("Invalid projection revision");
    if (state.dirty) state.conflict = true;
    state.projection = clone(plan);
    state.revision = revision;
  }
  function activate() {
    if (!state.call?.proposal) return;
    const result = owner.resume(current, state.call.id, state.call.proposal);
    if (result.status === "answered") {
      state.call.status = "answered";
      state.activeDecision = false;
      state.business = result.receipt.choice === "accept" ? "confirmed" : "rejected";
    } else {
      state.call.status = "ready";
      state.activeDecision = true;
    }
  }
  function reduce(e) {
    if (e.type !== "run-start" && state.run === "not-started") throw Error("Run start required");
    switch (e.type) {
      case "run-start":
        fields(e.payload, []);
        if (state.run !== "not-started") throw Error("Run already started");
        state.run = "running";
        break;
      case "progress":
        fields(e.payload, ["text"]);
        text(e.payload.text, 300);
        state.progress = e.payload.text;
        break;
      case "snapshot":
        fields(e.payload, ["revision", "plan"]);
        if (state.revision !== null && e.payload.revision < state.revision) throw Error("Stale snapshot");
        projection(e.payload.plan, e.payload.revision);
        break;
      case "delta": {
        fields(e.payload, ["base", "revision", "patch"]);
        if (state.revision === null || e.payload.base !== state.revision || e.payload.revision !== state.revision + 1) throw Error("Missing/incompatible delta base");
        if (!Array.isArray(e.payload.patch) || e.payload.patch.length < 1 || e.payload.patch.length > 8) throw Error("Patch budget");
        const next = clone(state.projection);
        for (const p of e.payload.patch) {
          fields(p, ["op", "value"]);
          if (p.op === "replace-title") next.title = p.value;
          else if (p.op === "append-task") next.tasks.push(clone(p.value));
          else throw Error("Rejected patch operation");
        }
        projection(next, e.payload.revision);
        break;
      }
      case "args-start":
        fields(e.payload, ["tool"]);
        if (!id(e.payload.tool) || state.call) throw Error("Invalid/duplicate tool start");
        state.call = { id: e.payload.tool, status: "preparing", raw: "", bytes: 0, proposal: null };
        state.business = "pending";
        break;
      case "args-delta":
        fields(e.payload, ["tool", "chunk"]);
        if (!state.call || state.call.id !== e.payload.tool || state.call.status !== "preparing" || typeof e.payload.chunk !== "string") throw Error("Arguments lack current start");
        if (state.call.bytes + bytes(e.payload.chunk) > 4096) throw Error("Argument byte budget");
        state.call.raw += e.payload.chunk;
        state.call.bytes += bytes(e.payload.chunk);
        break;
      case "args-end": {
        fields(e.payload, ["tool"]);
        if (!state.call || state.call.id !== e.payload.tool || state.call.status !== "preparing") throw Error("Arguments lack current start");
        const proposal = JSON.parse(state.call.raw);
        if (proposal?.component !== "project-plan" || proposal?.version !== 1) {
          state.call.status = "unsupported";
          state.progress = "Unsupported component/version; read-only fallback.";
          break;
        }
        validateProposal(proposal);
        state.call.proposal = clone(proposal);
        state.call.status = "ready";
        state.draft = clone(proposal.plan);
        state.dirty = false;
        if (!history) {
          try {
            activate();
          } catch {
            state.activeDecision = false;
            note("decision-unavailable", "current-owner-recheck");
          }
        }
        break;
      }
      case "tool-result":
        fields(e.payload, ["tool", "summary"]);
        if (state.call?.id !== e.payload.tool) throw Error("Unknown result tool");
        text(e.payload.summary, 300);
        state.call.reportedResult = e.payload.summary;
        state.activeDecision = false;
        state.business = "unverified-result";
        break;
      case "run-end":
        fields(e.payload, ["outcome"]);
        if (!["success", "interrupt", "cancelled", "error"].includes(e.payload.outcome)) throw Error("Unknown terminal outcome");
        state.run = "reported-" + e.payload.outcome;
        if (["cancelled", "error"].includes(e.payload.outcome)) state.activeDecision = false;
        break;
    }
  }
  function accept(e, { repair = false, fromSeq = e.seq } = {}) {
    ensure();
    if (scopeKey(e.scope) !== scopeKey(current)) {
      note("ignored", "foreign-scope");
      return "ignored";
    }
    const signature = canonical(e);
    if (seen.has(e.id)) {
      if (seen.get(e.id) !== signature) {
        fail("conflicting-delivery-id");
        return "repair-required";
      }
      return "duplicate";
    }
    if (!repair && (!state.synced || fromSeq !== state.nextSeq)) {
      fail("delivery-gap");
      return "repair-required";
    }
    try {
      if (repair) {
        owner.canRead(current);
        if (e.type !== "snapshot" || e.seq < state.nextSeq - 1) throw Error("Invalid repair snapshot");
        if (state.revision !== null && e.payload.revision < state.revision) throw Error("Stale repair");
      }
      reduce(e);
      state.nextSeq = e.seq + 1;
      seen.set(e.id, signature);
      if (seen.size > 128) seen.delete(seen.keys().next().value);
      if (repair) {
        state.synced = true;
        state.repair = null;
      }
      note(e.type, "applied");
      return "applied";
    } catch (error) {
      if (state.call?.status === "preparing" && e.type.startsWith("args-")) state.call.status = "invalid";
      fail("rejected-event");
      return "repair-required";
    }
  }
  return {
    get state() {
      return clone(state);
    },
    get scope() {
      return clone(current);
    },
    ingest(raw) {
      try {
        return accept(decodeEvent(raw));
      } catch (error) {
        fail("invalid-envelope");
        return "repair-required";
      }
    },
    consume(packet) {
      if (typeof packet === "string") return this.ingest(packet);
      if (!packet || packet.kind !== "progress-range" || packet.last.type !== "progress" || packet.last.seq !== packet.to || !Number.isSafeInteger(packet.from) || packet.from > packet.to) throw Error("Invalid display batch");
      return accept(packet.last, { fromSeq: packet.from });
    },
    repair(raw) {
      try {
        return accept(decodeEvent(raw), { repair: true });
      } catch (error) {
        fail("repair-rejected");
        return "repair-required";
      }
    },
    deliveryFailure() {
      ensure();
      state.transport = "closed";
      fail("delivery-overflow-or-failure");
      if (state.business !== "confirmed") state.business = "unknown";
    },
    eof() {
      ensure();
      state.transport = "closed";
      if (state.call?.status === "preparing") {
        state.call.status = "unknown";
        state.business = "unknown";
        fail("incomplete-arguments-at-eof");
      }
      if (!state.run.startsWith("reported-")) {
        state.run = "incomplete";
        state.business = state.business === "confirmed" ? "confirmed" : "unknown";
        state.activeDecision = false;
        note("eof", "terminal-unconfirmed");
      }
    },
    editPlan(plan) {
      ensure();
      if (!state.call?.proposal) throw Error("Complete proposal required");
      validatePlan(plan);
      state.draft = clone(plan);
      state.dirty = true;
    },
    resolveDraft(choice) {
      ensure();
      if (!state.call?.proposal || !["keep", "discard"].includes(choice)) throw Error("Invalid draft choice");
      if (choice === "discard") {
        state.draft = clone(state.call.proposal.plan);
        state.dirty = false;
      }
      state.conflict = false;
    },
    resume() {
      ensure();
      if (!state.synced || !state.call?.proposal) throw Error("Repair/complete proposal required");
      activate();
      return this.state;
    },
    decide(choice) {
      ensure();
      if (!state.synced || state.conflict || !state.activeDecision || state.call?.status !== "ready") throw Error("Complete current decision required");
      const proposal = { ...clone(state.call.proposal), plan: clone(state.draft) };
      validateProposal(proposal);
      try {
        const receipt = owner.decide(current, state.call.id, choice, proposal);
        state.call.status = "answered";
        state.activeDecision = false;
        state.business = choice === "accept" ? "confirmed" : "rejected";
        return receipt;
      } catch (error) {
        state.activeDecision = false;
        state.business = "unknown";
        throw error;
      }
    },
    reconcile() {
      ensure();
      if (!state.call?.proposal) throw Error("No complete operation identity");
      const receipt = owner.outcome(current, state.call.id, state.call.proposal.operation);
      if (receipt) {
        state.call.status = "answered";
        state.activeDecision = false;
        state.business = receipt.choice === "accept" ? "confirmed" : "rejected";
      }
      return receipt;
    },
    bindDecision() {
      const lease = generation, identity = scopeKey(current), tool = state.call?.id, proposal = canonical(state.draft);
      return (choice) => {
        if (disposed || lease !== generation || identity !== scopeKey(current) || tool !== state.call?.id || proposal !== canonical(state.draft)) throw Error("Expired decision handler");
        return this.decide(choice);
      };
    },
    switchScope(next) {
      ensure();
      const connection = current.connection + 1;
      validateScope({ ...next, connection });
      current = { ...clone(next), connection };
      generation++;
      seen = new Map();
      state = fresh();
    },
    dispose() {
      disposed = true;
      generation++;
      state.activeDecision = false;
    }
  };
}
// Complete JSON events only: framing and split UTF-8 decoding belong to the real
// transport. Only adjacent display progress may coalesce; semantic events retain order.
function createDeliveryQueue({ maxBytes = 32768, maxEvents = 64 } = {}) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 8192 || maxBytes > 1048576 || !Number.isSafeInteger(maxEvents) || maxEvents < 1 || maxEvents > 256) throw Error("Queue budget");
  const queue = [];
  let used = 0;
  return {
    push(raw) {
      const event = decodeEvent(raw), size = bytes(raw), last = queue.at(-1);
      if (event.type === "progress" && last?.event.type === "progress" && scopeKey(last.event.scope) === scopeKey(event.scope) && event.seq === last.to + 1 && last.to - last.from < 1023) {
        if (used - last.size + size > maxBytes) throw Error("Queue overflow; stop and repair");
        used += size - last.size;
        last.size = size;
        last.event = event;
        last.to = event.seq;
        last.raw = raw;
        return;
      }
      if (queue.length >= maxEvents || used + size > maxBytes) throw Error("Queue overflow; stop and repair");
      queue.push({ event, raw, size, from: event.seq, to: event.seq });
      used += size;
    },
    drain(consume) {
      while (queue.length) {
        const next = queue.shift();
        used -= next.size;
        consume(next.from === next.to ? next.raw : { kind: "progress-range", from: next.from, to: next.to, last: clone(next.event) });
      }
    },
    get size() {
      return queue.length;
    },
    get bytes() {
      return used;
    }
  };
}
export {
  SCOPE_KEYS,
  createDeliveryQueue,
  createEffectOwner,
  createSession,
  decodeEvent,
  validatePlan,
  validateProposal,
  validateScope
};
