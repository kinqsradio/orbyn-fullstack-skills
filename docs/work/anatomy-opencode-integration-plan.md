# Anatomy and engineering-method integration

Status at authoring review checkpoint: **corrected-scope source implementation prepared; qualification is partial**. Updated 28 October 2026. Baseline A–I is merged at `933dd9db93c98382f1e451f7a62198a8458d5cc6`. The user explicitly wants engineering methods learned from OpenCode, not OpenCode usage/host integration. Local implementation and verified commit are authorized after independent clearance; push, PR and merge are not authorized.

The selected planning endpoint is the reusable engineering methods evidenced by OpenCode and Anatomy executable authoring workflow. Core SVG is a milestone; React, capture/drive, print, WebGL and documented beta 3D remain required for the full endpoint. Delivery uses six bounded packages: existing-owner engineering-method refinements; test reliability; localization/UI semantics; technical illustrations; maintained illustration executables; and small runtime/research refinements. Most changes belong to existing owners. One narrowly triggered technical-illustration owner is added for the selected figure-creation endpoint. Wholesale installation of either repository would add conflicting instructions and effects without proving capability.

## Decision and coverage boundary

“Fully integrated” should mean every **selected applicable requirement** has a maintained owner, reachable offline guidance, a concrete acceptance case and evidence at the level claimed. It does not mean importing every command or declaring every platform supported. A renderer, browser driver, host subagent or service remains unqualified until exercised on its supported surface. A deliberate exclusion retains its reason; it is not a passing result.

The [127-observation register](anatomy-opencode-gap-register.json) contains 44 Anatomy and 83 OpenCode observations, including ten cross-stack instruction syntheses. These are not 127 missing skills or measured failures. Each row records pinned evidence, current/proposed ownership, A–I overlap where identified, a positive case and a countercase. Package assignments are planning groups, not new skills. New discoveries can extend the register.

The initial research baseline was library `7a75684ad31b6a5d0ea3e6905b0868f7cc138301` with 35 canonical owners. The initial source reconciliation used the then-frozen, uncommitted A–I candidate identified by file-map SHA-256 `02c5e628ee107d9f679e11d236a47ce55de0621c1c3239c8a143047bd9be6dcc`, rooted at that same baseline. All 54 candidate files were checked against their receipt. This was the evaluated source identity. A–I subsequently merged as `933dd9db93c98382f1e451f7a62198a8458d5cc6`; all 280 guidance anchors across 47 owner files were rechecked against merged main and still match. Only delivery/evidence documentation differed from the evaluated source. The implementation baseline is now that merged commit. Revalidate any later drift before implementation.

### What remains after A–I source reconciliation

Every register row now includes `candidate_reconciliation` with exact candidate
anchors, a residual requirement and evidence limits. The 280 anchor ranges were
checked; unchanged owner files also match the baseline Git objects. All original
127 observation records and their source findings are preserved.

| Primary disposition | Anatomy | OpenCode | Total | Minimal response |
| --- | ---: | ---: | ---: | --- |
| Equivalent written method | 3 | 17 | 20 | Retain the owner; add no duplicate general policy |
| Specificity remains | 18 | 38 | 56 | Consolidate related refinements in conditional references/examples |
| Host/domain integration remains | 21 | 25 | 46 | Versioned host qualification or selected illustration support |
| Deliberate exclusion | 2 | 3 | 5 | Preserve the reason and Orbyn's boundary |

These are primary planning dispositions, not pass rates or counts of missing
skills. An equivalent verification rule can still have an unqualified optional
renderer or host adapter; its residual field retains that distinction. The 56
partial rows do not call for 56 paragraphs or 56 new tests. Shared assertions may
cover related requirements when they actually discriminate those requirements.

The remaining OpenCode-derived work is engineering-method specificity and
precise testing/localization examples; no product usage/host profile is selected. The substantial Anatomy capability gap is
model-driven technical illustration and its selected executable support. Generic
negative controls, bounded-evidence claims, import authority, nesting and explicit
memory already have owners. This reconciliation therefore reduces duplication
without treating unread implementation bodies or unperformed runtime checks as
covered. Before adopting a selected helper or host path, inspect its full relevant
dependency/execution closure; the source-scope limits below remain in force.

| Source | Pinned revision | Reviewed scope | Evidence limit |
| --- | --- | --- | --- |
| [Anatomy](https://github.com/wheresryan22/anatomy/tree/1482e8469b0a9e0d8cc18ea2740a01423d29ae80) | `1482e8469b0a9e0d8cc18ea2740a01423d29ae80`, main | Complete 173-file snapshot; one skill entrypoint, ten references; selected kit, capture, driver, print, publisher and audit paths/tests | All paths accounted with hashes; not every implementation line audited or executed. No AGENTS.md, CLAUDE.md, .cursorrules or codex.md exists in this snapshot |
| [OpenCode](https://github.com/anomalyco/opencode/tree/f0160a12627fcf9107bcb5914bba2b012bd1d23e) | `f0160a12627fcf9107bcb5914bba2b012bd1d23e`, dev | Complete 9,058-path index; 1,455 selected files; all eight skill entrypoints, eight commands and 19 AGENTS.md files; relevant core/schema/CLI/plugin/protocol, docs and selected tests | Remaining app/AI/TUI/SDK implementations not fully downloaded or line-audited; pinned development source is not proof of installed OpenCode 2.2 behavior |

Both repositories use MIT licensing. Copied or substantially derived support needs retained notices, explicit provenance, exact dependency closure and pinned source hashes. Reviewed inspiration must be labelled accurately. No source import pin was advanced. The ignored local evidence directory is `orbyn-references/integration-research/`; it is neither a published attachment nor a dependency of this proposal. Source receipts and full source-path accounting stay there; the committed-candidate register contains the reviewed findings and pinned links.

## Keep the nesting contract minimal

Retain the [workspace contract](../../skills/orbyn-setup/references/repository-workspaces.md), [action scope](../../skills/orbyn-setup/references/action-scope.md), [target skill ownership](../../skills/orbyn-setup/references/project-skills.md), [offline/search contract](../../skills/orbyn-setup/references/offline.md) and [workspace ownership](../synchronization.md). Shared methods stay in the outer repository; independent targets/worktrees stay under ignored `repo/`. No new target copies, links, sync protocol, mandatory daemon or third host-configuration tree is proposed.

Instruction lookup stays separate from narrowed code search. Resolve actual target/worktree and required instructions first, then constrain code queries. A search no-match, catalog entry or successful file read does not establish model-request inclusion or runtime enforcement. Continue preferring usable shell `rg`/`rg --files`; native search remains valid. Preserve project policies, private material, licenses and unrelated changes.

Keep Luna High and Sol Medium defaults, optional Terra Medium, standard processing, at most two active children and no recursive delegation. Source-specific model fallback never grants permission to change these defaults. [Memory](../../skills/reflect/references/memory.md) remains explicitly requested, scoped and outside Git; source session APIs and automatic learning hooks do not turn it on.

This proposal adds conditional references only when their task is selected. Ordinary bug fixes must not load illustration, RTL, GPU or OpenCode internals. The research register is a review artifact, not a runtime manifest an agent must maintain for every task.

## Full endpoint and dependency order

The exact P0–P5 owners, dependency IDs and acceptance cases below are authoritative
for this full plan. Earlier N1–N6 labels remain domain groupings, not alternative
endpoints or six new skills. P1 and P2 may proceed independently after P0; P3 uses
P2's verification methods; P4 follows P3; P5 requires all four implementation
batches. Shared mutable files still have one author at a time.

## N1 — Engineering methods from source evidence

OpenCode is a source of engineering decisions, not a host to install or qualify.
Review each observation for reusable registry/collision identity, cache freshness,
context handoff, scoped retrieval, authority versus OS isolation, lifecycle and
client/server ownership. Extend an existing owner only for an actual residual gap;
retain adequate methods unchanged. The corrected per-row applicability distinguishes
these lessons from product-specific discovery paths, tool names, session APIs,
provider routing, binary downloads and native client operations. Those operations
are NOT ADOPTED with reasons, not missing runtime blockers or passing tests.

Preserve all original source observations and their provenance. Do not blanket
exclude OP-001–030: a source-specific observation can support a generic contract
without importing its product's operating procedure. The existing setup/workflow,
architecture, upstream review and tool-effects owners remain canonical. No
OpenCode usage skill/reference, configuration tree, native host trial or provider
qualification is added. Generic search/delegation/evidence policy remains intact.

## N2 — Test reliability and evidence precision

**Owners:** [TDD strategy](../../skills/tdd/references/test-strategy.md), [reproduction](../../skills/how/references/reproduction.md), CI [scope/gates](../../skills/orbyn-ci-design/references/change-scope.md), [bulk failures](../../skills/orbyn-ci-design/references/bulk-failures.md) and visual verification. Prefer one conditional test-reliability reference with short links from the existing owners.

A–I already adds CLI/PTY, browser action contracts, visual baselines, verification adapters and adversarial evidence. The new value is precise failure handling inside those boundaries:

| Additional contract | Failure it should catch | Records |
| --- | --- | --- |
| Propagate the owning virtual clock/signal into actual async work; register waiters before advancing time | Test controls one clock while implementation waits on another; task starts after advance | OP-038–043, 062 |
| Timeout does not imply cancellation; cancel/join before fixture teardown | Late body mutates a disposed fixture or leaks a worker | OP-041 |
| Semantic readiness differs from frame count, visibility, network response and visual idle | Next action races missing content or event connection | OP-039, 048–050, 057 |
| Cold optimizer, production module identity and shared cache ownership | Browser reload loses fixtures; visual copy passes; two ports still share a cache | OP-045, 054–056, 082 |
| Actual runner leg/project/shard/cache/test-file coverage | CI green without executing the affected case; stale helper artifact | OP-047, 052–053, 082 |
| Boundary and artifact fidelity | Service-worker/clock mocks are reported as deployed behavior; retry success hides failed first attempt | OP-051, 053 |
| Input/platform and cost contracts | Real keyboard protocol/Windows path behavior skipped; process-spawn multiplier concealed by local timing | OP-040, 044, 046 |
| Illustration capture and independent oracle validity | Slow RAF mistaken for slow wall timers; geometry stand-in or missing clipped shape passes | AN-007, 018–025, 044 |

Do not import Bun/Effect/Playwright as mandatory frameworks. Pin actual project APIs and ownership. A product race gets a product guard when warranted; adding sleeps, retries or broader timeouts must not hide it. Tests protect credible contracts at an appropriate boundary, with an independent failing control. Existing coverage is extended before adding duplicate suites. A project's prohibition on restarting a server or sharing a build cache outranks a generic reset recipe.

## N3 — Localization, RTL and responsive state

**Owners:** UI and content design; one conditional localization/RTL reference with language/async-state links. This fills a substantive domain gap without a separate localization skill collection.

Cover direction independently from language; preserve semantic DOM/focus order; distinguish logical layout from physical pointer coordinates/native controls; isolate mixed code/paths with bidi-aware markup; normalize RTL scroll; mirror icons according to meaning. Test keyboard, hit zones, submenu anchoring and mixed-direction text. [RTL skill](https://github.com/anomalyco/opencode/blob/f0160a12627fcf9107bcb5914bba2b012bd1d23e/.opencode/skills/rtl-aware-development/SKILL.md), OP-058–060.

Use complete phrases and owned plural/interpolation/fallback APIs. Preserve authored source copy, placeholders, identifiers and established product names. Verify uncertain terminology against relevant locale data and maintained localized products, then flag native review needs. Test live locale changes, missing translations and asynchronous native UI rather than relying on English web fixtures. Do not mandate OpenCode's English-only feature policy for every consumer. OP-067, 080; [app localization rules](https://github.com/anomalyco/opencode/blob/f0160a12627fcf9107bcb5914bba2b012bd1d23e/packages/app/AGENTS.md#L83).

Add only missing reusable refinements for meaningful accessible announcements, reduced-motion content parity, text clipping/font roles, semantic themes and first-load/refetch focus/scroll continuity. AN-015–016, 033; OP-057, 079. Keep framework-specific APIs, token names and pixel sizes conditional. A narrower Suspense boundary changes what blanks; it does not prevent suspension. No universal Solid/React API mandate follows.

## N4 — Truthful technical illustrations

**Proposed owner selected in this full plan:** `technical-illustration` at `skills/technical-illustration/SKILL.md`. Trigger on creating/editing interactive explanatory figures with model-driven geometry, motion, readouts and export. Adjacent non-triggers: ordinary app layout, social post graphics, a simple Mermaid explanation, scientific chart, and routine architecture design.

This end-to-end artifact differs from product UI and social preview enough to justify one owner with conditional references. A guidance-only reference under `how`/UI would leave the selected creation capability incomplete. The new owner provides the full artifact workflow and links to existing general methods; prose alone cannot claim Anatomy parity.

The entrypoint should stay short: choose whether a physical metaphor helps; choose fidelity and a minimum useful artifact; define the model; establish interaction, accessibility and evidence; select only the needed output path. Load craft/motion/geometry/print/WebGL/3D references on demand. Do not copy mandatory part counts, monochrome/light-first aesthetics, no-arrows or no-comments rules into general engineering.

Core coverage contract:

1. One pure model and sampled instant drives geometry, movement, numeric readout, caption, accessible state and exported values. A lagging gauge must not pair an old numeric value with a new phase. [Motion contract](https://github.com/wheresryan22/anatomy/blob/1482e8469b0a9e0d8cc18ea2740a01423d29ae80/references/motion.md#L13), AN-001–004.
2. Camera/projection/depth and actual drawn geometry agree with the verifier, including clipping, transforms and attributes. Surface coverage heuristics expose missing records but do not prove equivalence. AN-005–010.
3. Test actual animation schedule, tails, reversals and intermediate/prefix states; distinguish visual ownership from physical attachment. User takeover starts from visible state; controls arm when physically ready. AN-011–014.
4. Keep input under reduced motion, meaningful accessible updates rather than frame-rate announcements, SSR rest state, per-figure identity and owned offscreen/settled cleanup. AN-015–017, 033.
5. Preserve the live figure/model in export, report finite sampled versus full configured audits accurately, and inspect the actual image/print artifact. AN-024–027, 035–036.

Existing UI/TDD/language owners retain reusable accessibility, lifecycle and evidence rules; this owner links to them. It must not become a second general UI workflow.

## N5 — Complete Anatomy executable support

Guidance and executable support have separate evidence requirements, and both are in the full endpoint. Keep raw research ignored. Pin a reviewed MIT subset at the proposed maintained path below, with required notices, source manifest, transitive dependencies and offline support. Do not depend on ignored downloads or target skill installation. Adding generated figure code to an authorized target artifact is distinct from copying shared skill instructions there.

| Stage | Selected capability | Exit evidence |
| --- | --- | --- |
| 1 | Core SVG/model/motion plus necessary geometry/line checks | Dependency closure; deterministic geometry cases; native browser interaction; actual wrong-value/missing-shape/misattached-line controls fail |
| 2 | React integration and print export, required | SSR/hydration, streamed/large page and multi-figure isolation; same live poses; vector/raster labels; all PDF pages/crops/fonts/focus IDs inspected |
| 3 | WebGL/shader capability, required | Shared camera/layers, opening masks, event envelopes, bandlimits, same-task GPU readback, light/dark/nested theme and missing-context/compile-failure fallback parity; hardware/driver recorded |
| 4 | Documented beta 3D capability, required and still labelled beta | State envelope/decomposition/identity, actual temporal paths, full configured sampled audit plus planted failures; explicit finite bounds and performance cost |

Experimental `turn-fixed`, `canvas-painter` and `gl-shared` stay excluded by default. Anatomy core's “zero dependencies” does not cover React/development/qualification. Upstream CI rebuilds examples on macOS; it is not proof of cross-platform geometry, interaction or browser success. Five authored eval prompts are not recorded agent trials. AN-022–039, 044.

Pre-adoption controls matter: capture/drive can print console errors without making exit status a complete console-clean oracle; slow RAF does not slow wall timers; documentation and implementation disagree on some timeout behavior. Inspect exact selected helper semantics and use failure-sensitive controls rather than copying prose claims. AN-019, 021, 043.

Exclude the default gallery publisher and automatic session extraction from this integration. The [publisher](https://github.com/wheresryan22/anatomy/blob/1482e8469b0a9e0d8cc18ea2740a01423d29ae80/scripts/publish.mjs#L245) can configure Git auth, reset a branch and force push; the [session helper](https://github.com/wheresryan22/anatomy/blob/1482e8469b0a9e0d8cc18ea2740a01423d29ae80/scripts/session.mjs#L34) can inspect Claude history. Neither becomes authorized by requesting an illustration. Existing scoped memory and publication policies remain authoritative. Chrome helpers that allow local file access, supplied JS or Linux `--no-sandbox` require a trusted, permitted test surface; never use them to bypass a blocked browser tool. AN-040–042.

## N6 — Small runtime and research refinements

Prefer focused examples in existing owners after A–I reconciliation:

- **Research/upstream:** freeze actual reference bytes/revision before comparing; shared managed Git caches can refresh/reset between attachment and later read. A reference advertisement is not readiness, access or immutable provenance. OP-029–030.
- **Runtime/trace forensics:** identify client/server/build/run/role; distinguish heap retention from RSS/native allocation and account for observer overhead. A debugger attachment must not silently change the user's color, motion or focus preferences. OP-031–037.
- **AI application/tool effects:** provider pass-through extensibility differs from closed authorization decisions; replay selected redacted exchanges with no key requirements. Tool registration/catalog visibility does not imply execution authorization, and a snapshot does not freeze mutable producer state. OP-073–074.
- **Architecture/backend/lifecycle:** admission versus execution/recovery, plugin generation versus route/screen identity, event/reply/snapshot ordering, async persistence load, PTY byte bounds/EOF/identity and shipped-key migrations. Keep actual protocol authority explicit; a process-local recovery marker is not distributed fencing. OP-075–078.
- **Refactoring/release:** an empty permanent experiment framework is not dead code; changelog attribution follows actual diff/history. Target conventions, sample commands and embedded model/service instructions stay target-owned. OP-061, 063–066, 068–072, 081–083.

These observations often refine an existing principle. If the exact final A–I owner already explains the case adequately, close it as equivalent with an anchor rather than writing another paragraph. No automatic history capture, learning hook, auth change, model fallback, server replacement or source-specific universal coding style is proposed.

## Exact owners and future file allowlist

Implementation uses the following owning paths. Existing owners remain canonical; the register retains every source observation and gives each row its corrected method owner, `REQ-<source-ID>` case and separate evidence disposition.

| Area | Primary owner and proposed files | Existing links / support |
| --- | --- | --- |
| Engineering methods from source | Existing setup scope/offline, architecture, workflow and tool-effects owners | Per-row generic contracts only; no product-specific usage reference or host configuration |
| Test reliability | `tdd`: `skills/tdd/references/test-reliability.md` (new reference) | test-strategy; how reproduction; CI change-scope/affected-targets/bulk-failures |
| Localization / RTL | UI: `skills/orbyn-ui-design/references/localization-rtl.md` (new reference) | UI design-rules/async-state; content-design |
| Illustration workflow | `skills/technical-illustration/SKILL.md`, `LICENSE`; references `craft-and-model.md`, `motion-and-input.md`, `geometry-and-lines.md`, `react-and-accessibility.md`, `capture-and-drive.md`, `print.md`, `webgl.md`, `3d.md`, `dependencies-and-update.md` | how/UI prototypes; existing TDD, performance and artifact-lifecycle owners |
| Maintained executable support | `skills/technical-illustration/references/upstream/anatomy/` with inactive `SOURCE.md`, MIT notice and `source-manifest.json`; selected `kit/` and `scripts/` relative paths | D-SVG through D-PACK below; no plugin-cache edits or ignored research dependency |
| Runtime / maintenance refinements | Exact per-row current owner in the register | Partial rows: trace/runtime forensics, upstream review, AI tool-effects, architecture, async-state, CLI and explanation/recaps; equivalent/excluded rows retain existing guidance |
| Registration / tests / delivery | `skills/catalog.json`, generated discovery/index, `provenance.json`, `distribution/manifest.json`, `docs/skill-audit.md`, `skills/orbyn-skill-creator/evals/cases.json`; proposed `tests/test_engineering_methods.py`, `tests/test_technical_illustration.py` if repository-native harness fits | Existing helpers generate metadata; preserve all 283 previous case objects/holdouts; no new framework presumed |

One illustration owner adds one skill (35 to 36), not one per renderer or host. The consumer owns its actual figure/model, assets, React peer locks and permitted artifact output. Authorized generated figure code may include selected drawing modules; shared skill instructions are never installed into targets.

## Delivery batches and blocking edges

| Batch | Responsible owner | Depends on | Required outcome |
| --- | --- | --- | --- |
| P0 | orbyn-plan + orbyn-upstream-review + architect | none | Freeze merged baseline, full selected closure, licenses, supported host/OS/runtime/build cells and all requirement cases; resolve remaining version/dependency gates. |
| P1 | Existing engineering owners | P0 | Extract generic identity/cache/authority/context/lifecycle decisions and retain adequate existing methods; do not add source-product operating instructions or host qualification. |
| P2 | tdd, UI/content, CI and each existing runtime/tool-effect owner | P0 | Complete reusable method refinements and retain equivalent/excluded boundaries without duplicate instructions. |
| P3 | technical-illustration; tdd/UI support existing generic methods | P0, P2 | Complete pure-model SVG/motion/geometry/line/capture/drive path and offline packaging. This is a milestone, not the full endpoint. |
| P4 | technical-illustration | P3 | Complete React/hydration, print, WebGL and documented beta3D paths with their specific dependencies and checks. |
| P5 | orbyn-skill-creator + orbyn-ci-design; independent reviewer | P1, P2, P3, P4 | Reconcile all 127 cases, validate full integration, fresh contexts/support matrix/upgrade controls and final review. Publication remains separately authorized. |

Every batch has failure-sensitive cases below. Keep build outputs, fixtures, profiles and ports owned per attempt. Roll back only a failing owned batch and preserve prior evidence/unrelated checkouts. P0 records exact runtime/tool/peer locks, selected test fixtures and missing prerequisites before adoption. A pending dependency is a blocker, not a compatibility claim.

## Dependency contract

Pinned source fixes code bytes, not browser/GPU/font or React peer versions. Exact dependency edges and candidate source paths follow. Node/Chrome are conditional illustration prerequisites. OpenCode application/host/provider prerequisites are not adopted. No source-product application fork/build is proposed.

| ID | Depends on | Contract and unresolved gate |
| --- | --- | --- |
| D-NODE | none | Pinned Anatomy README declares Node 20.10+ and documents 20.19/22.11 rebuilds; core/scripts use Node built-ins, browser helpers need native WebSocket or documented Node 20 restart flag. No upstream package.json/lockfile exists. Freeze actual maintained runtime path/version and compatibility tests; do not invent an npm dependency lock. **Gate:** Exact supported runtime matrix must be frozen during implementation preflight; source-declared minimum is not a new compatibility result. |
| D-BROWSER | none | Permitted browser/Chrome executable and owned profile/port/storage; record exact browser/OS/renderer. Generic method fixtures can use their existing project browser tools. Anatomy capture additionally requires D-NODE and native WebSocket/CDP via D-CAPTURE. Denied sandbox or missing browser stays blocked; no automatic sandbox/file-access escalation or download. **Gate:** Actual supported browser/OS cells and input semantics require execution. |
| D-SVG | D-NODE | audit -> iso-kit+lathe+tube; tube -> iso-kit+lathe; lathe -> iso-kit; CSS travels with the figure. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-CAPTURE | D-SVG, D-BROWSER | drive -> chrome-port+line-ends; capture -> chrome-port; lines spawns drive. Preserve all relative imports/spawn targets. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-REACT | D-SVG, D-CAPTURE | draw.tsx -> React + ../iso-kit + ./live; live.tsx -> React. Source declares React 18+; ReactDOM, TypeScript, bundler and SSR framework are consuming-project/test-fixture peers, pinned by that project lock. No new application-wide React/Next dependency. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-PRINT | D-SVG, D-CAPTURE | print -> print-sheet; PDF button is browser-side. Each authored sheet/figure/model and approved local fonts are artifact inputs. A PDF renderer/inspector with recorded version is required to inspect every page; no new PDF npm package presumed. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-GL | D-SVG, D-CAPTURE | gl.mjs uses browser WebGL; shader/ramp/mask code is artifact-owned. Actual supported context/GPU/SwiftShader, DPR, theme and buffer lifetime must be captured. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-3D | D-SVG, D-CAPTURE | turn-build -> turn+iso-kit+lathe+audit; turn-audit -> turn+audit+lathe+iso-kit+turn-build; turn-check -> chrome-port+line-ends; fidelity -> iso-kit+lathe+tube+turn; bench -> turn. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |
| D-PACK | D-SVG, D-CAPTURE | inline-kit and fingerprint are reviewed adaptation candidates, not safe unchanged wrappers. Freeze selected-file scope and references/model/style/host inputs outside the kit fingerprint separately. Package incrementally: P3 closes core files only; advanced files enter only when their P4 dependency is ready. The final P5 full package includes every required stage. This shared packager does not require P4 to begin P3. **Gate:** Before import, recursively close static/dynamic imports, file reads, spawned tools, applicable tests/fixtures and fonts; freeze hashes/notices. The 25 listed runtime files do not by themselves establish complete test/fixture closure. |

The register records SHA-256 hashes for the exact 25-file runtime source candidate set at the Anatomy pin, before applicable tests/fixtures and authored regressions. Preserve relative paths at the maintained destination. Recursively close any required import/read/spawn/fixture/font dependencies before adoption:

| Dependency | Pinned source paths (relative to Anatomy) |
| --- | --- |
| D-SVG | `kit/iso-kit.mjs`, `kit/iso.css`, `kit/lathe.mjs`, `kit/tube.mjs`, `kit/audit.mjs` |
| D-CAPTURE | `scripts/chrome-port.mjs`, `scripts/capture.mjs`, `scripts/drive.mjs`, `scripts/line-ends.mjs`, `scripts/lines.mjs` |
| D-REACT | `kit/iso-kit.ts`, `kit/react/draw.tsx`, `kit/react/live.tsx` |
| D-PRINT | `kit/pdf-button.mjs`, `scripts/print.mjs`, `scripts/print-sheet.mjs` |
| D-GL | `kit/gl.mjs` |
| D-3D | `kit/turn.mjs`, `kit/turn-build.mjs`, `kit/turn-audit.mjs`, `scripts/turn-check.mjs`, `scripts/turn-fidelity.mjs`, `scripts/turn-bench.mjs` |
| D-PACK | `scripts/inline-kit.mjs`, `scripts/fingerprint.mjs` |

Packaging is incremental: P3 packages the core closure; P4 adds each qualified advanced closure; P5 requires the complete package. D-PACK depends on the core, so it creates no P3/P4 dependency cycle. Generic browser method fixtures may use their existing project tools; Anatomy CDP helpers additionally require Node.

These are source-planning candidates, not an assertion that unmodified helpers satisfy Orbyn. Review capture/drive timeout/console-exit behavior, packaging replacement effects, fingerprint scope and all required fixtures. No package manifest/lockfile exists at this Anatomy pin; React peers and test-only dependencies require explicit consumer/test-owner locks. Do not invent a dependency count or call an import complete before those gates pass.

## Acceptance cases and required evidence

All 127 original observations retain unique `REQ-AN-xxx` or `REQ-OP-xxx` specifications in `full_integration_plan`: exact owner files, P batches, dependency IDs, original positive/countercase and linked group assertions below. These are instructed development specifications, not agent results. Implementation/evidence fields record actual selected checks separately; a group criterion cannot erase a failing or unrun row assertion.

| Case | Required positive | Discriminating negative | Required surface |
| --- | --- | --- | --- |
| OC01 | Resolve actual target/affected instruction scope and distinguish bytes/read/request/effect evidence. | Sibling instruction or read-only source evidence is treated as execution enforcement. | Source/owner review and synthetic scope/evidence counterexample; no source-host injection test. |
| OC02 | Registry replacement, selected identity and cache refresh use explicit collision and generation ownership. | Catalog or stale symlink-target snapshot is mistaken for immutable current implementation. | Generic controlled registry/cache identity fixture and source review. |
| OC03 | Existing explicit scoped brief and current owner account for context/constraints and all attempts. | Assumed context inheritance or a late old result grants current effect authority. | Existing policy/ownership fixtures; no OpenCode child/model/provider trial. |
| OC04 | Selected search roots/hidden/ignore/result bounds define the actual coverage claim. | No-match/truncated prefix or query resource is called whole-tree absence/path confinement. | Generic controlled file/search fixture and source review; no source-native backend probe. |
| OC05 | Timeout, interruption, completion and recovery reconcile current ownership before effects. | Observation timeout duplicates a live owner; stale result replaces current output. | Existing bounded lifecycle/late-result fixtures; no OpenCode session qualification. |
| OC06 | Effective allowed effects, policy and OS isolation are distinct and retained across operation identity. | UI permission prompt, fresh worker or query restriction is called credential/OS isolation. | Generic denied/stale effect contract fixture and source review. |
| OC07 | Diagnostics identify actual client/server/process/build/run and immutable reference bytes. | UI restart or reference advertisement is mistaken for server replacement/readiness. | Owned generic process/reference identity fixture and source review; no product usage support. |
| TR01 | Actual tool-launched executable and clock domain are recorded; waiters register before advancement; timing/deadline owners propagate to async work. | Wrong virtual clock, process-relative timestamp comparison, advance-before-registration or process spawn defeats timing assertions. | Separate-process and async fixtures with deliberately mismatched clocks; actual command traces. |
| TR02 | Per-attempt state, mocks and module registry are isolated; cancel/join finishes before fixture removal. | Timed-out body mutates deleted fixture, inherited mock/global state or mutable builder pollutes next attempt. | Real controlled cleanup, leak and late-write checks. |
| TR03 | Semantic readiness, connection/event delivery, final focus/mount and native keyboard/pointer states precede the action. | Quiet frames/visibility alone, unknown mocked route, synthetic input labelled native or service-worker mock labelled deployed behavior. | Actual relevant terminal/browser/native surface with race and rejected-action controls. |
| TR04 | Production module identity and cold optimizer/cache ownership match the checked source and actual fixture. | Copied story passes while production module fails; cold reload resets seed; separate ports share contaminated cache. | Cold/warm source-bound browser/build fixture; explicit shared outputs. |
| TR05 | Affected test file/project/task/shard is executed; skipped leg and first failed/retry artifacts remain visible. | CI green without target case, stale task registration/cache input, missing shard or retry-only evidence qualifies the claim. | Selected runner discovery and receipts with planted omitted case/job. |
| TR06 | Correct completed-work counts and bounded varied-input oracle accompany cost measurements. | Fast empty/error/hardcoded known vector or noisy wall-time threshold passes as valid optimization. | Matched workload/harness, diverse correctness controls and retained attempts. |
| RTL01 | Direction independent of language preserves DOM/focus order, logical layout, physical hit zones, meaningful icon direction and RTL scroll endpoints. | Mixed Arabic/Hebrew code/path, RTL English, wrong mirrored icon or negative-scroll endpoint breaks interaction. | Actual renderer/keyboard/pointer cases; declared platform and language-review limits. |
| RTL02 | Whole phrases, plural/interpolation/fallback APIs and authored placeholders survive live locale change and native asynchronous labels. | Concatenated phrase, damaged MDX/code placeholder, missing fallback or stale locale/native label. | Locale fixture and actual consuming renderer/native surface; terminology review. |
| UI01 | Loading/refetch identity, focus/scroll continuity, semantic themes/font roles and reduced-motion content remain coherent. | A smaller Suspense boundary is called prevention of suspension; custom token fallback/portal/transition loses meaning or focus. | Real renderer state transitions and inspected theme/font evidence. |
| RT01 | Reference revision and exact bytes remain identified across managed-cache attach/read; source/prose conflicts retain evidence. | Refresh/reset silently substitutes a different revision or a fingerprint is claimed to cover unmeasured inputs. | Read-only pinned source/byte receipts and planted cache drift. |
| RT02 | Client/server/run/role diagnostics separate heap retention, RSS/native allocation and observer effects while preserving user media/focus settings. | Partial heap artifact, wrong run, debugger-induced theme/motion/focus change or RSS increase is misdiagnosed as retained JS heap. | Owned process/capture fixture and actual renderer attachment where claimed. |
| RT03 | Tool definition/executor snapshot is separated from mutable producer state; open provider fields pass through while closed authorization decisions remain validated. | Stale definition grants effects or unknown orchestration verdict is accepted because provider payloads are extensible. | Redacted synthetic exchange replay, schema and current-generation effect controls. |
| RT04 | Durable admission, execution, unknown outcome and restart recovery are separate; event/reply/snapshot/storage-load authority is explicit. | Process-local marker is called distributed fencing; old snapshot or early reply overwrites current accepted state. | Controlled lifecycle/persistence protocol fixture; no real service/cluster claim from a local model. |
| RT05 | Route A-B-A/plugin replacement reacquires the correct service; PTY has one I/O owner, byte bounds, durable identity and joined terminal state. | Shorter-lived cached object survives replacement, child exit is mistaken for EOF or stale PID/reply affects the next owner. | Real owned process/PTY plus async generation controls. |
| RT06 | Changelog uses exact range and user impact; useful permanent experiment infrastructure and target maintenance constraints are preserved. | Invented attribution, deletion of a graduated framework, major excluded upgrade or source-specific convention becomes universal. | Scoped source/history and synthetic editorial/maintenance cases. |
| AN01 | A concept model/sample drives parts, movement, phase, numeric readout, accessible caption and exported values together. | Wrong gauge/phase, fabricated physical claim, meaningless parts or a chart request routed into physical illustration. | Pure model cases plus actual inspected figure/readout and adjacent non-trigger tasks. |
| AN02 | Actual emitted paths, transforms, clipping, depth, contacts, variable radii and line attachments agree through intermediate states. | Missing clipped shape, unrecorded drawing, false mount, dangling endpoint, reversal collision or exhausted curve budget passes. | Independent geometry/line oracle, real SVG/browser ground truth, planted broken variants. |
| AN03 | Actual schedules/tails/prefixes/reversals and valid arming are exercised; tour takeover begins at visible state. | Ownership confused with attachment, double toggle/reset, pre-armed action or mid-tour jump. | Native pointer/keyboard interaction and sampled schedule/state controls. |
| AN04 | Selected figure/input/crop is current; whole action list validates before effects; async assertion/until failures propagate. | Missing selector, empty/nonfinite action, swallowed console/rejection/timeout, synthetic click labelled native or stale crop. | Real permitted Chrome/CDP and retained screenshots/action/error output; failure-sensitive exit checks. |
| AN05 | Offscreen/settled loops stop and resume without jump; reduced motion retains input/content; announcements track choices/phases. | Frame-rate screen-reader stream, lost explanation without GPU or replaced-ref/listener leak. | Actual browser accessibility/input and lifecycle checks; inspected fallback. |
| AN06 | React server rest pose, hydration, first readout, streamed page, StrictMode and multiple figures preserve independent state. | Hydration mismatch, wrong nearest readout, second figure updating first or stale replaced component. | Consumer-owned React/ReactDOM/TS build plus actual SSR/browser hydration and lifecycle. |
| AN07 | Same-model poses export faithful vector/raster layers with unique IDs, selected focus, fonts and every configured page/format inspected. | Missing selector, remapped-ID collision, clipped page/font substitution or raster output presented as all-vector. | Actual PDF generation and rendered inspection of every page, not only page one. |
| AN08 | Model/camera/layers/masks and event phases agree; paper/ramp/theme compositing and reduced-motion/no-context fallback preserve meaning; GPU readback occurs in the same draw task. | Wrong opening mask, pre-boundary energy, empty/cleared framebuffer, wrong alpha or compile failure loses content. | Actual hardware/software renderer, numeric image controls, light/dark/nested themes and measured work budget. |
| AN09 | Documented beta3D state envelope, convex/group/parent identity and actual temporal paths pass configured full finite audits; continuity and cost are measured. | Missing decomposition/group, hinge/free-clip mismatch, jump hidden by coordinate rounding or quick sampling labelled continuous proof. | Actual turn build/check/fidelity/benchmark, planted broken models and explicit sampled bounds; beta label retained. |
| AN10 | Selected source closure, MIT notices, source fingerprints, target artifact packaging and offline reproduction are exact and recoverable. | Missing relative import, untracked runtime download, mismatched kit, shared-skill copy, destructive replacement or fingerprint overclaim. | Pinned source manifest, transitive import/read/spawn/fixture inventory and clean offline rebuild/diff controls. |
| POL01 | Equivalent methods and explicit exclusions retain target ownership, no recursive delegation, scoped memory and separate publication authority. | Automatic history harvest/publisher/auth rewrite, target skill installation or upstream style/model/default override is adopted for parity. | Source/policy review and each original row positive/negative example; no external writes required. |

**Support matrix:** qualify actual Node/Chrome/React/PDF/GPU illustration surfaces separately by OS/renderer. Unavailable required Anatomy surfaces remain BLOCKED and keep full live illustration qualification incomplete. No OpenCode CLI/TUI/desktop/model/provider support matrix is selected. Generic method fixtures do not qualify a source product or model behavior. Native mobile is not implied.

**Completion requires** evidence for every selected applicable row, dependency closure, required platform/client/renderer cell and maintenance control, plus library checks, applicable executable regressions and independent exact-candidate review. Preserve failed/invalid attempts, unknown outcomes and beta labels. Equivalent/excluded rows require reviewed owner/reason preservation, not fabricated runtime execution. The five existing policy exclusions remain. Experimental `turn-fixed`, `canvas-painter` and `gl-shared` variants are explicit research exclusions, not qualified stable capabilities. Stage 1, an aggregate score or a code fingerprint cannot substitute for full closure.

## Corrected verification protocol

Freeze all 127 source-row dispositions, the 33 corrected method/illustration
groups, actual candidate/tool/input hashes, allowed effects and stop limits before
qualification. Preserve old evaluation objects/holdouts. Use source review for
existing equivalents and policy exclusions; use controlled async/process/search/
registry/CI/renderer fixtures for generic engineering contracts and actual browser,
React, PDF/GPU and beta3D surfaces for illustration claims. Each selected assertion
needs its own discriminating negative control. A case may cover multiple rows only
when its assertions distinguish their relevant contracts.

Product-specific OpenCode operating requirements are NOT ADOPTED, never scored as
passing engineering methods or reported as runtime blockers. The superseded
OpenCode-native host and 126-trial agent-study design remains only in preserved
research history, not the current implementation endpoint. No inference/provider
calls, source-host usage probes or paid agent study is required or authorized by
this correction. Keep unperformed Anatomy/runtime/platform qualification explicit;
static library checks do not prove those surfaces. Independent review covers the
actual final candidate, not the author's own claims. No aggregate percentage can
replace per-row applicability and evidence.

## Sequencing, acceptance and handoff

Follow P0–P5 below. A–I is already merged; preserve it as the baseline. The full
endpoint includes every required capability and per-row acceptance requirement,
with deliberate exclusions retained explicitly. Do not stop at guidance-only or
core SVG and describe the entire integration as complete.

Implementation is now authorized within the corrected scope. One author owns each
coherent batch and a reviewer checks actual source, evidence and limits. Keep
runtime/source adoption and existing-owner method changes reviewable without
creating one PR or one new skill per observation. Publication, merge, external
service writes and model/provider changes keep their separate authority.

Rollback uses only the owned failing batch, preserves previous evidence and leaves unrelated user work/resources intact. No force reset, broad clean, global configuration replacement or deletion of active target paths is a recovery shortcut.

This proposal and its register are local research artifacts. Skills, defaults, nesting and imported support remain unchanged by this research. Static document validation must be reported separately from A–I qualification and future integration results.

## Research artifact validation history

The research plan/register passed the library validator under Python 3.13. All 127 unique rows, 211 pinned source anchors, 19 OpenCode instruction files, eight skill entrypoints, eight commands, A–I overlap IDs and referenced existing OpenCode owner paths were checked. Both new files passed explicit whitespace validation; the Git index remains empty. This validates the research artifacts, not the proposed integration.

The later frozen-candidate reconciliation preserves all original observation
fields, covers all 127 IDs exactly once, and validates 280 candidate owner anchors
against the named source map. Its two source-review slices independently checked
the 54-file receipt identity. This is independent source reconciliation, not
independent execution of an integration or review of changes not yet authored.

A separate read-only reviewer checked Anatomy source fidelity and proposal consistency. That review identified a stage-1/stage-2 evaluation coupling; Q10 now requires core geometry/SVG acceptance, while print is a separate required stage-2 subcase in the full endpoint (conditional only in the earlier core-SVG proposal). The reviewer did not repeat the OpenCode audit. Source audit depth and unperformed runtime checks remain as declared above. No skill, host configuration, model default, source dependency or target file changed in this research worktree; no commit or publication occurred.

## Historical full-plan update before user scope correction

This update changes only this planning document and its existing JSON register.
It pins merged A–I as the implementation baseline, preserves all original 127
observations/reconciliations, and adds explicit owners, dependency edges and
acceptance specifications. P0–P5 and all new tests/host/render cases remain
planned, not implemented or run. No skill, generated catalog, model default,
host/provider configuration, target, vendored code or package lock is changed.
No install, inference, browser execution, commit, push or PR is authorized by this
plan-only update. The existing completed A–I publication is separate.

Validation of this update passed the library checker (35 existing skills, 269 Markdown documents) and a separate structural check: all 127 original observation records are unchanged, all 127 requirement IDs are unique, all 33 acceptance groups are referenced, both batch/dependency graphs are acyclic, all 47 existing owner paths exist, and all 25 runtime candidate hashes match the pinned snapshot. Whitespace and scope checks passed; the index is empty and only these two existing untracked planning artifacts changed. These checks validate the plan structure and source identities, not executable compatibility or live behavior. This update has not received independent review.

## Current implementation scope correction

The user's later instruction supersedes the OpenCode host integration in the
historical proposal. P1 now adapts engineering methods into existing owners;
source-specific operating instructions are not adopted. The full Anatomy
workflow, executable dependency closure and P3/P4 capabilities remain selected.
The current register preserves every original source observation and adds explicit
corrected applicability/ownership/case metadata. The removed host guide is retained
only in ignored implementation history. No target instruction, auth, model policy,
shared installation, live host qualification or publication is added.

## Implementation review checkpoint

The [implementation evidence](reference-integration-verification.md) records the
corrected source scope, selected offline support, actual dependency locks and
executed checks. The register maps all127source observations and33groups without
turning exclusions into passes. One new illustration owner and two generic method
references extend existing owners; no OpenCode usage guide or host integration is
included. All283old case objects and protected nesting/model/memory policy remain
preserved. Thirty-six new criteria are explicitly instructed development
specifications; no natural-routing, effectiveness or paid-model result follows.

All selected Anatomy source capabilities are maintained, including core, React,
print, WebGL and documented beta3D. This is not a claim of full live qualification:
actual checked surfaces and remaining motion/GPU/beta/framework/OS/font/AT/model
cells are separate. The original full-qualification rule still applies to any
future claim of full runtime support. Commit requires the coordinating reviewer's
exact-candidate clearance. No publication, merge or Orbyn update is authorized.
