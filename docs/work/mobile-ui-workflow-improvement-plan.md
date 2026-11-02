# Expo mobile, UI craft and cause-oriented workflow improvement proposal

Research date: 28 October 2026. **Implementation approved after this proposal.**
P0–P7 are being implemented in the owning local worktree; commit remains held for
independent review. The original research findings and acceptance contract below
are retained. See [current verification](mobile-ui-workflow-verification.md) for
actual evidence and open qualification; approval does not imply every native,
service or agent cell has passed.
PR [#40](https://github.com/kinqsradio/orbyn-fullstack-skills/pull/40) was merged
after its checks passed. The research baseline is merged main
`4e7dbe0bb1de2fb23c7ecb8c6582e8edeb9e3e35`; the primary checkout was fast-forwarded
to that commit and its post-merge validation run passed.

## Decision and scope

Make Expo a first-class source of mobile engineering capability in the nested
library. Preserve concrete Expo/React Native methods, version-aware examples and
release diagnostics, rather than reducing them to generic engineering advice.
Combine these with Emil's ordinary UI motion, mobile-web and stress-testing methods
and the useful cause-to-work-item reconciliation pattern from the supplied image.

Use existing skill owners with conditional, local references and a small mobile
routing index. This is a complete implementation proposal across the reviewed
capability families, not a proposal to install upstream plugins, operate a new
agent host, or import every upstream instruction. Keep 36 canonical skills unless
later routing trials demonstrate that a separate mobile owner is necessary.
Do not sacrifice domain depth merely to minimize file count.

Preserve the [nested workspace contract](../../skills/orbyn-setup/references/repository-workspaces.md),
[action scope](../../skills/orbyn-setup/references/action-scope.md),
[project-owned skills](../../skills/orbyn-setup/references/project-skills.md),
[local memory boundary](../../skills/reflect/references/memory.md), current model
defaults and consuming-project authority. No target installation, copied skill
tree, provider configuration, global plugin change or automatic memory capture.
Package installation, native generation and remote effects belong only to a
subsequently authorized consumer task, with its actual scope.

## Sources and evidence limits

| Source | Pinned identity and inspected scope | What this establishes |
| --- | --- | --- |
| [Emil skills](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202) | `2d228630ba1446365f614a108cb8252f1feda202`; 29 regular files, including 15 public skill entrypoints, eight skill support Markdown files, root performance cheatsheet, README and MIT license | Source methods and their depth; no measured agent-quality advantage |
| [Expo skills](https://github.com/expo/skills/tree/8a0dc4fa57ae345923c357e1451cbcd8b6f2a7db) | `8a0dc4fa57ae345923c357e1451cbcd8b6f2a7db`; 184 regular files, 23 main product skills, one experimental migration skill and internal evaluation guidance | Substantial mobile-specific methods; not proof of compatibility with any consuming app |
| Supplied workflow image | Visually inspected image supplied with this request; root/cause orchestration, investigation, tickets, proposal, implementation and PR stages | Visible design only; scripts, schemas, tracker state, atomic claims and operational results were not available |
| Current library | Main `4e7dbe0`; existing UI/language/architecture/workflow/CI/TDD and evaluation owners | Current written coverage, not evidence that agents always follow it |

Raw downloaded files and investigator reports remain under ignored
`orbyn-references/` in the primary checkout. Regular files were extracted from
pinned Git archives after path/type inspection; no upstream scripts, hooks,
installers or tests were executed. Expo's `CLAUDE.md` symlink points to its
`AGENTS.md`; the symlink was not materialized. Its `eval-harness` Git submodule
(`da0eba34bf02b6dc57a6eca611c4bdab73b246c5`, expo/eval-experiments) was not fetched
or run. Do not claim a complete audit or reproduced result for that dependency.

The lead separately checked official [runtime compatibility](https://docs.expo.dev/eas-update/runtime-versions/),
[Continuous Native Generation](https://docs.expo.dev/workflow/continuous-native-generation/),
[development builds](https://docs.expo.dev/develop/development-builds/introduction/)
and [Expo UI](https://docs.expo.dev/versions/latest/sdk/ui/) documentation online.
These confirm relevant distinctions, not target-version compatibility. Future
examples must select the consuming app's SDK documentation, not moving `latest`.

Both repositories carry MIT notices. Selected adaptations need source revision,
local notice and provenance records. Linked articles, platform talks, fonts,
screenshots and dependencies do not inherit the repositories' licenses. Do not
publish the friend's image, company keys, ticket labels or private procedures.

## Coverage findings

The library already provides root-cause investigation, affected checks, genuine
failure controls, explicit lifecycle/authority, bounded delegation, meaningful
review, rendered/native evidence distinctions and resumable work. These should be
reused. The missing depth is mainly SDK-specific mobile execution, ordinary UI
motion mechanics and reproducible adverse UI inputs. The screenshot contributes
a small workflow refinement, not a replacement orchestration system.

### Expo: complete product-entrypoint disposition

The source paths below are relative to the pinned repository; main entrypoints
are under `plugins/expo/skills/<name>/SKILL.md`. All proposed references are local
to their named existing owner and load only for the relevant mobile request.
“Partial” means general principles exist but Expo-specific mechanics need work.

| Source entrypoint | Current gap / selected coverage | Proposed owning destination |
| --- | --- | --- |
| `expo-overview` | Missing SDK-aware goal router; distinguish Expo dependency, explicit Expo/EAS intent and native-only EAS delivery | Workflow `references/mobile-engineering.md`; links to domain owners, no mandatory extra invocation |
| `expo-project-structure` | Missing Expo Router route-vs-component and config ownership examples | Architect `references/mobile-boundaries.md`; preserve existing layout, use conventions only for new work |
| `expo-native-ui` | Partial native controls, platform styling, media, icons, storage, effects and native rendering | UI `references/mobile/native-ui.md`; API/version-gated examples, no mandatory visual theme |
| `expo-ui` | Missing universal versus SwiftUI/Compose/drop-in host contracts and component capability selection | Same native UI owner; large-data virtualization distinguished from grouped native rows |
| `expo-router` | Missing route groups/layouts, deep links, tabs, sheets, search, toolbars, transitions and back-stack behavior | UI `references/mobile/navigation.md`; architecture owns route/permission boundaries |
| `expo-animation` | Missing concrete worklet/runtime, gesture arbitration, keyboard synchronization and haptic lifecycle | UI `references/mobile/motion.md`; paired with general motion guide and actual runtime configuration |
| `expo-design-system` | General tokens/drift covered; native semantic tokens, text scaling and platform conventions need concrete examples | Existing UI design-rules/visual-direction plus native UI reference |
| `expo-data-fetching` | General stale-result/retry semantics covered; mobile connectivity, foreground recovery, caching, route loaders and SDK APIs need detail | UI `references/mobile/data-and-lifecycle.md`; backend links for real authority/idempotency |
| `expo-dom` | Missing native/DOM serialization, asset, layout, ref and callback boundary | Architect mobile-boundaries plus UI native UI; permissions and trust stay at actual effect owners |
| `expo-web-to-native` | Missing incremental migration method with live native milestone and web/native false-friend mapping | Workflow mobile index and architect mobile-boundaries; UI/data/runtime references supply implementation |
| `expo-dev-client` | Missing Expo Go/development/release binary distinctions and dependency-change rebuild decisions | Language `references/mobile/expo-runtime.md`; CI `references/mobile/build-and-upgrade.md` |
| `expo-module` | Missing config plugins, autolinking, native view/module shape, registration and lifecycle/subscription ownership | Architect mobile-boundaries; language Expo runtime plus existing Swift/Kotlin leaves |
| `expo-brownfield` | Missing integrated versus isolated artifacts, host compatibility, native navigation and release verification without Metro | Architect mobile-boundaries; CI build-and-upgrade |
| `expo-app-clip` | Missing target/bundle/entitlement/association and size/distribution boundary | CI `references/mobile/distribution.md`; architect/native language contracts as needed |
| `expo-upgrade` | Missing SDK/React/RN compatibility sequence, CNG/manual native ownership, old-media migration, native tabs, compiler and architecture transitions | CI build-and-upgrade plus language Expo runtime; preserve patch rationale and rollback |
| `expo-examples` | Comparative research already covered; add SDK-matched canonical example selection and source-to-real-app mismatch check | Existing research comparable-implementations and upstream review; mobile index cross-link |
| `eas-app-stores` | General release evidence covered; concrete native binary, signing, submission, metadata and store/track states missing | CI distribution; retain Apple/Google/native-iOS distinctions and review evidence |
| `eas-update` | Missing build/update/platform/runtime/channel/branch/environment identity and activation lifecycle | CI `references/mobile/updates-and-health.md`; native changes require compatible new binary |
| `eas-update-insights` | Missing group/channel/runtime-cohort denominators, crash/adoption/payload interpretation and schema differences | CI updates-and-health; no-data and incompatible-cohort controls, no universal numeric thresholds |
| `eas-observe` | Missing startup/launch/TTI metric boundaries, client integration and scoped queries | CI updates-and-health plus existing performance playbook/backend observability owner |
| `eas-workflows` | CI trust/artifact policy covered; EAS YAML, installed schema, environment and job dependencies need examples | CI `references/mobile/workflows-and-hosting.md`; no cloud run implied by editing YAML |
| `eas-hosting` | Missing Expo Router API request/runtime and deploy alias/environment distinctions | Backend `references/expo-api-routes.md` and CI workflows-and-hosting; no client secrets |
| `eas-simulator` | Generic resource ownership covered; remote/local simulator choice, session IDs, crash logs and native drive loop missing | Workflow mobile-engineering index owns session/cost/lifetime/handoff; TDD `references/mobile-verification.md` owns qualification |
| `expo-experiments/.../expo-migrate-module` | Experimental legacy bridge migration, not stable automatic migration | Conditional section in architect mobile-boundaries and language runtime; preserve API/events/config, native compile and behavior controls |

Retain useful SDK recipes and service methods in these references; do not exclude
them merely because they are Expo-specific. Cloud availability, plans, credentials,
privacy and publication are qualification/authority boundaries, not reasons to
discard the capability from the plan. Conversely, no Expo migration is proposed
for unrelated bare RN, Swift, Kotlin, web or desktop projects.

Supporting scope includes Router route/tab/sheet/zoom/search/header references;
native UI icons/gradients/media/storage/effects/WebGPU; all four Expo UI API
families; animation recipes; offline/cancellation/loaders; module/config-plugin/
view/lifecycle references; six brownfield references; seven upgrade references;
web-to-native assessment/run/native-pattern/device controls; six store references;
simulator operation/troubleshooting/logs/controllers; update-insight schemas;
Observe setup/metrics/queries/integrations; example catalog; App Clip native module;
workflow schema fetch and component-list scripts. Each needs a per-file
adapt/covered/exclude decision before any future import. Their contents cannot be
treated as optional just because only SKILL.md entrypoints are listed above.

### Upstream inconsistencies and support-code decisions

These are source observations, not reproduced runtime defects. Resolve them in
the adaptation rather than copying the source's strongest wording.

| Finding and pinned source anchor | Required plan treatment |
| --- | --- |
| Expo overview `expo-overview/SKILL.md:35` references absent `expo-tailwind-setup`; internal runtime matrix lists it too | No fictitious route. Existing NativeWind/Tailwind keeps its installed stack; add version-aware styling within native UI when relevant. Check both intended-capability reachability and declared-destination existence. |
| Internal eval `references/runtime-matrix.md:28` suggests Observe in Expo Go; `eas-observe/SKILL.md:12` requires development/production build | Check actual installed native package and matching binary; incompatible Expo Go is a negative control, not a screenshot-only pass. |
| Internal eval `scripts/snapshot-android.sh:58–59,93–97,111–114,177–178` kills port listeners, broad qemu processes and shared adb | Do not reuse cleanup. A future capture helper carries owned PID/session/device identity, refuses foreign-resource cleanup, retains failures and stops only its resources. |
| Internal eval assumes Claude subprocesses, global plugin disable and host-specific permission workarounds | Keep supported host/model and isolated candidate context; no permission bypass or silent global-discovery changes. |
| `scripts/ci.sh:17–31` relies on private/token-scoped harness; `scripts/ci.py:13` names absent baseline-promotion design file | No benchmark-reconstruction claim. Readable wrappers inform local design; unavailable evaluator/dataset/results remain unverified. |
| Public `scripts/ci.py` fingerprints skills/harness/scenario/prompts/model; main-baseline workflow separates trusted producer from PR restore-only consumer | Extend optional result-reuse integrity in existing eval guidance: full input/environment identity, cache authority and manifest checks. Build no cache system without a real requirement. |
| Component-list script parses declarations; workflow fetch helper writes remote schema/cache under skill without explicit response budget | Prefer scoped installed-export reads and pinned schema bytes. A justified parser/fetcher needs export-shape, timeout/size/path tests and task-owned ignored output. Parser success is not runtime support. |
| Mobile data wording overstates automatic cancellation; connectivity can be unknown | Require actual signal consumption/current-generation guard; distinguish link connectivity from demonstrated service reachability. |
| Web-to-native payment advice mandates vendor and broad fee/IAP rules; App Clip advice mirrors parent permissions | Keep a requirements/platform-policy decision using current official evidence, not copied commercial/legal defaults. Select least-needed per-target permissions and test denial/recovery. |
| Repeated feedback commands can upload reports; animation sync follows moving upstream ref | No automatic feedback publication. Pin reviewed source and preserve notices; moving sync is an update lead, not reproducible implementation evidence. |

Expo's `scripts/sync-animate-expo.ts` documents the shared animation lineage.
Recipes are close but not identical; compare actual deltas, retain applicable
notices from both sources, and maintain one mobile motion method.

The internal eval skill, two rubric/applicability references, visual grader and
nine scripts inform evaluation design; they are not product skills to import.
Add requested-screen navigation, wrong-screen/blank/error controls, source/binary
applicability, trusted fixture-cache identity, device/shared-build resource
ownership and per-platform required evidence to our existing evaluator guidance.
An initial-route screenshot cannot qualify an arbitrary task. Numeric visual
scoring cannot certify accessibility. Missing infrastructure/capture/platform
results remain not-run/blocked, not smaller denominators or product failures.

### Emil: complete entrypoint disposition

Source paths are `skills/<name>/SKILL.md` at the pinned revision.

| Source entrypoint (support) | Finding and selected improvement | Owner |
| --- | --- | --- |
| `emil-design-eng` | Partial ordinary UI motion depth; umbrella overlaps existing design owner | UI general motion/performance references |
| `animate` (`RECIPES.md`) | Add construction sequence, readiness, origins, exit lifetime, takeover and reduced-motion continuity | UI `references/motion.md` |
| `animate-expo` (`RECIPES.md`) | Same mobile motion family as Expo source; compare real differences and retain both attributions | One UI mobile motion reference, no duplicate owner |
| `review-animations` (`STANDARDS.md`) | Add source/interaction/evidence-shaped review; distinguish accessibility/behavior defect from taste | UI motion reference and existing engineering-scope review rules |
| `improve-animations` (`AUDIT.md`, `PLAN-TEMPLATE.md`) | Existing plan/review workflow covered; add motion inventory and measured plan particulars | UI motion/performance; existing workflow |
| `find-animation-opportunities` | Purpose is covered; add contextual frequency/restraint and legitimate no-change outcome | UI motion |
| `animation-performance` (root cheatsheet) | Add driver/property/concurrent-work/trace diagnosis; source property is not GPU proof | UI `references/animation-performance.md`, existing perf playbook |
| `animation-vocabulary` | Small terms useful for precise feedback; no new invocation or closed vocabulary | Short glossary inside UI motion |
| `apple-design` | Add current presentation/velocity takeover, touch ownership and platform accessibility preferences | UI motion/native UI, preserving target tokens |
| `write-swift` | Existing concurrency leaf is shallow; deepen value/reference semantics, continuation races, view/task lifetime, dispatch and version-aware testing | Existing language Swift leaf; compiler-qualified examples |
| `pick-ui-library` | Existing stack selection covers decision; selected dependency fit examples only | Existing stack-selection, no default package changes |
| `prototype` (`PICKER.md`) | Core preview covered; same-scale comparison/replay and accessible selection need specific cases | Existing prototypes/visual-direction; no forced variant count or picker style |
| `mobile-native` | Add capability-based mobile-web input, viewport/keyboard/safe areas, scroll and selection mechanics | UI `references/mobile-web.md`; distinguish from native Expo |
| `break-ui` (`CATALOG.md`) | Add reproducible schema-backed adverse fixtures through real data interface | UI `references/stress-fixtures.md`; TDD for lasting failure regressions |
| `ask-sonner` (`API.md`) | Add generic notification identity/result ownership where needed; exact dependency APIs only if target uses it | Existing async-state/UX, optional version-checked notification section |

### Supplied workflow: visible observations and disposition

| Observation | Existing coverage | Residual change or exclusion |
| --- | --- | --- |
| F01 stateless coordinator/current cause table | autonomous-run reads source/refs/PRs | Define external-state precedence, freshness and conflicting observations |
| F02 root/cause/test-name input | CI preserves test/attempt identity | Scope cause key by repository/root; disambiguate ambiguous test names |
| F03 family query/status/assignee/markers | CI requires complete collection | Extend conditional tracker example with pagination, partial access and stale-marker cases |
| F04 start-work assignment as claim | one current writer/head lease | Read back authorized claim, honor conflict; no assertion that assignment is atomic exclusion |
| F05 deterministic evidence JSON plus model analysis | offline CI analyzer/hypothesis separation | Carry observation IDs/hash into cause explanation; no invented evidence |
| F06 cause-oriented grouping | pipeline diagnosis already shares causes | Worked many-to-many test/symptom/cause example, not one issue per failed test |
| F07 fixed-title investigation page | optional task record already exists | Keep existing record; no new Confluence page, mandatory format or title-as-identity rule |
| F08 tickets/routing/dedup labels | general ownership/idempotency exists | Stable key plus actual remote ID/readback; reconcile unknown write outcome before retry |
| F09 routed cause disposition | boundary/owner mapping exists | Routed is not resolved; retain actual destination, acknowledgment if observed, and uncertainty |
| F10 confident/best-guess proposal | evidence-led hypotheses exist | Confidence must cite support, counterevidence and next discriminating check |
| F11 cause worktree/plan-derived diff | already explicit | Retain; no extra worktree machinery or mandatory ticket per branch |
| F12 council/adversarial rubric | interrogate/review already exist | Use risk-directed review, reject compulsory councils and self-labelled independence |
| F13 one approved stage at a time | inherited authority already explicit | Keep meaningful effect boundaries; reject repeated approval of already-authorized work |
| F14 return/re-derive after every stage | continuation refresh exists | Reconcile partial effects before next dependent action; no orchestration runtime |
| F15 fixed two review rounds | bounded loops already exist | Keep cause-specific/consumer budgets, no universal two-round limit |
| F16 PR/merged/routed/open end states | delivery states already explicit | Add compact cause-handoff example linking actual candidate and remaining gate |

## Implementation design and contracts

### C1. Conditional mobile routing

Start from user goal, manifests/lockfile, Expo/RN and native toolchain versions,
platforms and actual native directory ownership. Expo-specific references apply
to explicit Expo work or demonstrated Expo dependencies; EAS-only delivery can
apply to an otherwise native application. A generic mobile request with no selected
stack goes through existing stack-selection, not automatic Expo scaffolding.

The mobile workflow index points directly to existing UI, architecture, language,
backend, TDD and CI owners. Load only the requested family. Dependencies must be
selected through the project's package manager and SDK-compatible mechanism,
not blind latest installs. Inspect config-plugin/CNG/manual native edits before
generation; directory presence alone is not sufficient proof of ownership.

### C2. Real mobile implementation depth

Include small SDK-qualified examples for controls/navigation, route/native host
boundaries, worklets and gesture cancellation, network/cache/foreground ownership,
DOM/native serialization, native modules/views and incremental web-to-native work.
Preserve actual contracts through callers and native hosts. Safe area, keyboard,
accessibility text size, RTL, focus, back navigation, permissions, deep links and
offline/error recovery must be connected to the same component and binary under
test. Destructive gestures require a cancellable, accessible commit mechanism.

Keep source-guided Swift/Kotlin language correctness at language owners. Do not
turn Swift features or Reanimated 4 APIs into universal target defaults. Native
module migration remains conditional/experimental until representative bridge,
event, view and lifecycle contracts pass on the target toolchain.

### C3. Mobile release and operation

Bind source, bundle/package ID, native binary, platform, build profile,
environment, runtime version, update group, channel/branch and store/track to
the claim being made. An OTA update cannot add a native capability to an old
binary. A downloaded update is not necessarily activated; a dev client does not
qualify release startup behavior. Build success, submission acceptance, TestFlight
availability, store approval, rollout and observed health are separate states.

Use version-current CLI/schema discovery and privacy-aware diagnostic recipes,
but never auto-link an account, create credentials, start paid cloud sessions,
upload builds, change a production channel or enroll telemetry from a skill read.
Reuse only owned sessions and stop only owned resources. Health comparisons need
the same cohort/window/denominator and enough observed traffic; missing data is
unknown, never zero crashes. Preview qualification is distinct from production.

### C4. Motion and adverse inputs

General UI motion states purpose, trigger, driver, properties, concurrent workload,
interruptibility, current-value/velocity takeover, exit/resource lifetime, input
and reduced-motion behavior. Layout/paint/composite/React work is diagnosed with
the relevant trace and completed interaction, not inferred from a screenshot or
`transform` spelling. Preserve focus, semantic hidden state and task admission.

Adverse fixtures map real fields to actual constraints and inject deterministic
synthetic values through existing fixtures/data interfaces into real components.
Cover long/missing/Unicode/RTL/money/count/date/media/collection/pending/error
inputs as relevant; retain field-level wrap/truncate/full-access decisions and
reproduction seed. Do not introduce a permanent debug route or change production
validation merely because a schema lacks an explicit length cap.

Notification feedback must preserve stable operation identity, update the
intended surface without duplicates, fence stale async completion and keep durable
outcomes available after a toast disappears. Supported reduced-transparency and
increased-contrast preferences need readable solid/high-contrast fallbacks; no
unsupported universal CSS/native setting is prescribed.

### C5. Cause handoff without another tracker

Extend existing pipeline diagnosis/task records only for multi-cause work that
benefits from it. A compact record needs repo/root/cause identity, observation
pointers, hypothesis/counterevidence/confidence, owner, disposition, actual
work-item/PR IDs, checked candidate, allowed effects and next discriminating action.
Use a paragraph or existing issue fields when sufficient; JSON and a new helper
are not mandatory. Validate before any authorized write, read back identity,
reconcile ambiguous completion and avoid duplicate creation on replay. Respect
foreign claims; local markers and labels are hints, not ownership or completion.

### C6. Selective source adaptation

Before implementation imports anything, classify every relevant reference/script:
already covered, adapted text/example, deliberately maintained executable, excluded
with reason, or blocked qualification. Prefer local prose plus minimal synthetic
fixtures. Only import a helper if it solves a demonstrated task and its dependencies,
I/O, network, errors, cancellation, notices and upkeep are accepted. Do not vendor
Expo's internal model/evaluation runner, remote schema-fetcher or component-list
script simply to achieve an upstream file count. A useful omitted capability still
needs a maintained local equivalent or an explicit open gap.

## Ordered implementation units after approval

One lead owns integration; Skills Builder owns the approved writing slice, and a
separate reviewer checks a frozen candidate when that collaboration is authorized.
At most the resolved harness limit of bounded children, resolved tiers unchanged. Roles below name
responsibility, not a new chat or permission to message anyone.

| Unit | Owner and concrete files | Dependencies | Completion condition |
| --- | --- | --- | --- |
| P0 source/contract lock | Skill maintainer: this plan; selected provenance/notices; existing catalog/README only if needed | Approval to implement | Every entrypoint/support family disposition recorded; exact licensed adaptations and fixture inputs allowlisted; protected nesting/default/holdout baselines captured |
| P1 mobile routing/runtime | Workflow mobile-engineering index; language mobile/expo-runtime; minimal existing SKILL links | P0 | Expo/EAS/native-only/non-Expo routes correct; SDK/config/native ownership and dev/release distinctions explicit; no setup or model changes |
| P2 mobile screen/data vertical slice | UI mobile/native-ui, navigation, data-and-lifecycle; architecture mobile-boundaries; existing async/RTL owners | P1 | A real Expo fixture covers navigation + native controls + cancellable data/error recovery with relevant input/accessibility boundaries; source trace alone is labelled |
| P3 motion, touch and stress | UI motion, animation-performance, mobile-web, stress-fixtures and mobile/motion; prototype/async refinements; perf/TDD links | P1; P2 for integrated Expo fixture | Ordinary UI and Expo motion share principles but retain separate drivers; deterministic adverse fixtures exercise the same components; interruption and busy-load negative controls discriminate defects |
| P4 native extension/migration | Architect mobile-boundaries; language Swift/Kotlin/Expo runtime; UI native media/DOM sections | P1–P2; version check before APIs | Module/view/config-plugin and brownfield integrated/isolated methods covered; web-to-native and experimental bridge migration retain behavior and explicit native qualification gaps |
| P5 build, upgrade, release and services | CI mobile/build-and-upgrade, distribution, updates-and-health, workflows-and-hosting; backend expo-api-routes; TDD mobile-verification | P1; P2/P4 identify affected binary/contracts | SDK/native generation recovery, stores/App Clip, OTA activation/compatibility, health cohorts, workflows/hosting/remote simulator guidance complete; no real-service writes required to validate prose |
| P6 cause-oriented handoff | Existing how/pipeline-diagnosis, CI/bulk-failures, workflow/task-record and autonomous-run; one synthetic example | P0; independent of P1–P5 | Duplicate/partial-write/conflicting-claim/stale-state/routed-not-resolved cases are explicit without a Jira/Confluence framework |
| P7 evaluation and integration | Existing skill-creator eval suite/protocol, relevant fixture tests; skill provenance/catalog/discovery/manifest; README | P1–P6; cases drafted alongside each unit | All changed contracts have positive and adjacent/failure cases; route map checked in both directions; capture target/error controls and result-reuse integrity specified; static/helper/native/agent evidence separated; exact candidate reviewed; unresolved qualifications listed without claiming closure |

P2 is the first complete risky vertical slice before scaling the full family;
P4 and P5 must still be completed, not silently dropped if that slice succeeds.
P3/P6 may proceed independently within their listed dependencies. Preserve owned
outputs and consumer changes; revert only this candidate's reviewed file allowlist
if a reference/import proves unsuitable. No production rollback is performed.

## Acceptance and evaluation cases

These are proposed cases, not executed tests or benchmark results. Implementers
should split a row into focused fixtures where it contains different mechanisms.
Keep negative controls at the actual claimed boundary, not a copied stand-in.

| ID | Task and required behavior | Failure/adjacent control and evidence |
| --- | --- | --- |
| M01 | Expo UI request detects actual SDK, package manager and native ownership; loads only relevant references | Plain web/bare RN/Swift task does not get Expo scaffolding; EAS-only native release does not get an Expo runtime install |
| M02 | Existing manually edited native tree survives upgrade planning; generated configuration has explicit owner and recovery | Automatic clean prebuild or deletion of native edits is a failure; disposable generated fixture tests regeneration separately |
| M03 | Native controls and large list remain usable with text scaling, safe areas, RTL, keyboard and platform theme | Grouped row container passed off as virtualized large list fails; browser-only image cannot establish iOS/Android behavior |
| M04 | Router deep link/auth redirect/tab/sheet/back flow preserves intended history and selected identity | Warm/cold deep link, cancellation and stale route owner controls; generic route-name prose is insufficient |
| M05 | Gesture continues under busy RN JS on the supported UI runtime; pointer identity, release velocity and snap choice remain correct; one commit | Takeover/multitouch/cancel/unmount/stale callback/reduced-motion controls; haptics disabled/unavailable keeps complete visible feedback; effects happen at threshold/end, not each frame |
| M06 | Offline request/cache scope and foreground recovery preserve account/tenant identity and stale-result guard | Sign-out/account switch, late response, reconnect and duplicate mutation controls; simulated network is not deployed API proof |
| M07 | DOM/native bridge serializes supported data and preserves measured layout/input/asset behavior | Unsupported function/object transfer, unsafe origin/message and unsupported native APIs; device versus web receipts distinct |
| M08 | Native module/view owns subscription, cancellation, thread/actor and teardown; config registration is real | Unmount/callback race, duplicate listener, missing native binary symbol, permission denial; actual native compile and event checks required |
| M09 | Brownfield host passes initial props, gets exactly one correlated result, cancels through RN/native/back/swipe and reopens with fresh input | No stale listener/result; isolated/integrated artifact compatibility; matching Release host/artifact runs with Metro stopped; debug server success is insufficient |
| M10 | Web-to-native plan reaches runnable shell then replaces high-value screens without losing auth/data/navigation | False friends for CSS/DOM/storage/native input; compilation-only migration claim fails; representative iOS and Android cells named |
| M11 | SDK/media/compiler/architecture migration uses compatible versions, respects patch rationale and validates actual affected builds | Unsupported API on pinned old SDK or incidental language/compiler mode change fails; unrun platforms remain open |
| M12 | Store/App Clip guide identifies binary IDs, entitlement/association, versions and distribution stage | Build/upload/submit/approved are distinct; App Clip AASA/parent association and native-module contract checked; no unauthorized upload |
| M13 | OTA plan matches platform/runtime/channel/branch/environment and real binary; checks activation lifecycle | Native dependency addition with old binary is rejected; downloaded-not-activated, incompatible runtime and preview-vs-production controls |
| M14 | Health report uses correct update group, cohort, window and denominator; downloads are distinguished from launches and people | Delayed/self-reported failures, top-N OTA undercount and cross-platform duplicate people remain explicit; no samples/partial/mismatched cohorts are not zero crashes; no universal threshold |
| M15 | Workflow/hosting/API example validates installed syntax, artifact/environment identity and real request authority | Untrusted PR secret access, EXPO_PUBLIC secret assumption, wrong alias and stale artifact controls; no actual deploy required for source claim |
| M16 | Simulator workflow uses dev binary for live iteration or source/fingerprint-matched static artifact; owns exact session/device/app/logs and preview lifetime | Foreign session preserved; preview URL differs from simulator deep link; token dotenv ignored; owned cleanup/expiry only; unavailable access is blocked, not green; cloud effects stay scoped |
| U01 | Menu/sheet follows trigger origin after edge collision; current presentation/velocity survives rapid reversal and pointer-ID/multitouch ownership | Teleport/stale-exit/focusable-hidden/duplicate-commit controls; correct focus and snap; reduced-motion can retain immediate final state |
| U02 | Performance correction compares same workload/completed interaction with relevant trace; layout, hit testing and text readability remain correct | Screenshot-only/GPU-by-property claims fail; transform cannot silently change semantics; will-change requires measured need and bounded lifetime |
| U03 | Mobile web supports hybrid input, cancellable activation, zoom/selection, keyboard/safe area/viewport and nested scroll | Pointerdown destructive commit, global touch-action/zoom suppression and unreachable action fail; emulator versus device scope recorded |
| U04 | Same component/data boundary accepts seeded schema-valid extreme Unicode/RTL/text/count/money/date/media/collection/error fixtures | Copied toy UI, western-only initials, title-only full-value access, production data/debug leakage and invented schema limits fail |
| U05 | Swift examples preserve nested-reference semantics, actor suspension invariant, continuation exactly-once and view task lifetime on declared toolchain | Race/cancel/default-dispatch controls; unverified newer Swift syntax cannot be called compiler-qualified |
| U06 | Equal-scale alternatives differ on named design axis; selection/replay is keyboard/touch/focus safe and cleanup correct | Focused text input shortcuts ignored; rapid remount cancellation works; no forced three variants, fixed glass picker or default package swap |
| W01 | Same cause maps many tests; identical symptom may have different causes, with source evidence and counterexample | Keyword cluster or model confidence alone cannot establish cause; original attempts and missing inventory preserved |
| W02 | Authorized work-item replay reconciles stable key and actual remote ID before retry after lost response | Duplicate label, ambiguous completion, stale title, pagination gap and cross-repository collision controls; connector stub is not live tracker proof |
| W03 | Current claim/head/PR state wins over stale local marker; foreign owner blocks takeover; routed remains unresolved | Conflicting assignment, late child, merged PR, missing read access and late write controls; no claim of atomic exclusion without actual API mechanism |
| W04 | Research-only request ends with findings; authorized implementation continues routine work; no-merge endpoint holds | No automatic Jira/Confluence writes, councils, provider changes or per-stage approval ceremony; scope tested through visible actions |

Additional proposed cases:

| ID | Task and required behavior | Failure/adjacent control and evidence |
| --- | --- | --- |
| M17 | Experimental module macro migration checks paired macro/core support and preserves JS names/events/defaults/requiredness/static placement, queue and error meaning | Retain unsupported DSL; reject duplicate registration/hooks, missing core or changed pre-first-await execution; actual running-app module lookup and TS/native roundtrip required |
| U07 | Supported reduced-transparency/increased-contrast preferences keep useful feedback and readable solid/high-contrast surfaces | Unsupported preference is recorded, not invented; decorative material cannot hide controls/readouts; rendered/native evidence on claimed surface |
| U08 | Notification stable-ID update/unmount/retry preserves one current operation and intended multiple notification surfaces | Stale completion cannot replace current result or duplicate feedback; durable outcome remains elsewhere; exact Sonner API only if installed/version-checked |
| E01 | Mobile evaluation reaches requested screen and binds capture to source/binary, fixture, runtime and device | Root screen instead of requested flow, blank/error/dialog, old binary or incompatible Expo Go invalidates claim; missing required platform stays incomplete |
| E02 | Reused result matches exact skill/harness/scenario/model/tool/SDK/environment and trusted provenance | Reject stale/tampered/foreign/PR-promoted baseline; natural routing cannot inherit candidate skills; no shared-cache implementation mandated |

### Evidence ladder and comparison protocol

1. Static library/source checks: notices, provenance, links, conditional routing,
   catalog/discovery/manifest and validation of proposed evaluation definitions.
2. Deterministic helper/fixture checks only where executable content is changed:
   input/identity/cancellation/error controls and before/after production-boundary
   regressions. Simulated tracker/network/OTA records cannot establish live services.
3. Real render/native cells: web interaction and busy trace; Expo iOS simulator and
   Android emulator/device on named SDK/React/RN/build/OS versions; release startup
   where claimed. Physical keyboard/haptics/performance/accessibility and signing/
   store/cloud services retain their own observed or unqualified status.
4. Agent trials: use the [existing evaluation protocol](../../skills/orbyn-skill-creator/references/evaluations.md).
   Baseline is this merged main; candidate is a frozen future commit. Same host,
   model/effort/processing, tools, fixture bytes, permissions, context isolation and
   task budget in both conditions. Detect installed-skill/plugin leakage without
   silently editing global configuration. Separate natural routing from explicitly
   instructed execution and artifact quality. Preserve existing holdouts unchanged.

Initial proposed paired pilot: eight tasks (M01, M02, M05, M13, U01, U04, W02,
W04), three trials each per condition: **48 executions**. This is an initial
decision pilot, not sufficient qualification for all 31 case groups or every Expo
capability. Grade task correctness, harmful/unauthorized actions, source/version
accuracy, recovery, selected references and observed time/tokens; unknown usage is
null. No authority breach is acceptable. Retain failures/timeouts; publish actual
counts and uncertainty rather than inventing a quality-gain target. Broader claims
require fresh cases across the remaining families and held-out observations after
the candidate is frozen. A readiness probe must confirm the exact supported host
and defaults before any pilot; unavailable capacity remains openly blocked.

## Rules to adapt critically

- No universal timing/easing/frequency, preferred-library, always-haptic or always-
  animate policy. Treat these as contextual craft choices; accessibility and task
  continuity outrank author taste. Core Animated, CSS, WAAPI and platform controls
  remain valid where they meet the actual contract.
- Prefer cheap rendering where appropriate, but do not promise GPU acceleration
  from property names or replace layout with scale without checking semantics.
- Press feedback may start on down; committing the action must remain cancellable
  and keyboard accessible. No global zoom, selection or scroll suppression.
- Keep version and architecture gates on Expo UI, Router, Reanimated/Worklets,
  Swift and native APIs. Missing upstream paths or stale examples are research
  leads, not instructions to invent an API or rewrite a consumer.
- No mandatory 4–8-agent audit, imported model presets, councils or repeated stage
  approvals. Keep one canonical owner and the current bounded delegation policy.
- No automatic plugin installation, upstream feedback posting, issue creation,
  production update, remote simulator launch, signing enrollment or telemetry.

## Delivery and remaining uncertainty

The original research ended with this local proposal. Subsequent user approval
authorizes P0–P7 implementation and local review, with commit held for independent
clearance. New PR/push/merge and consuming-project changes remain outside scope.
The merged PR #40 is separate and done.

After approval, deliver the full P0–P7 implementation with focused cases, licensed
adaptations, required library checks and a reviewable exact candidate. Clearly list
every blocked native/cloud/store/agent qualification. Guidance can be verified
without claiming that every paid service, OS, device or runtime was exercised.
Do not silently mark these open qualifications complete or shrink the planned
capability coverage to whichever fixture is easiest to run.

Main uncertainty is future consuming-app SDK/platform/service availability and the
uninspected evaluation submodule, not whether Expo offers valuable mobile methods.
The friend workflow's operational quality is unknown beyond its screenshot.
The upstream collections' documentation depth does not prove a measured model
advantage. Evaluate the resulting changes against the pinned baseline before
claiming improved agent behavior.

## Research delivery verification

The two bounded source investigators reviewed this proposal against their own
source slices. Their missing-case findings were incorporated: experimental macro
capability pairing, correlated brownfield cancel/reopen, EAS metric traps, binary/
session identity, notification ownership, gesture velocity/pointer ownership and
platform accessibility preferences. This is source/plan review, not independent
runtime qualification of a future implementation.

`/opt/homebrew/bin/python3.13 scripts/check-library.py` passed: 36 skills,
284 Markdown documents, links, provenance/licenses, host assets, presets,
evaluation definitions and manifest. The first generic `python3` invocation in
the worktree resolved below the validator's required floor and did not run the
validator; the explicit installed 3.13 runtime above corrected that harness choice.
Local proposal checks passed for 31 unique acceptance IDs, existing local links,
whitespace and pilot arithmetic (8 tasks × 3 trials × 2 conditions = 48).

The plan is the only new worktree file, on local branch
`docs/ui-mobile-workflow-research`. It is not committed or pushed. Primary main
remains clean at merged `4e7dbe0`, matching remote main; post-merge GitHub run
`40658205194` passed both Python 3.11 and 3.13 validation jobs. Raw source and
research reports are ignored. No future skill improvement, runtime compatibility,
device test, model trial or service outcome is claimed as completed.
