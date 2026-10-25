# Fullstack engineering capability audit — 25 October 2026

Scope: improve the uncommitted 34-skill consolidation, address its observed
writer-fencing omission, and cover junior/senior/staff responsibilities across
backend, frontend, UI/UX, prototypes, verification, operations and resource cleanup.
No commit, publication, consumer promotion or production action is authorized.

The catalog remains 34 skills. The changes strengthen existing task owners and
conditional methods; job levels are not additional entrypoints or reduced quality
settings. This is a bounded capability map, not a claim that every engineering
specialism or organizational responsibility is now qualified.

## Research and decisions

Primary sources were inspected on 25 October 2026. The table distinguishes what
the source establishes from the library decision. No external code, templates,
visual assets or full text were imported. The maintained procedures are original
syntheses and remain usable offline. Sources are attribution and review pointers.

| Question | Source and finding | Local decision |
| --- | --- | --- |
| Can an API-only lock stop an old direct writer? | [PostgreSQL 18 advisory locks](https://www.postgresql.org/docs/18/explicit-locking.html#ADVISORY-LOCKS) are cooperative; the database does not require callers to acquire them. | Require the actual enforced boundary and bypass inventory in the migration deliverable. |
| Does an expired lease exclude a paused process? | [Kleppmann, 2016](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) explains delayed writers and resource-side fencing. | Define when the durable fence becomes effective and test stale effects after cutover; a token alone is insufficient. |
| Is reverting code sufficient after a format change? | [AWS deployment compatibility, 2019](https://aws.amazon.com/builders-library/ensuring-rollback-safety-during-deployments/) discusses compatibility during both forward and backward transitions. | Distinguish exposure, code rollback, stored-data recovery and later writes; rehearse compatible recovery. |
| What changes with engineering responsibility? | GitLab's [associate](https://handbook.gitlab.com/job-description-library/engineering/development/backend/associate/), [senior](https://handbook.gitlab.com/job-description-library/engineering/development/backend/senior/) and [staff](https://handbook.gitlab.com/job-description-library/engineering/development/backend/staff/) descriptions combine execution, collaboration and review; broader roles add scope, standards and mentoring. | Provide a task-scope/learning guide, not a universal career ladder, employee assessment or title-based authority. |
| How do large changes become adoptable? | [Google large-scale changes](https://abseil.io/resources/swe-book/html/ch22.html) addresses incremental changes, cross-team review and preventing backsliding. | Extend strategy with one consumer pilot, adoption/support ownership and independent release compatibility. Existing staged migration remains its own method. |
| What should review transfer? | [Google code review](https://abseil.io/resources/swe-book/html/ch09.html) treats review as both quality control and knowledge sharing. | Add ordinary review/coaching guidance with concrete findings, questions versus preferences and rationale at the owning artifact. |
| What defines an operable service? | [Google SRE SLOs](https://sre.google/workbook/implementing-slos/) relates user-relevant reliability indicators to decisions; [incident response](https://sre.google/workbook/incident-response/) separates restoration from coordination. | Add service readiness and strengthen incident handoff/aftercare. Existing observability, performance and rollout methods remain owners of mechanisms. |
| How can a person evaluate an interface? | [GOV.UK prototyping](https://design-system.service.gov.uk/get-started/prototyping/) uses rendered components; [MDN local testing](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Tools_and_setup/set_up_a_local_testing_server) distinguishes local files from server-dependent behavior. | Deliver an existing app route/story or self-contained HTML with opening path and working state transitions. Do not mandate a framework or confuse a mock with product integration. |
| What can preview checks establish? | [W3C preliminary checks](https://www.w3.org/WAI/test-evaluate/preliminary/) are explicitly limited, not complete accessibility evaluation. | Separate source, rendering, interaction, native evidence and human usability research. |
| When can local resources be removed? | [Git worktree documentation](https://git-scm.com/docs/git-worktree) distinguishes checkout removal and registration; [Compose teardown](https://docs.docker.com/reference/cli/docker/compose/down/) distinguishes normal teardown and explicit volume removal. | Retain pending review/valuable ignored data; identify owned processes and data before scoped cleanup. A merge or clean status is not sufficient. |

## Coverage, gaps and implementation

“Existing” means a maintained local method was found, not demonstrated mastery.
“Strengthened” means a concrete method/output gap was corrected in this change.
Live evaluation status belongs to the linked reports, not this coverage label.

| Capability | Owner / local method | Disposition and practical result |
| --- | --- | --- |
| Discover source, history, ownership and runtime edges | `how`, `why`, impact map | Existing; source/deployment uncertainty already explicit. Large actual monorepo tracing remains unqualified. |
| Bounded contribution, onboarding and constructive review | [Workflow scope](../../skills/orbyn-workflow/references/engineering-scope.md) | Strengthened: one working path, understandable invariant/check, defect versus preference, coaching versus implementation scope. |
| Product problem and technical investment | `orbyn-plan`, [strategy](../../skills/orbyn-plan/references/technical-strategy.md) | Strengthened: no-change/smaller option, decision owners, opportunity cost, adoption/support and knowledge transfer. |
| Architecture and module/API evolution | `architect`, large changes, maintainable modules | Existing plus explicit durable-writer handoff; ownership and independently released consumers remain central. |
| Backend effects, authorization and concurrency | `orbyn-backend-design`, service contracts, observability | Existing; sampled effect behavior does not qualify every engine/provider. No new security scan. |
| Stored data and writer transition | [Migration writer cutover](../../skills/orbyn-data-migration/references/writer-cutover.md) | Strengthened after actual omission: writer/version inventory, enforced admission, bypasses, old/new controls, recovery and readiness decision in the final deliverable. |
| Frontend state and integrated task flow | `orbyn-ui-design`, async-state, fullstack contract | Existing recovery methods plus explicit prototype-to-real-API transfer, permission/error states and removal of demo scaffolding. |
| UI/UX, content and accessibility | `orbyn-ui-design`, `orbyn-content-design` | Existing task/recovery/layout/copy methods; representative-user research and full accessibility conformance remain separate. |
| Prototype and human preview | [UI prototypes](../../skills/orbyn-ui-design/references/prototypes.md), workflow prototype | Strengthened: choose app route/story or portable HTML, working states/reset, simulation labels, actual link, open/render evidence and integration limits. Replaced the prior React/React Native assumption. |
| Test strategy and language correctness | `tdd`, language guides | Existing: real boundary, failing-before, negative and legitimate controls, meaningful fixture ownership. No need for a separate junior testing skill. |
| Performance, capacity and reliability | Workflow performance, [service readiness](../../skills/architect/references/service-readiness.md) | Strengthened: user completion indicator, denominator/window, workload/quota, admission/retry bounds, privacy/retention and recovery objectives. Unknown targets remain unknown. |
| CI, supply-chain execution and release | `orbyn-ci-design`, affected targets, release verification | Existing privilege separation, pinned inputs, exact artifact evidence and broad fallback; no new deployment authority. |
| Incident management and learning | [Rollout/recovery](../../skills/orbyn-ci-design/references/rollout-recovery.md) | Strengthened: operational/incident/communication owners, factual timeline, handoff, user/data closure and owned prevention work. No automatic messages. |
| Storage, development environments and cleanup | [Artifact lifecycle](../../skills/orbyn-workflow/references/artifact-lifecycle.md), `orbyn-worktree` | Strengthened: task-scoped ignored output, retained preview/evidence, session/port/cwd ownership, shared-resource protection, preservation before removal and actual final resource state. |
| Dependency/technology decisions and updates | Stack selection, research, upstream review | Existing primary-evidence/version/ownership methods; target-specific compliance, licenses and operational policy still need consumer context. |
| Security assurance, native/hardware and specialized domains | Existing security and REA owners; consumer guidance | Remain scoped specialties. This work does not qualify medical, financial, safety-critical, embedded, ML/data-science or every infrastructure domain. |

## Responsibility model

For a bounded/junior contribution, success means understanding and completing a
small safe change with evidence and actionable help when blocked. Team/senior scope
adds ambiguity resolution, connected delivery and operation. Cross-team/staff scope
adds investment decisions, interfaces, adoption and enabling others. These are
useful task shapes, not titles the assistant can assign to people. Correctness,
privacy, authority and honest reporting apply at every scope.

Fullstack means the requested outcome can connect product intent, UX/content,
frontend state, domain/API, persistence, verification and operations. It does not
mean every task must modify every layer or that HTML prototyping is backend proof.
A static website can be complete without adding a server or database.

## Verification and remaining work

The [original comparison](../evaluations/2026-10-25-skill-consolidation.md) remains
unchanged: 17/20 baseline and 19/20 previous candidate, including its writer-fencing
omission. The follow-up completed 24 migration calls and
12 breadth calls on new scenarios, then six separate development rechecks after
three entrypoint corrections. See the [complete result and limits](../evaluations/2026-10-25-migration-followup.md).
Migration outcomes were 4/12 baseline versus 11/12 revised candidate; breadth was
1/6 versus 4/6. Remaining candidate omissions were recovery health gates, a normal
cleanup control and service retention/privacy. The corrected entrypoints passed
all three cases in the additional paired round (baseline 0/3, candidate 3/3).
Earlier failures remain recorded. The final candidate was not rerun across every
original case. No independent review or universal no-regression claim follows.

Command review showed `how` selected for coaching and backend design selected for
service readiness. The final entrypoints now hand those tasks to the appropriate
methods and state the necessary final-answer criteria. The recheck service answer
selected architecture directly, so its result does not isolate the backend-link
change. Active routing expectations now accept ordinary coaching through `how`
and a bounded rename through `orbyn-plan`; frozen evaluation scores stay unchanged.

The SQLite exercise uses real disposable storage and a separately authored oracle,
but excludes direct-SQL bypass and concurrent-fleet qualification. The HTML subject
has no browser and must report that limit; lead rendering observations are
recorded separately. New development cases are added without modifying existing
cases or holdouts. All new methods ship through existing owners and generated
host discovery. Research, methods and static checks alone do not demonstrate
full engineering capability.

Next validation beyond this pass should exercise a real multi-package candidate,
shared-environment teardown in a disposable integration fixture, native UI where
required, and independent review of representative outcomes. Do not convert these
remaining evidence gaps into claims of completeness or indiscriminately add skills.
