# Keep verification true to the code

Use after covered code changes, merges, refactors or a request to check whether a
model still describes the implementation. A green run of an old abstraction can
be stale evidence. Do not change product code in a drift-only task.

1. Find the real check and its property, coverage, source identity, configuration,
   bounds, assumptions, tools and last confirmed correspondence. Run it unchanged
   first. If no coverage record exists, mark the baseline uncertain; inspect the
   verification history as a starting point, not proof of correspondence.
2. Review all relevant changes since that identity, including uncommitted edits,
   renamed/moved functions, new callers/writers and changed dependencies that alter
   atomicity. An unchanged covered filename does not establish an unchanged system.
   Follow state ownership to newly introduced mutation paths.
3. Classify each change: no semantic effect; model/harness drift; an intentionally
   changed promise supported by owner-approved requirements; or a possible bug.
   A failing test alone does not establish that the promise was intentionally changed.
4. Update verification from the actual code before interpreting a rerun. Split a
   formerly atomic action when code introduces an await or releases a lock. Keep
   the property and bounds unless an intended change justifies a documented
   old/new contract. Never weaken either merely to obtain green.
5. Rerun. For a violation, replay the trace against real code and distinguish an
   impossible model step from a feasible product defect. For a pass, demonstrate
   that a relevant broken implementation variant is still detected, then restore
   and confirm baseline. Retain the original run and updated run separately.
6. Report **in sync**, **updated**, **bug**, or **blocked** per check. Updated and
   bug can both apply. Include changed source, trace/replay, negative control and
   unverified behavior. Advance correspondence only after inspecting that exact
   code/model pair; never advance a blocked check. Dirty code uses exact digests
   rather than a fabricated commit. Keep verification updates separate from a
   subsequently authorized product fix.

Example: an old model combines idle-check and park. A refactor separates them
with an await; a job can now be admitted between the two. The old model may pass.
After modeling both real actions, a counterexample may expose parking over live
work. Reproduce that ordering in the real controller before calling it a code bug.
Another change might leave the model stale without breaking the property; report
updated only after checking correspondence and failure sensitivity.

Maintained method adapted from the sources in [the source record](verification-source.md).

When a real-code replay reveals a defect, identify its introducing change when
practical, separately from the latest touched or correspondence-sync commit.
Follow scoped history through moves; report uncertain origin as unknown rather
than blaming the newest refactor. This history step does not advance blocked
correspondence or replace the current failing replay.
