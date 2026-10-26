# Prototype, statechart and verification-drift qualification

26 October 2026. Local implementation and explicitly authorized paired model
experiments; no commit, push, PR, merge or deployment. The catalog remains 34.

## Outcome

The six development pairs and one separately frozen transfer pair completed.
Their core artifact/behavior outcomes were confirmed through lead review and
actual controller browser/checker/code execution. No candidate-only critical
regression was observed in those cases. Both conditions generally succeeded;
this is not evidence of a statistically established capability improvement.

The runs exposed repeated collisions in TLC's default timestamp-based state
directory. One method-file correction added distinct per-invocation outputs and
explicit checking-mode limits. A new focused pair on that final candidate
completed: baseline preserved isolated evidence and honestly reported the blocked
checker; candidate additionally completed safe → broken → safe with a supported
mode. A controller run confirmed the supplied models in both conditions.

There were **16 scored model calls** (eight pairs) and one unscored readiness call.
Every scored call completed within its five-minute budget, with an exact 34-skill
prompt inventory. Completion does not mean every requested tool succeeded.

## Frozen inputs and source identity

Baseline: `6a872049f92e46bc1c0f8f55143500429739d507`. Candidates were uncommitted
source snapshots, not invented Git revisions. Exact per-file inventories, public
synthetic fixtures, tasks and criteria are in the
[development protocol](2026-10-26-behavior-prototypes-protocol.json),
[transfer protocol](2026-10-26-behavior-prototypes-holdout.json) and
[focused follow-up](2026-10-26-behavior-prototypes-followup.json).

| Methods snapshot | Files, excluding eval material | Inventory SHA-256 |
| --- | ---: | --- |
| Baseline | 280 | `df2883e7b82011ff2f7a1d363bc62e1448e7baa0e68ce1921f29c001902aa6e0` |
| Initial candidate | 292 | `8932cdf12ad2950d2ee041d808be0b41163deac4db0e00a3a7edabf6ddf5f290` |
| Final candidate | 292 | `81b1d023aedf81b1b998f86e31dd73f5b83a67d912612d4237ba94bdde865959` |

Inventory digests hash compact JSON with sorted keys and separators `(',', ':')`.
The final candidate differs from the initial methods in only
`skills/tdd/references/formal-verification.md`, as pinned in the follow-up.
The seven original pairs were not silently reclassified as final-snapshot reruns.
All 186 existing evaluation cases, including their holdouts, remain unchanged;
seven new development cases and one new transfer case bring the suite to 194.

## Host, isolation and execution

Codex CLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`, medium reasoning, configured
`service_tier=default`, with fast/ultrafast disabled. Effective provider scheduling
was not independently attested. Explicit model experiments used the evaluation
guide's non-interactive path; they were not implementation delegation or an
independent review panel. Native delegation was not used because it could not
preserve the repository's standard processing selection.

Each condition received a separate disposable Git root, an archived/copied
`library/skills` snapshot and its own relative `.agents/skills` links. Evaluation
cases/rubrics were excluded from the subject library. Prompts, supplied product
files and tool capabilities matched within each pair. A task wrapper constrained
effects to the fixture and explicit installed tools. Product repair, unrelated
reads, downloads, installations, delegation, accounts and publication were excluded.

Per-run isolated host configuration disabled inherited global/system/plugin
skills, previous context, user/project instruction documents and unrelated
capabilities. Actual prompt inventories contained exactly the intended 34 local
skills before scoring. Disabling inherited documents was paired with the same
explicit fixture instructions in the task, not removal of task scope.
Configuration used a separate task-owned host home; existing authentication was
used without recording credentials or modifying user settings.

The command shape was:

```sh
codex exec --ignore-user-config --ephemeral --json --sandbox workspace-write \
  --model gpt-6.1-sol \
  -c 'model_reasoning_effort="medium"' \
  -c 'model_reasoning_summary="none"' \
  -c 'service_tier="default"' \
  -c 'approval_policy="never"' \
  -c 'web_search="disabled"' \
  -c 'project_doc_max_bytes=0' \
  --cd FRESH_FIXTURE -
```

The retained argv also disables fast mode, ultrafast mode, memories, multi-agent,
apps, plugins, hooks/plugin hooks, browser integrations, computer use, image
generation, tool suggestions and workspace-dependency discovery. Per-run
`skills.config` disables the actual global entrypoints and resolved paths;
inventory inspection verifies the result rather than assuming those flags suffice.
Only visible events, answers, tool output, termination, duration and reported
usage were captured; reasoning items were excluded. At most two study calls ran
at once, with alternating condition order in development pairs. Transfer and
follow-up calls ran sequentially after the preceding group.

Tools: Node `22.16.0`, Python `3.13.3`, Java `22.0.2`, TLC release jar `1.7.4`
(internal banner TLC2 `2.19`, 8 August 2024), task-local `pele@1.10.0`, existing
Playwright and Chrome `156.0.8078.47`. The jar checksum and dependency versions
are pinned in the protocols; no dependency was installed globally or vendored.

## Paired observations

“Confirmed” below includes the explicitly separate controller qualification;
it is not a claim that each subject completed browser and exhaustive TLC runs.

| Scenario | Baseline | Candidate | Decisive observation |
| --- | --- | --- | --- |
| Small visual decision | Confirmed | Confirmed | Real HTML, usable edit/visibility/save/reset, no unnecessary formal tooling |
| Uncertain save | Confirmed | Confirmed | Real fixture HTTP effects, same-key retries, reconciliation and stale-response fence after reset |
| Host parking interleaving | Confirmed | Confirmed | `observe_idle → admit → park` violates the model rule and actual Python state |
| Drift from new writer | Confirmed | Confirmed | Unchanged covered host file did not hide the new admin writer; old model passes, updated model fails and actual code reproduces |
| Migration writer fence | Confirmed | Confirmed | Safe/broken/safe checks plus actual storage-command effects; stale rejection preserves prior events |
| Forget versus stale update/restore | Confirmed | Confirmed | Both command orders checked; removing the actual restore guard resurrects the body and is detected |
| Progress versus reachability transfer | Confirmed | Confirmed | Both preserve absent fairness assumptions and distinguish a completion path from universal eventual completion |
| Final checker-output isolation | Agent blocked; controller confirmed | Agent completed; controller confirmed | Separate run artifacts, safe/broken/safe results and correct mode/coverage interpretation |

The prototype controller exercised the actual HTML in Chrome against the unchanged
local Node HTTP fixture. For each condition it checked normal commit, lost reply,
same-key retry, reconciliation without another write, reset with transport
cancellation deliberately ignored, keyboard navigation and 360px containment.
Seven POST calls produced four effects across four logical saves, including
Chrome's transport retries; this is fixture idempotency evidence, not production
transaction correctness. Separate visual-screen checks exercised edit/save/reset
and 320px layout with doubled computed text sizes. That stress test is not native
browser zoom or accessibility certification. Screenshots were actually inspected.
Both host-chart previews were rendered and inspected; no horizontal overflow was
observed at the tested 1100px width. The candidate used the new Pele adapter;
baseline supplied an explicitly hand-authored SVG alongside Mermaid source.

The controller ran normal TLC independently of the subject sandbox. Both old drift
models completed safely; both updated models violated `Protected` with a feasible
admin-writer trace. Both migration/forgetting safe models completed their finite
graphs, and each broken model violated its configured invariant. Both progress
models produced temporal counterexamples in a completed three-state graph check.
Direct imports of original Python entrypoints independently confirmed stale-write
rejection, preserved effects, forgotten-body rejection and admin parking violations.
Disposable actual-source guard removals reproduced stale appends and resurrection.
Twenty supplied input-file instances remained unchanged, excluding verification
files that the drift task explicitly authorized updating. Final method hashes
match the frozen final inventory.

## Failures retained and correction boundaries

- Subject browsers failed during Chrome launch, and the save fixture's listener
  was denied by its sandbox. Reports preserved those failures without claiming
  rendered or real-HTTP success. Later controller browser evidence is separate.
- Default subject TLC runs could not initialize an RMI listener. Some completed
  supported DFID checks; some reported sampled simulation/actual-code exploration
  and left exhaustive TLC blocked. DFID's lack of temporal checking was correctly
  distinguished from a liveness violation. The controller supplied normal TLC runs.
- Concurrent or rapid sequential TLC invocations sometimes collided in default
  timestamp directories. The final method correction requires distinct outputs,
  scope-preserving modes and interpretation of actual property results. The
  focused follow-up preserved all setup failures and completed its safe/broken/safe
  sequence on the final source; it did not overwrite the original study.
- An initial library test run rejected a stale manifest after cases changed.
  Regeneration corrected the inventory; the final full suite passed 155 tests.
- The first browser-controller assertions incorrectly expected focus to remain
  inside the page after tabbing past its last control and assumed no automatic
  POST retry. Their failed results and original script were retained. Corrected
  checks use a field-to-control Tab step and observed request-count deltas; the
  frozen task criteria were unchanged. No prototype fix was needed to pass.
- Direct standalone-SVG screenshot capture timed out once. The retained actual
  HTML chart previews subsequently rendered successfully. Earlier model/type,
  state-directory and test-expectation failures remain in local captures.

## Library checks and limits

155 unit tests passed, including four new renderer boundary tests. Actual Pele
rendering was also exercised. Library checks pass for 34 skills, provenance and
licenses, links, both generated host discovery trees, 194 cases and 295 distributed
skill assets. The `.mjs` adapter survives the existing skills-only distribution
checks. Existing SQLite ResourceWarnings remain warnings, not failing tests.

These are small synthetic fixtures on one configured model/host, with one run per
condition per case, reviewed by the implementing lead. They are not independent,
blinded, statistically powered, enterprise-scale, native-device or participant
usability qualification. Models use explicitly supplied atomic-command contracts;
they do not establish real database isolation, deployed writer retirement,
physical erasure or production scheduling. Routing/method reads and achieved
outcomes are separate observations; no keyword-only or self-reported success score
was used. The new transfer case was authored by the lead after the initial methods
freeze, not drawn from an independently sealed benchmark.

Raw visible captures, inventories, answers, failed attempts, screenshots and
controller receipts are retained locally in ignored `output/behavior-prototypes/`;
disposable fixtures are in ignored `repo/behavior-trials/`. They are not public
downloadable artifacts. Keep them while review/reproduction is pending and mark
their availability if intentionally retired. The retained human preview copy has
its own identity and resource receipt; a live local URL is not permanent hosting.
