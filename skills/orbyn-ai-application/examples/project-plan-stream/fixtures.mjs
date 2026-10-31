import { createEffectOwner } from "./interaction.mjs";
const SCOPE = Object.freeze({ principal: "person-a", account: "account-a", resource: "project-a", thread: "thread-a", run: "run-a", attempt: "attempt-a", connection: 1 });
const PROPOSAL = Object.freeze({ operation: "plan-operation-a", component: "project-plan", version: 1, expectedVersion: 1, plan: { title: "Publish an accessible project guide", tasks: [{ id: "draft", title: "Write the guide" }, { id: "check", title: "Check examples and keyboard flow" }] } });
function event(seq, type, payload, scope = SCOPE) {
  return { id: "event-" + seq, seq, scope: structuredClone(scope), type, payload: structuredClone(payload) };
}
function raw(e) {
  return JSON.stringify(e);
}
function fixture({ scope = SCOPE, proposal = PROPOSAL } = {}) {
  const owner = createEffectOwner();
  owner.registerPending(scope, "proposal-a", proposal);
  const source = JSON.stringify(proposal), cut = Math.floor(source.length / 2);
  const events = [event(1, "run-start", {}, scope), event(2, "snapshot", { revision: 1, plan: { title: "Draft plan", tasks: [{ id: "draft", title: "Write the guide" }] } }, scope), event(3, "progress", { text: "Checking the project brief\u2026" }, scope), event(4, "delta", { base: 1, revision: 2, patch: [{ op: "append-task", value: { id: "check", title: "Check examples and keyboard flow" } }] }, scope), event(5, "args-start", { tool: "proposal-a" }, scope), event(6, "args-delta", { tool: "proposal-a", chunk: source.slice(0, cut) }, scope), event(7, "args-delta", { tool: "proposal-a", chunk: source.slice(cut) }, scope), event(8, "args-end", { tool: "proposal-a" }, scope), event(9, "run-end", { outcome: "success" }, scope)];
  return { owner, events };
}
export {
  PROPOSAL,
  SCOPE,
  event,
  fixture,
  raw
};
