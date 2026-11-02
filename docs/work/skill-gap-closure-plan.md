# Skill gap closure plan

Status at final authoring freeze: **verified guidance and available checks complete; review PR awaited final independent review**. Prepared 28 October 2026. This plan addresses portable-method coverage, including small obligations and autonomous delivery, while keeping the nested workspace and current model defaults. The user subsequently selected “Verified guidance and available checks; list remaining qualifications openly in the PR.” Commit, push and a public review PR are authorized after final verification; merge is not authorized. Target installations, global configuration changes and real-service writes remain outside this candidate.

## Approved delivery endpoint

Deliver the A–I guidance and available verification as a review PR, with actual
source, fixture and host evidence distinguished and remaining qualifications
listed openly. Completing that authorized delivery does not assert that every
live behavior or integration in the original research scope is qualified. Every
one of the 211 observations keeps its evidence-level disposition; open requirements
are neither silently closed nor deleted to satisfy the endpoint. The replacement queue pair passed independent review (2 of 36 planned cells;
28 not run, 6 blocked by native-child settings). Final delivery checks and exact
candidate review remain prerequisites to publication. The user reviews the PR; no merge
or Orbyn target update is included. Anatomy/OpenCode integration remains a separate,
unimplemented proposal for the user's later review and manual planning.

The two passing queue cells are one synthetic repetition per condition. Both
baseline and candidate passed; no speed, efficacy, reliability or full live
qualification claim follows. Two prior invalid-protocol attempts remain separately
retained and do not count as scored failures or additional passing cells.

The original broad behavioral acceptance criteria below remain the standard for
any later full-qualification claim. They are not a prerequisite to this explicitly
selected, transparently scoped method-review delivery.

## Approved implementation scope

Implement the approved packages in coherent batches, retaining open evidence requirements. The recommended target is complete coverage of the applicable engineering behaviors in the pinned source, with concrete runtime evidence for the hosts and adapters we claim to support. Keep host products and external-service integrations visible as separate requirements. An absent integration is not closed by writing prose about it.

“No gap” means no unresolved **applicable, explicitly inventoried requirement** at the approved endpoint. It cannot mean that every future task, model response, platform or service is perfect. Unknown, blocked, partial and unrun requirements remain open. An exclusion or alternative implementation needs an explicit reason and review; it is not a passing test.

## Frozen evidence and completeness boundary

| Item | Identity / observation |
| --- | --- |
| Library baseline | `7a75684ad31b6a5d0ea3e6905b0868f7cc138301`; 35 canonical skill owners |
| Current upstream, rechecked during planning | [cursor/plugins `c742dd61706fbacc1b95f1a20b7b988cf096ce6c`](https://github.com/cursor/plugins/tree/c742dd61706fbacc1b95f1a20b7b988cf096ce6c), pstack 0.15.36 |
| Previous full review | `519d36aa98955bf680db01bcde5fdfba686dc901`, pstack 0.15.34 |
| Original source/import pin | `74dd2291e8e37b12fd6dc49b2acbd655c6bdaf12`; remains unchanged by research |
| Download integrity | Complete 2,037-file Git archive and source-byte SHA-256 receipts in ignored local research |
| Entrypoint scope | 58 top-level pstack + 3 nested Benny + 47 other top-level plugin + 7 third-party skill entrypoints = **115** |
| Catalog boundary | 108 third-party plugin manifests, 101 without a skill entrypoint; generated harness copies are not independent capabilities |
| Current pstack delta | No new entrypoint; 22 modified and 7 deleted files. The orchestration CLI/store was deleted upstream and is not a backlog dependency |
| Closure register | [211 atomic observations](skill-gap-closure-register.json), including overlaps, equivalents, deliberate differences and integrations; not 211 missing skills or observed defects |

The register gives each observation a pinned source path/line, current local owner/line, exact limitation, proposed change and positive/negative case. It contains 79 general-method observations, 41 workflow/tooling observations, 77 other-plugin observations and 14 Benny intake/adapter observations. Root review reclassifies already-present broad principles as specificity refinements and the log initializer as a conditional investigation, rather than inflating missing-skill or proven-bug counts. Related observations can close through one coherent owner patch.

All 115 entrypoints were inventoried and read. Material method references, workflow playbooks and selected helper contracts/tests were inspected. Source paths/hashes are accounted, but large compiler/orchestration implementations, generated/golden/test corpora, assets and third-party service bodies were **not all audited line by line or executed**. Thus there is no defensible claim that all possible source defects or behavioral gaps have already been found. Package H explicitly resolves the evidence needed for any selected executable integration; subsequent discoveries update the same register.

Local raw evidence is under the primary checkout's ignored `orbyn-references/cursor-plugins-refresh/`: complete snapshots and receipts, complete entrypoint mapping, `deep-method-audit.json`, `deep-workflow-audit.json`, `deep-other-audit.json`, `deep-benny-audit.json` and the previous comparison. These are local access pointers, not committed runtime dependencies or public attachments. This plan and its register are task-specific review artifacts, not a mandatory agent runtime schema.

## Constraints that remain fixed

- Shared methods stay in outer `skills/`; independent target repositories/worktrees remain under ignored `repo/`. No copied, linked or synchronized shared-skill installation into targets.
- Keep 35 canonical top-level owners unless a genuinely distinct unsupported task later earns a separately reviewed owner. Use conditional sections/references for the proposed improvements.
- Keep the resolved harness tiers and effort (the lead, worker and scout agents and their defaults). Preserve standard processing, actual consumer policy, no more active children than the resolved `max_children` and no recursive delegation. No hidden CLI inference or automatic model/provider fallback.
- Read required instructions explicitly in the selected target; use shell `rg`/`rg --files` when usable and accept native search. Instruction lookup is separate from code filtering, including hidden/ignored instruction paths.
- Preserve target instructions, company skills, private data, unrelated edits, active resources, licenses and original import history. Raw source stays ignored. Required offline guidance must not depend on that ignored download.
- Local work, commit, push, PR, review posting, merge, scheduling and deployment retain their actual authorization. A promise of autonomy supplies no additional effects.

## Packages and intended owner changes

The package letters describe implementation sequencing, not nine new skills or a required PR count. Keep one authoring candidate. Split independent delivery only when each diff has a useful review boundary; do not make one large unreviewable bulk change or one PR per sentence.

| Package | Concrete coverage | Existing owners / expected files | Completion evidence |
| --- | --- | --- | --- |
| **A. Reconcile scope and freeze** | Validate all 211 records against current main, map overlapping obligations, retain equivalents, explicit differences, blocked integrations and invalid hypotheses; connect every record to a package/case | This register; upstream-review; skill-creator; catalog/provenance only when actual owned content changes | No orphan entrypoint/path or applicable obligation; each disposition has a reason and evidence requirement; exact candidate/file allowlist |
| **B. Autonomous delivery and recovery** | Single-task autonomy, independent PR queue, no-merge handoff, dependent stacks, ready-unit dispatch, first-unit pilot, current owner/lease, complete child accounting, liveness, bounded retries, late results, pause/resume, truthful terminal state | Workflow routing; autonomous-run; coordination/handoffs/task-record; opening-a-PR/PR-iteration. One conditional autonomous-delivery reference if required for clarity | Disposable real source/Git/forge fixtures plus host execution of the scenarios below; correct output/refs and preserved failure evidence |
| **C. Verification and review** | Non-formal launch/doctor/drive/evidence/cleanup adapter; cold readiness; stable handles; action plus persisted result; honest dry-run effects; alternate entrypoints; fixture reset; map/index maintenance; doctor/reset/re-drive; executable adversarial receipts; baseline attribution; reviewer traversal and history tree preservation | Project-verification; verification-map; interrogate; engineering-scope; PR-iteration/opening-a-PR | Actual app/CLI adapter fixture and negative controls; lead reruns supported findings; source-proven risks remain labeled; independent exact-candidate review |
| **D. Discovery, CLI/UI and change proof** | Falsify load-bearing safety assumptions; pin behavior before consequential refactor; generic CLI inputs/help/output/errors/retries; real PTY waits/resize/signals; positive UI identity/fresh snapshots; Figma node/assets/primitive/token intake; immutable visual baselines and meaningful image diffs; queryable/source-mapped trace evidence | How impact/reproduction; architect/language guidance; refactoring; runtime/trace-forensics; visual-parity/UI-design. One portable CLI reference is a likely justified addition | Controlled CLI/TUI/UI fixtures, dynamic-consumer/mixed-version controls, Figma/reference example, visual mismatch and noise controls; same-surface limits explicit |
| **E. Sustained optimization and evaluation integrity** | Hillclimb route; decision/noise/correctness/budget before runs; sensitive frozen workload/harness; tune adoption competitors; work/error counts; physical/end-to-end plausibility; one hypothesis, keep/reject and plateau; candidate/judge blinding and leakage checks | Performance playbook; evaluation guide/evaluator only if a demonstrable helper change is needed; AI-application evaluation handoff | Known faster/slower/empty/error workloads; correctness-regression control; leaked-rubric/metadata negative control; preserved rejected trials; honest inconclusive result |
| **F. Explanation, recall and learning from work** | Introducing-change/history search; discussion/retention/schema/sampling boundaries; bounded asynchronous historical queries; missed trigger versus body gap versus execution failure; lucky success; historical-error negative controls; conflicting preference confidence; professional-depth prompt refinement; scoped multi-chat recall; every pending human decision; technical document/teaching purpose; work recaps; simpler total types and log ownership | Why; reflect/skill-creator; automate-me; plan/research; show-me-your-work/handoffs; how/unslop/engineering-scope; language guidance | Synthetic selected-history/recall corpus and authored-work fixture; expected decisions/results; no capture or cross-workspace scan; procedure usable from fresh context; log change only after reproduction |
| **G. Voice, teaching and video output** | Provider-neutral audio gesture/lifetime, formats, turn/barge-in, transcript finalization, batch/stream choice, player/chunk/cache identity and redacted diagnostics; deliberate-practice roadmap/retrospective; real subtitled catch-up video with reading holds and frame inspection | AI-application/UI/backend for speech; existing coaching/how owner for curriculum (linked from F); social-preview conditional video reference with engineering catch-up handoff | Disposable audio state/format/turn fixtures plus actual permitted audio surface before support claim; generated video/frames/hold measurement; no external speech provider change or unrequested capture |
| **H. Optional executable and service adapters** | Statechart compiler/rendering; native PR watch/stack equivalent; host wake/resume; issue-to-thread/tracker intake and compensation; existing-fix verification; Canvas/SDK/plugin/service contracts | Existing formal verification, CI/workflow, backend/AI tool-effects, setup/upstream ownership; actual application adapters stay with consumer | Capability-by-capability source/runtime contract and tests. No script imported solely for name parity. An unavailable service/tool remains open or an explicitly approved product exclusion |
| **I. Qualification, delivery and drift closure** | Full obligation/case mapping, supported-host readiness and matched trials, independent review, unchanged scope/defaults, source attribution and terminal library checks | Existing evaluator/execution lab, library checks, source records and this register | All selected applicable rows have the evidence level their claim needs; failures/blocks visible; final exact allowlist and actual local/commit/PR/merge state |

Existing equivalents are preserved and regression-checked rather than rewritten. Small source-derived refinements do not automatically require a new helper or model run. A missing callable integration cannot be “fixed” by a longer skill description.

## Autonomous delivery contract to implement in B

Keep one concise task record with the goal, exclusions, delivery endpoint, items/dependencies, current owners, candidate heads, evidence, owned resources and unresolved decisions. Reuse an existing plan/PR/tracker. No orchestration database or permanent service is required.

The agent selects the endpoint from the request:

1. **Autonomous task:** reach the actual requested artifact/behavior and evidence.
2. **PR queue:** build and verify independent items; publish/merge only where granted.
3. **Verified handoff:** produce verified PRs and stop at the specified heads without merge/auto-merge. Clearly freeze writes at handoff unless continued scope says otherwise.
4. **Dependent stack:** create a real base graph only for actual dependencies; land only an authorized contiguous verified prefix, or hand it off intact.
5. **Standing program:** use the same bounded native methods and durable state when work spans contexts; do not import cloud fleets, recursive coordinators or a scheduler by default.

For each iteration: reconcile actual state → select ready work → dispatch with current goal/instructions/effects → inspect artifacts → verify the changed contract → deliver within the endpoint → record progress or blocker. A wait requires a real live handle; a timeout is not death. A stale or late result is checked against current ownership/head/dependencies. A failed prerequisite stops dependent push/PR/merge actions. Never lower the success condition to call incomplete work done.

The following are separate acceptance cases, not just prose checklists:

| Case | Required observation |
| --- | --- |
| Independent queue with one blocked item | Other independent item advances; blocked item remains visible, not silently complete |
| Dependent stack with unverified middle | Verified upper work cannot carry the unverified middle into trunk |
| No-merge handoff followed by watcher wake | No merge, auto-merge, push or retarget outside frozen handoff scope |
| Observation timeout with live worker | Same owned handle inspected; no duplicate replacement based only on timeout |
| Dead/stalled worker and replacement | Cause/budget recorded, constraints consolidated, terminal child accounting complete |
| Late old-worker result | No overwrite of newer work; unique finding rechecked at current candidate |
| New caller/base with same patch identity | Relevant evidence refreshed; patch-id alone does not preserve verdict |
| Foreign remote push/changed lease | Preserve it and reconcile; no blind force overwrite |
| Restart with dirty work and already merged item | Resume next unfinished work from actual source/PR/process state |
| Explicit pause/stop | No new task mutation after safe boundary; preserve resources/patch and next action |
| Failed commit followed by attempted delivery | No push of unchanged baseline, PR or acceptance of unrelated CI |
| Merge command returns queued/auto-enabled | Report pending, not merged; verify actual trunk base and terminal readback |
| Unsupported host capability | Clear blocker and preserved work; no provider/default change or fake completion |
| Plateau/no progress | Revised evidence-led hypothesis or honest blocker; no goal relaxation or infinite unbounded retry |

## Tool and integration scope in H

Close these by explicit capability outcomes, not by copying the whole Cursor repository:

- **PR watch:** first qualify supported native watch plus complete current snapshots and pagination. If it supplies the required result, it is the accepted functional implementation. If it does not, specify and review a thin missing adapter. Test empty/unknown gates, lost handles, fork identity, changed head, queued versus merged, deadline and stack-frontier transitions.
- **Compiler/renderer:** use a selected pinned optional tool, preserve MIT attribution and qualify actual prerequisites/configuration/property outputs, projection validity, chart budgets, trusted executable views, signals and output preservation. Run the relevant upstream compiler/config/parser/process corpus and read skips; the previous bounded qualification is not a blanket pass. Keep model verdict, projection, source correspondence and real-code replay separate. A licensed shipped tool must have a real owner and source manifest; an essential method cannot depend on ignored raw research.
- **Benny-style intake:** propose a consumer-owned adapter for immutable source identity, trusted verdict actor, child effect isolation, conservative duplicate classification, tracker compensation, one-reply/readback and stop semantics. Prove it first with disposable fake Slack/tracker services and a real controlled application. Enabling real traffic needs a specified consumer, actual provider tools/credentials and authorized external effects; do not imply those exist now. Existing-fix verification produces confirmed/insufficient/inconclusive outcomes without racing the owner. Do not copy shared pstack skills into targets.
- **Host persistence:** a supported active process/watch or separately requested scheduler must actually resume/cancel the right task. Prose cannot keep an ended process running. Preserve quiet unchanged-state behavior and user stop.
- **Canvas, SDK, plugin and external services:** reusable interface/lifecycle/evidence guidance belongs in current owners. Actual Cursor Canvas/cloud APIs and the 108 service catalog entries are provider products, not interchangeable skill prose. Record existing external owners/capabilities and version/auth uncertainty. Google artifact methods already have external connected owners in this host. If literal integration parity is selected, implement and qualify that integration separately; until then it remains open, not core-method completion.

Preserve deliberate differences: no automatic learning hook, unbounded Ralph loop, arbitrary comment/line counts, deletion-first comments, blanket no-draft PR rule, universal type-branding or global model fallback. Upstream also contains practices weaker than ours, including forced cleanup and assumptions about untracked scratch. Equivalence is measured against the approved behavior and safety contract, not literal wording.

## Verification sequence and evidence levels

1. **Scope and source audit:** validate source/current-owner anchors and complete case membership; independently challenge each claimed gap and eliminate duplicates/equivalents. Inspect real target-owned policies before consumer execution.
2. **Static/library checks:** links, catalog/discovery, licenses/provenance/import pins, manifest and evaluation definitions. Keep all 263 previous case objects/holdouts unchanged; add development cases only where the contract changes. Run the relevant required checks from CONTRIBUTING, including library validation, Python tests and Node record validators when their CI gate applies.
3. **Executable fixtures:** extend the existing contribution/pipeline labs and focused tools where needed. Use actual source, Git refs and controlled UI/CLI processes. Every new helper needs a discriminating bad input and legitimate control; a prose change need not acquire an implementation-mirroring test.
4. **Host readiness:** record installed host/model/effort/processing, actual tool availability and permissions for Codex, Claude Code and OpenCode. Use supported task-local state/config isolation and synthetic nested targets. Never chmod global auth, replace defaults or silently switch models to obtain a pass. Missing auth/capability is a blocker. The prior OpenCode failures and unrun child trial remain historical/unverified until a fresh supported run succeeds.
5. **Candidate qualification:** observe actual child/tool/read events, artifacts and effects. Include `rg` availability in the child, native grep, no-match exit 1, unavailable-tool fallback, hidden/ignored instructions, individual code/worktree roots and sibling exclusion. Host file reads do not prove model-request inclusion or runtime enforcement; claim only what the host exposes.
6. **Matched behavior pilot:** freeze task/fixture/tool protocol before trials, use fresh contexts and neutral labels, keep rubrics/judge metadata out of candidate scope, retain failures/timeouts, and use actual output/effects rather than self-report. Distinguish instructed compliance qualification from blind natural-task behavior. Suggested first batch: six diagnostic scenarios × baseline/candidate × three repetitions = **36 host trials per host**, not36API requests. Start with one host; expand to the other two only once their readiness and scope are confirmed (108 total if all three complete). This is a diagnostic pilot, not a reliability guarantee or model ranking.
7. **Independent and final review:** the researcher reviews Builder's actual diff and artifacts; a reviewer of their own edits is not independent. Recheck affected callers and exact source/head after fixes; no mandatory panel or model-family change. Use holdouts only after candidate freeze. Audit every applicable requirement and claimed exclusion before delivery.

Six initial pilot families: independent/autonomous queue; dependent/no-merge stack; worker interruption/late result/resume; app verification/adversarial false-positive control; child search/instruction scope; noisy benchmark/evaluation leakage. Domain video/audio/provider adapters receive their own concrete checks from the register; success on the six families does not qualify them.

## Closure, review and rollback

For each applicable observation, record the final owning change or existing-equivalent evidence, linked positive/negative case, actual candidate and evidence level. Useful states are planned, source-covered, fixture-qualified, host-qualified, blocked, equivalent-with-evidence and intentionally excluded with reviewed rationale. These are audit labels in this task, not a mandated runtime state framework.

A row closes only at the evidence level of the claim: source text can close written guidance, helper fixtures can close the exercised helper contract, actual host events can close the observed host behavior, and a real provider run can close that integration's exercised path. An unsupported or unexecuted component never counts passed. Do not collapse these levels into a single percentage.

Final acceptance requires:

- Every one of the 115 entrypoints and every material helper family has an explicit disposition; every applicable atomic obligation has an owner and evidence.
- No unsupported essential reference, duplicate owner, source-pin relabeling, target installation, model-default change or leaked private material.
- Applicable package behavior and controls actually pass at the delivered candidate. Required repository checks pass, including any new helper's failure/recovery tests.
- All blocked/unrun/integration exclusions visible. A claim of full approved-scope completion is withheld while an applicable required row remains open.
- New discoveries update this register and affected scope; they do not disappear because the first list had a fixed count.

Build in reviewable batches and retain the last verified candidate. On regression, revert only the owned failing batch and preserve prior evidence, dirty user work and unrelated changes. No branch/worktree deletion, broad clean, force reset, provider install or production effect is a recovery shortcut.

After this plan is approved, use one Skills Builder authoring owner and the researcher as independent verifier. Ask Builder to implement the selected batch, inspect and correct it, then qualify the exact candidate. Publication/merge must follow the actual delivery authority at that time. Implementation is assigned to one Skills Builder authoring owner; independent verification remains separate.
