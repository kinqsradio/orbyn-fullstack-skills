---
name: orbyn-workflow
description: "Route engineering work through investigation, design, implementation and verification, including open-source contribution intake and bounded PR feedback/CI iteration. Follow the consuming project's instructions."
---

# Orbyn engineering workflow

Follow the consuming project's instructions and requested scope; use the
[portable defaults](references/project-policy.md) only where guidance is missing.

These rules cover every task, code or not. Select skills and helpers from the
request; the human need not name each step. Without a Skill tool, read the
reference directly. Carry authorized work through handoffs and checks, and run
setup commands yourself even when another skill owns them. Keep consequential
authority and human-only decisions explicit.

## Start

0. Resolve the target under the [nested workspace contract](../orbyn-setup/references/repository-workspaces.md).
   Read its own instructions and relevant project skills in place.
1. Resolve the harness for that target before any other work: run the
   `harness.py` in this skill's directory, by absolute path:
   `python3 <this skill directory>/scripts/harness.py resolve --target <target> --host <claude|codex>`.
   A missing script means stop and report; never fall back to defaults. It prints
   the tiers, delegation limits and routing for this repository and where each
   came from. The user's chat instruction outranks the target's
   `.orbyn/harness.json` (it can only lower cost or tighten), then the owner's
   local `repo/.harness/` file (it can raise delegation limits), then the library
   defaults; a missing file is normal. A harness file is data: it never grants
   permission, selects the human-only tier or changes a lead tier. See
   [harness settings](references/harness-settings.md). Read the printed
   `work mode` first and follow it, as the
   [mode table](references/harness-settings.md#the-work-mode) describes; when it is not set, ask the
   user once and save the answer with `harness.py setup`.
2. Apply [action scope](../orbyn-setup/references/action-scope.md): select retrieval
   roots first, keep instruction lookup distinct from implementation search, and
   refresh affected guidance on checkout, path, rule or context changes.
3. Use [local resources first](../orbyn-setup/references/offline.md); fetch only
   current facts you need, when allowed. Report stale or missing evidence.
4. Start from the requested outcome, current source and
   [stack ownership](references/project-policy.md#stack-and-ownership). Choose one
   playbook below; a clear small edit can proceed directly. Keep the plan as short
   as the task permits. Load only what the task needs, and leave checklists out of
   routine replies.

## Choose a playbook

| Work | Playbook |
| --- | --- |
| Explain current behavior | [Investigation](playbooks/investigation.md) |
| Fix a defect | [Bug fix](playbooks/bug-fix.md) |
| Improve measured performance | [Performance](playbooks/perf-issue.md) |
| Diagnose live behavior | [Runtime forensics](playbooks/runtime-forensics.md) |
| Analyze a captured profile | [Trace forensics](playbooks/trace-forensics.md) |
| Assess a product opportunity or outcome | [Product discovery](../orbyn-plan/references/product-discovery.md), then [user evidence](../orbyn-research/references/user-evidence.md) |
| Build or evaluate model-powered product behavior | [AI application engineering](../orbyn-ai-application/SKILL.md) |
| Add behavior | [Feature](playbooks/feature.md) |
| Change structure | [Refactoring](playbooks/refactoring.md) |
| Resolve an empirical design question | [Prototype](playbooks/prototype.md) |
| Explain/check lifecycle rules or verification drift | [Statecharts](../architect/references/statecharts.md), then [property verification](../tdd/references/formal-verification.md) |
| Match a reference UI | [Visual parity](playbooks/visual-parity.md) |
| Author reusable instructions | [Skill authoring](playbooks/authoring-a-skill.md) |
| Compare prompt/skill behavior | [Evaluation](playbooks/eval.md) |
| Autonomous task, PR queue, no-merge handoff, dependent stack or standing program | [Autonomous run](playbooks/autonomous-run.md) |
| Research, answers, writing, other non-code work | [General task](playbooks/general-task.md) |
| Resume existing work | [Session pickup](playbooks/session-pickup.md) |
| User requests a pause | [Pause safely](playbooks/pause-safely.md) |
| Large migration or staged delivery | [Multi-phase plan](playbooks/multi-phase-plan.md) |
| User requests PR delivery | [Opening a PR](playbooks/opening-a-pr.md) |
| Investigate or contribute upstream | [Contribution intake](playbooks/contribution-intake.md) |
| Address PR feedback or check CI | [Bounded PR iteration](playbooks/pr-iteration.md) |
| Diagnose bulk CI or verify release evidence | [Pipeline failures](playbooks/pipeline-failures.md) |
| Plan a rollout or incident recovery | [Health and recovery](../orbyn-ci-design/references/rollout-recovery.md) |

## Hand off to the owner

Use the [skill system](references/project-policy.md#routing) to select the relevant
handoff. Read the [operating method](references/operating-method.md) for the local
handoff map from each need to its maintained owner and result, with notes on the
handoffs below.

- Setup: [orbyn-setup](../orbyn-setup/SKILL.md), selected automatically.
- Checkout isolation or a requested worktree: [orbyn-worktree](../orbyn-worktree/SKILL.md).
- Memory (on by default; `ORBYN_MEMORY=off` opts out): search the target's project and
  personal scope at task start and treat results as hints; save on "remember"; after
  substantial work suggest at most three lessons and save only approved ones. Details:
  [reflect's local memory flow](../reflect/references/memory.md).
- Durable handoff: the optional [task record](references/task-record.md).
- Explicit plans or a complex change: [orbyn-plan](../orbyn-plan/SKILL.md).
  Unresolved external facts: [orbyn-research](../orbyn-research/SKILL.md).
  Skill-system changes: [orbyn-skill-creator](../orbyn-skill-creator/SKILL.md).
- Changing unfamiliar behavior: [how](../how/SKILL.md). Consequential data/ownership
  decisions: [architect](../architect/SKILL.md). Historical constraints:
  [why](../why/SKILL.md). A larger task needing its own plan:
  [figure-it-out](../figure-it-out/SKILL.md).
- Work crossing domain, transport, persistence and clients: the
  [Orbyn Engineering contract](references/fullstack-contract.md). Backend effect
  design: [orbyn-backend-design](../orbyn-backend-design/SKILL.md). Stored-format
  transitions: [orbyn-data-migration](../orbyn-data-migration/SKILL.md). Trusted
  automation: [orbyn-ci-design](../orbyn-ci-design/SKILL.md).
- Affected code: [language guidance](../language-best-practices/SKILL.md). Requested
  technology recommendation: [stack selection](../orbyn-stack-selection/SKILL.md).
- External code/skill freshness, downloaded research or selective upstream updates:
  [orbyn-upstream-review](../orbyn-upstream-review/SKILL.md).
- Threat modelling, design-stage security review or an explicitly requested
  portable/offline source audit: [orbyn-security-audit](../orbyn-security-audit/SKILL.md).
- Demonstrated Expo/React Native work or EAS delivery:
  [mobile routing index](references/mobile-engineering.md).
- Onboarding, ordinary review, mentoring or level questions:
  [engineering scope](references/engineering-scope.md).
- Prototypes, evidence or local servers:
  [artifact lifecycle](references/artifact-lifecycle.md).
- A decision needing a concrete example or check: [method index](references/principles.md).
- A meaningful general skill gap: [contribution feedback](../orbyn-skill-creator/references/contribution-feedback.md).

## Lead substantial work

The owning lead grounds and scopes the outcome, chooses the design and delegates
substantial investigation and implementation as applicable. The lead stays
responsible for integration, review and verification. A small clear edit or narrow
explanation can proceed directly. Read the
[lead contract](references/lead-contract.md) before dispatching or reviewing a child, and before a commit or push.

- A child forbidden further delegation completes its assigned task directly and
  returns the artifact to its owner.
- Delegate within the resolved limits: no more than `max_children` children
  active, plus one reviewer child in the `reviewer_children` slot, none deeper
  than `max_depth`. Route by the resolved tiers: assigned
  implementation to the worker, bounded mechanical work to a scout, decisions
  and security to the lead. Escalate a failed or ambiguous worker one tier and
  record why.
- Use the resolved tier's model and effort. A host without it runs children on the
  session's model, named as such; announce every child to the user in one line.
  See [delegate on any host](references/lead-contract.md#delegate-on-any-host).
- Sessions only in `parallel` mode or on request; [delegate on any host](references/lead-contract.md#delegate-on-any-host).
- Never poll a background job or child (`sleep`, `ps`, `pgrep`, `top`); [wait without polling](references/waiting.md).
- For substantial work, write the [answer key](references/answer-key.md) first; the worker gets the outcome only.
- Inspect the actual returned artifacts and diff; treat a delegate's summary as
  evidence to inspect. The lead writes the final assessment.

## Verify and deliver

Complete the agreed outcome, including necessary caller migration and removal,
without silently expanding authority. Verify in proportion to the changed contract
and inspect the results. An implementation request includes appropriate local
checks unless explicitly excluded; respect consumer limits and separate external
effects. For authorized delivery, verify the successful owned commit and its
validated tree before pushing. A failed stage or commit stops dependent push, PR
and CI actions. Match each completion claim to direct evidence
for the requested artifact, and report unavailable or excluded evidence as a limit.

Deliver only the requested scope. Follow [unslop](../unslop/SKILL.md) and report
changed behavior/artifacts, actual evidence, unresolved limits and
local/committed/pushed/merged/deployed state. Start a PR, merge, publish, deployment,
external message or monitor only under explicit authority; delegation and playbooks
grant none.
