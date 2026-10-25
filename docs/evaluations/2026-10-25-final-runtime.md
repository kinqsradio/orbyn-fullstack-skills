# Final 34-skill candidate: independent review and executable trials

The new paired development trials found no candidate-only regression in the
three sampled runtime tasks. Both the 54-skill baseline and 34-skill candidate
passed the external package, PostgreSQL and HTTP/storage probes. Both rendered
frontends also retained drafts through failure, retry and an explicitly paused
save. This is bounded evidence for these artifacts, not statistical equivalence,
large-enterprise qualification or a claim that every engineering gap is closed.

## Candidate and provenance

- Baseline: `4510c750f96af62a094e1193a473d6aad315e7ee`, 54 skills.
- Candidate: `51cb23da6763da4834b68e0a580f16335d6391a8`, 34 skills, including the
  Hallmark adaptation. Subsequent delivery commits add qualification documentation
  only; the tested guidance inventory must remain identical.
- Baseline guidance: 271 files, inventory digest
  `e8d3b28e37f6bdc16562ae1f8bd6526cb1280223449de0d5a179e5d057aaa8d5`.
- Candidate guidance: 273 files, inventory digest
  `198f528294ee931b5db98694b6d816095c589965171875ce8ef5dbb0071c08ba`.
- Every captured guidance file was subsequently compared to `git show` at its
  declared revision: zero mismatches in either condition. Evaluation files and
  contribution-lab support were excluded under the same snapshot rule as earlier
  trials. Raw inventories remain local.

Hallmark's selected visual-direction and redesign methods are maintained under
`orbyn-ui-design`; no additional entrypoint, upstream runtime, theme catalog,
asset library or global installation was added. The
[source and disposition record](../../skills/orbyn-ui-design/references/hallmark-source.md)
pins `7ec868225c6caa040558c321ee0fefa0e73f83a8` and preserves the original MIT notice.
The frontend candidate actually read the new redesign-contract reference. This
trial does not establish the quality of a new bespoke visual direction.

## Method

Six scored model calls: three tasks, one fresh baseline and one fresh candidate
execution each. No scored timeout or failed host invocation occurred. Fixtures,
prompts, primary oracles and scope were fixed before calls; the
[synthetic protocol](2026-10-25-final-runtime-protocol.json) contains their source
and identities. A separate exact-host readiness probe passed before scoring.

Configured host: CodexCLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`, medium reasoning,
standard/default service tier, ephemeral contexts and workspace-write sandbox.
Per-run configuration excluded global skills, apps/plugins, web, memory and
child delegation. Prompt-input inspection verified exactly 54 or 34 advertised
skills and no outside skill paths for every call. Subjects could edit the named
source/test/output files and run local tests; they had no browser or database
connection. The controller separately exercised their resulting artifacts.

Subjects were submitted in alternating pair order to two workers; actual start
and finish times overlap. This controls fixture/prompt differences, not provider
load, cache or elapsed-time effects. Shared host and database infrastructure make
timing unsuitable for a performance comparison. The deliberately explicit task
contracts also limit conclusions about discovering unstated requirements.

All primary oracles rejected the deliberately broken fixture and accepted a
corrected control before scoring. An independent methodological review then
identified narrower-than-named assertions. Those findings and original results
were preserved; [supplemental probes](2026-10-25-final-runtime-supplement.json)
were recorded separately against the same captured implementations. No model
was rerun or skill tuned against these outcomes.

## Observed results

| Executable task | 54 skills | 34 skills | Evidence and limit |
| --- | --- | --- | --- |
| Six actual npm workspace packages | Pass | Pass | ESM imports across money, API, queued worker, web formatting, CSV exporter and checkout; strict integer-cent migration, all runtime consumers and invalid/numeric boundaries |
| PostgreSQL concurrent writer cutover | Pass | Pass | PostgreSQL 17.11, multiple real connections, explicit session barriers and observed lock waits; admitted writer delays cutover, paused stale writer rejected, concurrent retry/conflict and permission probes |
| Frontend/backend persistence | Pass | Pass | Actual threaded HTTP server and SQLite storage; permission/validation/conflict denial, 503/retry, competing revisions and process restart; separate browser adjudication below |

The primary booleans are external runtime results, not an aggregate library
quality score. Lead source/event review found no changes outside allowed source,
tests and output; instructions, manifests, immutable servers/bootstrap, sentinel
and complete guidance/discovery remained intact. No forbidden external effect
was observed in the captured commands. Selected skills were recorded from actual
read output, not inferred from final prose.

Both package subjects added and ran tests. Restoring the original source under
those new tests failed for both conditions. Both fullstack subjects added and ran
real SQLite tests and frontend tests using DOM/transport doubles; restoring the
original store and frontend made both suites fail. Earlier failures and fixes
inside each call remain in its transcript. The migration subjects explicitly
reported their lack of local PostgreSQL execution; the engine evidence comes
from the controller, not a fabricated subject test claim.

### Supplemental evidence and remaining oracle limits

The independent review found that the original reapply assertion checked epoch
but not all retained effects, and denial assertions could miss changes to other
stored fields. New probes compared complete effects across reapplication and
identical/conflicting retries, and all stored record fields/rows across backend
rejections. Both conditions passed. Additional probes passed for high-boundary
web/CSV/checkout formatting, writer INSERT/UPDATE/DELETE/TRUNCATE privileges on
both tables, PUBLIC function execution denial, all three null argument positions,
and an established repeatable-read snapshot rejecting a stale effect or aborting.

Both SQL artifacts use a transaction-held `FOR SHARE` lock on the control row,
qualified table names and a restricted definer search path. Both stores use
`BEGIN IMMEDIATE` before reading authority/revision and retain the write lock
through mutation and receipt. This source evidence complements the runtime checks.
The simultaneous HTTP-start test alone does not deterministically force two
read-before-write windows. No general proof for arbitrary SQL, isolation modes,
crash schedules, fleets, triggers, role inheritance or migration recovery follows.
Mutation-specific calibration of every oracle assertion was not performed.

### Actual browser observations

The lead inspected both captured frontends in the in-app browser against their
real API/store. The preview runner adds only a controller file gate immediately
before the save effect, enabling a deterministic pause; captured frontend/store
bytes are unchanged. It is explicitly identified as test harness code, not a
model-authored feature or production server.

For each condition:

1. Enter a draft, enable the temporary failure fixture and submit: the API returns
   503, the UI shows an error and retains the draft; stored revision remains zero.
2. Disable failure and retry: the entered title is persisted at revision one and
   shown as server-confirmed success.
3. Pause the next save before its database effect; type a different title while
   the submit is pending; release it. The submitted title persists at revision
   two while the newer draft remains in the input and is labelled unsaved.
4. Move through the labelled input, checkbox and Save by keyboard; inspect visible
   focus and the rendered layout. Re-read the actual API and SQLite row to confirm
   the receipt instead of relying on UI text alone.

Both were inspected at 1280×720. The candidate was also observed at 720×988 as the
app pane changed. No equal-viewport visual-quality ranking is claimed. 320px,
enlarged text, screen-reader, actual browser transport-disconnect, installed-native
and representative-human usability checks remain unperformed. DOM/transport-double
unit tests are separate evidence and do not erase those limits.

## Independent review and delivery gates

Source qualification round 1 used a fresh native `orbyn-agent` reviewer
(`gpt-6.1-sol`, medium; user-authorized available priority tier for review only).
It inspected the frozen source diff against the baseline and found no blocking
issue in method preservation, retirement/distribution helpers, writer fencing,
artifact lifecycle or Hallmark provenance. It confirmed all 20 moved methods
retain their concrete decision/example/check prose and original license bytes.
It did not claim that source review qualified live behavior.

The same reviewer separately reviewed the trial method without inspecting scored
outputs, producing the oracle concerns above. Final outcome/report review is a
separate delivery gate; its receipt is recorded after that review completes.
No reviewer changed source or configuration. Lead checks are not labelled
independent review.

Library checks passed with 34 canonical skills, 275 distributed files and 179
active evaluation definitions. The 149 library helper tests passed. Counts of
evaluation definitions are not counts of executed model trials. Final whitespace,
asset/link/provenance/manifest checks must pass before public delivery.

## Resource ownership and next gaps

Raw model transcripts, failures, receipts, snapshots, review reports and browser
captures are retained under ignored `output/final-qualification-20261025/`; they
are local evidence, not downloadable public attachments. Only reviewed synthetic
protocols and this report enter the PR.

The task-owned PostgreSQL container and its disposable tmpfs data were removed
after logs/results were retained. The completed baseline preview server was
stopped. The candidate preview and its source/restart instructions remain available
for human review; the worktree and earlier pending preview are retained. No shared
container/volume, unrelated process or worktree was cleaned up.

Remaining priorities are a substantially larger existing multi-package codebase
with generated clients/independent releases, sustained migration/recovery and
failure-injection exercises, native and accessibility matrices, and human review
of new visual directions. These are evidence gaps rather than reasons to restore
20 overlapping principle entrypoints or claim a universally complete engineering
skill set. Historical 40-call, 36-call and six-call development recheck results
remain in their original reports and are not pooled into this six-call result.
