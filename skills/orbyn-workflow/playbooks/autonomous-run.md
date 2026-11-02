# Autonomous delivery and recovery

Use for a requested autonomous task, independent PR queue, verified no-merge
handoff, dependent stack or standing program. These are endpoints within the same
workflow, not extra skills or authority. A short single task needs no queue file.
Use the existing task record, plan or tracker for goal, exclusions, endpoint,
items/dependencies, current owners, exact candidate heads, evidence, resources and
pending human decisions. Preserve the requested completion predicate through stalls.

## Select ready work

Reconcile actual source, dirty work, local/remote refs, PR state and live handles
before dispatch. Do not restart already merged items from stale notes. Select
only dependency-ready work; pass the actual upstream artifact/ref to a consumer,
not merely its task name. Keep independent work moving when another item is blocked.
An invalid shared premise suspends its dependent work, not unrelated slices.

Follow the [coordination boundary](../references/project-policy.md#delegation-and-host-configuration):
one lead, one child by default, never more than the resolved harness `max_children`, and no recursive delegates.
One coupled writer is sufficient. Complete a representative first unit through
its intended verification/endpoint before scaling a large queue; a trivial pilot
does not qualify materially different unit types. Refresh the brief after a pilot
exposes missing setup or evidence.

Each unit has one current writer and a last observed remote head/lease. Transfer
the current goal, exclusions, guidance, candidate, dependencies and allowed effects
explicitly on takeover. A foreign push stops dependent ref writes until reconciled;
even force-with-lease is unsafe with a guessed or stale lease. Preserve others' work.

## Observe and recover

Use supported process/task handles and inspect meaningful artifacts or log progress.
An observation timeout is not worker death. Reuse a live owned handle instead of
spawning a replacement. Distinguish waiting for a human, healthy long operation,
failed transport, dead worker and a supported stalled hypothesis. Assign a bounded
cause-specific retry/replacement budget; retain the failed attempt and constraints.
No silent provider/model fallback or lowered success target makes a run complete.

Account for every dispatched child: done, replaced, cancelled or scope absorbed,
with candidate/evidence and unresolved findings. Missing handoff is not success.
A late result must match the current owner/generation, head and dependencies before
integration; preserve a unique finding and recheck it against the new candidate.
Do not let an old writer overwrite a replacement. End-of-text or stream closure
is not a terminal run result; use the supported result/status and reconcile partial
effects before retry. Startup authentication failure means no run, while a terminal
run error can leave real partial work.

## Verify, deliver, repeat

Inspect the artifacts and changed contract, then run allowed checks. Independently
remeasure material numeric child claims at the same candidate, workload, units and
bounds using a reviewed command; discrepancies stay visible. Do not execute an
untrusted returned command or adopt an arbitrary tolerance. Preserve useful units
with authorized local checkpoints; local-only scope never implies remote backup.

Use [PR iteration](pr-iteration.md#dependent-stacks-and-current-context) for real
dependencies and current gates. A failed commit stops push/PR/CI acceptance. A
verified no-merge handoff names exact heads/bases, evidence and pending decisions,
then freezes further writes unless continued authority explicitly covers them.
Watcher wakes do not reopen that scope or authorize retarget, push or auto-merge.
A requested merge accepted into a queue is pending until terminal readback proves
its actual landing base and commit.

Classify each iteration as progress, verified wait, blocker or rejected hypothesis.
On plateau choose an evidence-led different mechanism, continue independent work,
or report the actual blocker; never relax the target or retry indefinitely. Pause
at the safe boundary on explicit stop, preserving dirty work/resources and next
action under [pause](pause-safely.md). Resume from actual current state.

## Close out each unit before expanding the queue

Apply the [task closeout decision](../../orbyn-worktree/references/task-closeout.md)
at the authorized endpoint before taking the next unit. Reuse owned task trees
and reference caches; do not multiply clones/worktrees per child, retry or timeout.
Account for held previews/evidence, later source and idle owned resources under
actual cleanup authority. A no-merge handoff can be terminal for this task while
its PR and resources remain open; record why and when that hold is reviewed.

Use the user/project-agreed storage/resource budget from actual inventory. If
expensive disposable copies would exceed it, stop creating them and continue
useful authorized low-storage/read-only work or report the bounded blocker.
Allocated directory sums are not reclaimable physical bytes. Do not invent a
threshold, delete caches to make room, stop foreign resources or install a janitor.
Retention triggers do not schedule work; future cleanup/monitoring needs its own
applicable authority and supported host capability.

## Persistence is a host capability

An active supported handle can continue while alive. An ended process cannot be
kept running by prose. A standing program uses supported host persistence or a
separately requested scheduler with task identity, wake/resume/cancel and quiet
unchanged-state behavior actually checked. Without that runtime, retain a durable
handoff and report persistence blocked; do not install a daemon or create chats.

Synthetic example: queue A and B are independent; C depends on A. B lacks a test
credential, so A can advance while B remains blocked. A's worker observation times
out but its handle is live; wait on that handle. If it later dies, transfer its
current constraints to one replacement and account for the old worker. A late old
patch cannot overwrite the replacement. C receives A's verified artifact, not a
stale task summary. At a no-merge endpoint both PRs remain unmerged despite a wake.
This example is guidance, not evidence that a host executed the lifecycle.

For multi-cause work, use [cause-to-work-item reconciliation](../../how/references/pipeline-diagnosis.md#cause-to-work-item-reconciliation): stable scoped identity, current remote readback, partial-write recovery and foreign claims. Routed remains unresolved; no automatic tracker writes or repeated routine approval stages.
