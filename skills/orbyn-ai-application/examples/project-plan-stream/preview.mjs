import { createSession, createDeliveryQueue } from "./interaction.mjs";
import { fixture, event, raw, SCOPE, PROPOSAL } from "./fixtures.mjs";
const $ = (id) => document.getElementById(id);
let source = fixture(), session = createSession(SCOPE, source.owner), generation = 0, invalidForm = false, busy = false;
function status(message, error = false) {
  $("status").textContent = message;
  $("status").className = error ? "error" : "";
}
function render({ preserveInput = false } = {}) {
  const s = session.state, owner = source.owner.inspect();
  for (const key of ["transport", "run", "business"]) $(key).textContent = s[key];
  $("projection").textContent = `${s.synced ? "Synchronized" : "Repair required"} \xB7 revision ${s.revision ?? "none"}`;
  $("decision").textContent = s.call ? `${s.call.status} \xB7 ${s.call.bytes} argument bytes` : "No complete call";
  $("progress").textContent = s.progress || "No progress event received.";
  const plan = s.draft ?? s.projection;
  if (!preserveInput) $("title").value = plan?.title ?? "";
  $("title").disabled = busy || s.call?.status !== "ready" || !s.activeDecision;
  $("tasks").replaceChildren();
  for (const task of plan?.tasks ?? []) {
    const li = document.createElement("li");
    li.textContent = task.title;
    $("tasks").append(li);
  }
  const actionable = !busy && !invalidForm && s.synced && !s.conflict && s.activeDecision && s.call?.status === "ready";
  $("accept").disabled = $("reject").disabled = !actionable;
  $("resume").disabled = busy || invalidForm || !s.synced || !s.call?.proposal || s.call.status === "answered";
  $("replay").disabled = busy || invalidForm;
  $("repair").disabled = busy || s.synced;
  $("fallback").hidden = s.call?.status !== "unsupported";
  $("conflict").hidden = $("keep").hidden = $("discard").hidden = !s.conflict;
  $("record").textContent = `v${owner.record.version} \xB7 ${owner.record.plan.title}`;
  $("writes").textContent = `Business writes: ${owner.writes} \xB7 answered decisions: ${owner.answered}`;
  $("trace").textContent = JSON.stringify(s.trace, null, 2);
}
async function play(kind, { history = false, reuse = false } = {}) {
  const lease = ++generation, oldDraft = reuse && session.state.dirty ? session.state.draft : null;
  session.dispose();
  if (!reuse) source = fixture();
  session = createSession(SCOPE, source.owner, { history });
  invalidForm = false;
  busy = true;
  render();
  const queue = createDeliveryQueue(), events = structuredClone(source.events);
  if (kind === "patch") events[3].payload.patch[0].op = "unsupported-operation";
  if (kind === "unknown") {
    events[5].payload.chunk = JSON.stringify({ ...PROPOSAL, component: "unknown-view", version: 99 });
    events[6].payload.chunk = "";
  }
  try {
    for (const e of kind === "eof" ? events.slice(0, 6) : events) {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      if (lease !== generation) return;
      queue.push(raw(e));
      queue.drain((packet) => session.consume(packet));
      render();
    }
    session.eof();
    if (oldDraft && session.state.call?.proposal) session.editPlan(oldDraft);
    status(history ? "History displayed passively. Check the current pending owner before deciding." : kind === "eof" ? "Delivery ended mid-call. Replay complete fixture history to reconstruct it; no effect ran." : "Fixture delivered. Inspect each witness before deciding.");
  } catch {
    session.deliveryFailure();
    status("Delivery stopped; preserve the draft and request repair.", true);
  } finally {
    if (lease === generation) {
      busy = false;
      render();
    }
  }
}
$("start").onclick = () => void play($("case").value, { history: $("case").value === "unknown" });
$("replay").onclick = () => void play("complete", { history: true, reuse: true });
$("title").oninput = () => {
  try {
    session.editPlan({ ...session.state.draft, title: $("title").value });
    invalidForm = false;
    $("title").setCustomValidity("");
    status("Local draft changed. No business write.");
  } catch {
    invalidForm = true;
    $("title").setCustomValidity("A nonempty complete title is required.");
    status("Retain the edit and provide a valid title before deciding.", true);
  }
  render({ preserveInput: true });
};
for (const choice of ["accept", "reject"]) $(choice).onclick = () => {
  try {
    if (invalidForm) throw Error("Invalid visible draft");
    session.decide(choice);
    status(choice === "accept" ? "The simulated owner accepted this complete plan." : "The simulated owner recorded rejection; no business write.");
  } catch {
    status("The current decision was not confirmed. Preserve it and reconcile the owner.", true);
  }
  render({ preserveInput: invalidForm });
};
$("resume").onclick = () => {
  try {
    session.resume();
    status(session.state.call.status === "answered" ? "Another answer already exists; it remains read-only." : "Current authority/version permit this outstanding decision.");
  } catch {
    status("Pending decision unavailable or stale. No write ran; keep the draft.", true);
  }
  render();
};
$("repair").onclick = () => {
  session.repair(raw(event(20, "snapshot", { revision: 5, plan: PROPOSAL.plan })));
  status(session.state.synced ? "Projection repaired. Missing tool state still needs complete history and current resume." : "Repair unavailable; preserve the prior view.", !session.state.synced);
  render();
};
for (const choice of ["keep", "discard"]) $(choice).onclick = () => {
  session.resolveDraft(choice);
  invalidForm = false;
  render();
};
window.projectPlanFixture = { get state() {
  return session.state;
}, get owner() {
  return source.owner.inspect();
} };
window.addEventListener("pagehide", () => {
  generation++;
  session.dispose();
}, { once: true });
render();
