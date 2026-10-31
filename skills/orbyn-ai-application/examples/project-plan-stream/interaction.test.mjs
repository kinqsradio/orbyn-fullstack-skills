import test from "node:test";
import assert from "node:assert/strict";
import { createEffectOwner, createSession, createDeliveryQueue } from "./interaction.mjs";
import { fixture, event, raw, SCOPE, PROPOSAL } from "./fixtures.mjs";
const feed = (session, events) => events.forEach((e) => session.ingest(raw(e)));
test("complete legitimate run supports edited acceptance at the actual simulated owner", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  assert.equal(s.state.run, "reported-success");
  assert.equal(owner.inspect().writes, 0);
  s.editPlan({ ...PROPOSAL.plan, title: "My reviewed project guide" });
  s.decide("accept");
  assert.equal(owner.inspect().writes, 1);
  assert.equal(owner.inspect().record.plan.title, "My reviewed project guide");
  assert.equal(s.state.business, "confirmed");
  assert.throws(() => s.decide("accept"));
  assert.equal(owner.inspect().writes, 1);
});
test("reject is a completed decision without a business write", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  s.decide("reject");
  assert.equal(owner.inspect().writes, 0);
  assert.equal(s.state.business, "rejected");
  assert.throws(() => s.decide("accept"));
});
test("partial and malformed complete arguments cannot execute an effect or leak raw diagnostics", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 6));
  assert.equal(s.state.call.status, "preparing");
  assert.throws(() => s.decide("accept"));
  const secret = "PRIVATE-RAW-ARGUMENT";
  s.ingest(raw(event(7, "args-delta", { tool: "proposal-a", chunk: secret })));
  s.ingest(raw(event(8, "args-end", { tool: "proposal-a" })));
  assert.equal(s.state.synced, false);
  assert.equal(owner.inspect().writes, 0);
  assert.ok(!JSON.stringify(s.state.trace).includes(secret));
  assert.throws(() => s.decide("accept"));
});
test("EOF without a terminal witness preserves a complete draft as unknown, then current resume works", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 8));
  s.editPlan({ ...PROPOSAL.plan, title: "Preserve this draft" });
  s.eof();
  assert.equal(s.state.run, "incomplete");
  assert.equal(s.state.business, "unknown");
  assert.equal(s.state.draft.title, "Preserve this draft");
  assert.throws(() => s.decide("accept"));
  s.resume();
  s.decide("accept");
  assert.equal(owner.inspect().record.plan.title, "Preserve this draft");
});
test("duplicate non-idempotent delta is not applied twice", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 4));
  assert.equal(s.state.projection.tasks.length, 2);
  assert.equal(s.ingest(raw(events[3])), "duplicate");
  assert.equal(s.state.projection.tasks.length, 2);
  assert.equal(s.state.synced, true);
});
test("gap and rejected patch retain readable state but require explicit authorized repair", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 2));
  const before = s.state.projection;
  s.ingest(raw(event(4, "delta", { base: 1, revision: 2, patch: [{ op: "append-task", value: { id: "x", title: "Must not apply across gap" } }] })));
  assert.equal(s.state.synced, false);
  assert.deepEqual(s.state.projection, before);
  s.repair(raw(event(10, "snapshot", { revision: 4, plan: PROPOSAL.plan })));
  assert.equal(s.state.synced, true);
  assert.deepEqual(s.state.projection, PROPOSAL.plan);
  s.ingest(raw(event(11, "delta", { base: 4, revision: 5, patch: [{ op: "execute-code", value: "unsafe" }] })));
  assert.equal(s.state.synced, false);
  assert.deepEqual(s.state.projection, PROPOSAL.plan);
  assert.equal(owner.inspect().writes, 0);
});
test("new snapshot preserves a dirty local draft and requires a deliberate conflict choice", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  s.editPlan({ ...PROPOSAL.plan, title: "My newer draft" });
  s.ingest(raw(event(10, "snapshot", { revision: 3, plan: { ...PROPOSAL.plan, title: "Remote proposal" } })));
  assert.equal(s.state.draft.title, "My newer draft");
  assert.equal(s.state.projection.title, "Remote proposal");
  assert.equal(s.state.conflict, true);
  assert.throws(() => s.decide("accept"));
  s.resolveDraft("keep");
  s.decide("accept");
  assert.equal(owner.inspect().record.plan.title, "My newer draft");
});
test("passive history cannot repeat a write or reopen answered approval", () => {
  const { owner, events } = fixture(), live = createSession(SCOPE, owner);
  feed(live, events);
  live.decide("accept");
  const replay = createSession(SCOPE, owner, { history: true });
  feed(replay, events);
  assert.equal(owner.inspect().writes, 1);
  assert.equal(replay.state.activeDecision, false);
  assert.throws(() => replay.decide("accept"));
  replay.resume();
  assert.equal(replay.state.call.status, "answered");
  assert.equal(owner.inspect().writes, 1);
  assert.throws(() => replay.decide("accept"));
});
test("pending history resume checks revocation, stale business version and another client answer", () => {
  const a = fixture(), history = createSession(SCOPE, a.owner, { history: true });
  feed(history, a.events);
  a.owner.grant(SCOPE.principal, false);
  assert.throws(() => history.resume(), /Denied/);
  assert.equal(a.owner.inspect().writes, 0);
  const b = fixture(), stale = createSession(SCOPE, b.owner, { history: true });
  feed(stale, b.events);
  b.owner.concurrentEdit({ ...PROPOSAL.plan, title: "Another writer" });
  assert.throws(() => stale.resume(), /Stale/);
  assert.equal(stale.state.activeDecision, false);
  const c = fixture(), first = createSession(SCOPE, c.owner), second = createSession(SCOPE, c.owner, { history: true });
  feed(first, c.events);
  feed(second, c.events);
  first.decide("accept");
  second.resume();
  assert.equal(second.state.call.status, "answered");
  assert.equal(c.owner.inspect().writes, 1);
});
test("replaced principal/thread/connection rejects old events and captured handlers while healthy new work works", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  const old = s.bindDecision();
  const next = { ...SCOPE, thread: "thread-b", run: "run-b", attempt: "attempt-b" };
  s.switchScope(next);
  assert.throws(() => old("accept"), /Expired/);
  assert.equal(s.ingest(raw(events[0])), "ignored");
  assert.equal(s.state.run, "not-started");
  const context = s.scope;
  owner.registerPending(context, "proposal-a", PROPOSAL);
  const fresh = fixture({ scope: context });
  feed(s, fresh.events);
  s.decide("accept");
  assert.equal(owner.inspect().writes, 1);
});
test("current authority is rechecked at commit even after presentation enabled the decision", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  owner.grant(SCOPE.principal, false);
  assert.throws(() => s.decide("accept"), /Denied/);
  assert.equal(owner.inspect().writes, 0);
});
test("lost effect reply reconciles existing operation without a second write", () => {
  const { owner, events } = fixture();
  const lost = { ...owner, decide(...args) {
    owner.decide(...args);
    throw Error("Simulated reply lost");
  } };
  const s = createSession(SCOPE, lost);
  feed(s, events);
  assert.throws(() => s.decide("accept"), /lost/);
  assert.equal(owner.inspect().writes, 1);
  assert.equal(s.state.business, "unknown");
  s.reconcile();
  assert.equal(s.state.business, "confirmed");
  assert.equal(owner.inspect().writes, 1);
});
test("unknown historical component has a non-executable fallback", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner, { history: true });
  const data = structuredClone(events);
  const proposal = JSON.stringify({ ...PROPOSAL, component: "untrusted-html", version: 99 });
  data[5].payload.chunk = proposal;
  data[6].payload.chunk = "";
  feed(s, data);
  assert.equal(s.state.call.status, "unsupported");
  assert.equal(s.state.activeDecision, false);
  assert.throws(() => s.resume());
  assert.equal(owner.inspect().writes, 0);
});
test("bounded queue coalesces only adjacent progress while preserving delta/tool/terminal semantics", () => {
  const owner = createEffectOwner(), s = createSession(SCOPE, owner), q = createDeliveryQueue({ maxEvents: 4 });
  q.push(raw(event(1, "run-start", {})));
  for (let seq = 2; seq <= 102; seq++) q.push(raw(event(seq, "progress", { text: "Display " + seq })));
  q.push(raw(event(103, "snapshot", { revision: 1, plan: PROPOSAL.plan })));
  q.push(raw(event(104, "run-end", { outcome: "success" })));
  assert.equal(q.size, 4);
  q.drain((packet) => s.consume(packet));
  assert.equal(s.state.nextSeq, 105);
  assert.equal(s.state.progress, "Display 102");
  assert.equal(s.state.run, "reported-success");
  assert.equal(s.state.synced, true);
  assert.equal(q.bytes, 0);
  const full = createDeliveryQueue({ maxEvents: 1 });
  full.push(raw(event(1, "run-start", {})));
  assert.throws(() => full.push(raw(event(2, "snapshot", { revision: 1, plan: PROPOSAL.plan }))), /overflow/);
  s.deliveryFailure();
  assert.equal(s.state.synced, false);
  assert.equal(owner.inspect().writes, 0);
});
test("UTF-8 argument bytes, malformed event and incompatible base are bounded failures", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 5));
  s.ingest(raw(event(6, "args-delta", { tool: "proposal-a", chunk: "\u{1F642}".repeat(1100) })));
  assert.equal(s.state.call.status, "invalid");
  assert.equal(s.state.call.bytes, 0);
  assert.equal(owner.inspect().writes, 0);
  const other = createSession(SCOPE, owner);
  assert.equal(other.ingest("{bad private JSON"), "repair-required");
  assert.equal(other.state.repair, "invalid-envelope");
  feed(other, events);
  assert.equal(other.state.synced, false);
});
test("authority denial does not misclassify a well-formed projection as a delivery gap", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  owner.grant(SCOPE.principal, false);
  feed(s, events);
  assert.equal(s.state.synced, true);
  assert.equal(s.state.activeDecision, false);
  assert.equal(owner.inspect().writes, 0);
  owner.grant(SCOPE.principal, true);
  s.resume();
  s.decide("accept");
  assert.equal(owner.inspect().writes, 1);
});
test("reported run success plus unfinished arguments remains unknown at EOF", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 6));
  s.ingest(raw(event(7, "run-end", { outcome: "success" })));
  s.eof();
  assert.equal(s.state.run, "reported-success");
  assert.equal(s.state.business, "unknown");
  assert.equal(s.state.call.status, "unknown");
  assert.equal(s.state.synced, false);
  assert.equal(owner.inspect().writes, 0);
});
test("account switch fences old display and decision handlers even when thread name repeats", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  const callback = s.bindDecision();
  s.switchScope({ ...SCOPE, principal: "person-b", account: "account-b" });
  assert.throws(() => callback("accept"), /Expired/);
  assert.equal(s.ingest(raw(events[1])), "ignored");
  assert.equal(s.state.projection, null);
  assert.equal(owner.inspect().writes, 0);
});
test("shape-valid JSON with invalid domain arguments cannot reach a write", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  const bad = structuredClone(events);
  bad[5].payload.chunk = JSON.stringify({ ...PROPOSAL, plan: { title: "Invalid duplicated task identity", tasks: [{ id: "same", title: "One" }, { id: "same", title: "Two" }] } });
  bad[6].payload.chunk = "";
  feed(s, bad);
  assert.equal(s.state.call.status, "invalid");
  assert.equal(s.state.activeDecision, false);
  assert.equal(owner.inspect().writes, 0);
});
test("conflicting delivery identity cannot be mistaken for a harmless duplicate", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events.slice(0, 2));
  const conflicting = structuredClone(events[1]);
  conflicting.payload.plan.title = "Wrong replacement";
  assert.equal(s.ingest(raw(conflicting)), "repair-required");
  assert.equal(s.state.synced, false);
  assert.equal(s.state.projection.title, "Draft plan");
  assert.equal(owner.inspect().writes, 0);
});
test("producer mutation after registration cannot rewrite the pending request or delivered proposal", () => {
  const mutable = structuredClone(PROPOSAL);
  const { owner, events } = fixture({ proposal: mutable });
  mutable.plan.title = "Mutated producer";
  const s = createSession(SCOPE, owner);
  feed(s, events);
  s.decide("accept");
  assert.equal(owner.inspect().record.plan.title, PROPOSAL.plan.title);
});
test("a retained handler cannot silently approve a later edited consequence", () => {
  const { owner, events } = fixture(), s = createSession(SCOPE, owner);
  feed(s, events);
  const old = s.bindDecision();
  s.editPlan({ ...PROPOSAL.plan, title: "A different reviewed consequence" });
  assert.throws(() => old("accept"), /Expired/);
  assert.equal(owner.inspect().writes, 0);
  s.bindDecision()("accept");
  assert.equal(owner.inspect().record.plan.title, "A different reviewed consequence");
});
test("new admitted attempt reconciles a lost reply by stable operation without another write", () => {
  const { owner, events } = fixture();
  const lost = { ...owner, decide(...args) {
    owner.decide(...args);
    throw Error("Simulated reply lost");
  } };
  const first = createSession(SCOPE, lost);
  feed(first, events);
  assert.throws(() => first.decide("accept"), /lost/);
  assert.equal(owner.inspect().writes, 1);
  const retryScope = { ...SCOPE, run: "run-retry", attempt: "attempt-b", connection: 2 }, retryTool = "proposal-retry";
  owner.registerPending(retryScope, retryTool, PROPOSAL);
  const retry = createSession(retryScope, owner, { history: true });
  const retryEvents = events.map((e) => ({ ...structuredClone(e), scope: retryScope, payload: e.payload.tool ? { ...e.payload, tool: retryTool } : e.payload }));
  feed(retry, retryEvents);
  const receipt = retry.reconcile();
  assert.equal(receipt.choice, "accept");
  assert.equal(retry.state.business, "confirmed");
  assert.equal(owner.inspect().writes, 1);
  assert.throws(() => owner.decide(SCOPE, "proposal-a", "accept", PROPOSAL), /not admitted/);
  assert.throws(() => owner.decide(retryScope, retryTool, "accept", { ...PROPOSAL, plan: { ...PROPOSAL.plan, title: "Changed payload" } }), /conflict/);
  assert.equal(owner.inspect().writes, 1);
  assert.equal(owner.decide(retryScope, retryTool, "accept", PROPOSAL).duplicate, true);
  owner.grant(retryScope.principal, false);
  assert.throws(() => owner.outcome(retryScope, retryTool, PROPOSAL.operation), /Denied/);
});

test("one admitted execution cannot bind two logical operations, even across expected versions", () => {
  const { owner } = fixture();
  const second = { ...PROPOSAL, operation: "different-operation", expectedVersion: 2 };
  const before = owner.inspect();
  assert.throws(
    () => owner.registerPending(SCOPE, "proposal-a", second),
    /already bound/
  );
  assert.deepEqual(owner.inspect(), before);
  assert.equal(owner.resume(SCOPE, "proposal-a", PROPOSAL).status, "pending");
  owner.decide(SCOPE, "proposal-a", "accept", PROPOSAL);
  assert.equal(owner.inspect().writes, 1);
  assert.throws(
    () => owner.decide(SCOPE, "proposal-a", "accept", second),
    /No current logical operation/
  );
  assert.equal(owner.inspect().record.version, 2);
  assert.equal(owner.inspect().answered, 1);
});

test("a retired execution cannot be recycled for another logical operation", () => {
  const { owner } = fixture();
  const retry = { ...SCOPE, attempt: "attempt-b", connection: 2 };
  owner.registerPending(retry, "proposal-retry", PROPOSAL);
  assert.throws(
    () => owner.registerPending(SCOPE, "proposal-a", { ...PROPOSAL, operation: "other-operation" }),
    /already bound/
  );
  owner.decide(retry, "proposal-retry", "accept", PROPOSAL);
  assert.equal(owner.inspect().writes, 1);
});

test("bounded execution admission refuses overflow without replacing the valid attempt", () => {
  const { owner } = fixture();
  let latest = SCOPE;
  for (let i = 1; i < 64; i++) {
    latest = { ...SCOPE, attempt: "attempt-" + i, connection: i + 1 };
    owner.registerPending(latest, "proposal-a", PROPOSAL);
  }
  const overflow = { ...SCOPE, attempt: "attempt-overflow", connection: 65 };
  assert.throws(
    () => owner.registerPending(overflow, "proposal-a", PROPOSAL),
    /admission budget/
  );
  assert.throws(() => owner.decide(overflow, "proposal-a", "accept", PROPOSAL), /not admitted/);
  owner.decide(latest, "proposal-a", "accept", PROPOSAL);
  assert.equal(owner.inspect().writes, 1);
});
