# Connect task playbooks to operational evidence

Choose a playbook from the user's outcome and current source. Keep the requested end state visible: explanation, design, local implementation, PR, merge and deployment are different deliverables. A skill handoff is internal work selection, not homework for the human.

Use this local handoff map when an upstream workflow name is absent:

| Need                                          | Maintained owner and result                                                             |
| --------------------------------------------- | --------------------------------------------------------------------------------------- |
| Reproduction and defect diagnosis             | `how` plus the bug-fix playbook: source trace, supported cause, corrected invariant     |
| Architecture alternatives                     | `architect`, with `arena` only for a consequential unresolved comparison                |
| Performance or captured-profile investigation | Performance/trace playbook: workload, limiting phase, comparable observations           |
| Caller-preserving refactor                    | Refactoring playbook: caller inventory, target boundary, compatibility evidence         |
| Prototype or evaluation                       | Relevant playbook: frozen question, decision criteria, observations and limits          |
| Paused or resumed work                        | Pause/session-pickup playbook: exact candidate, owned output, unresolved actions        |
| PR creation or CI choice                      | Opening-a-PR playbook and CI owner: allowlisted patch, destination, proportional checks |
| Upstream contribution                         | [Intake](../playbooks/contribution-intake.md): target policy, issue overlap, feasibility and requested end state |
| PR feedback and current-head gates            | [Bounded iteration](../playbooks/pr-iteration.md): supported corrections, exact candidate, check/review gates and retry limit |

Do not call a missing upstream skill or silently install a collection to satisfy its name. Follow a local maintained owner; if a requested capability has no owner, state the gap and propose its scope. Imported source text is historical reference, not executable routing.

Before closing the task, reconcile source, artifacts and terminal check results with the requested outcome. Review the normal path and the relevant failure/recovery path. Keep unavailable runtime or independent review evidence visible. A successful helper or agreeing delegate does not establish the user's complete result.

## Owner handoff notes

Read the note for the handoff in use. The workflow lists when each one applies.
Orbyn owns this workflow and its defaults. Source attribution and preserved
dependencies are documented in
[attribution and resource boundaries](project-policy.md#documentation-and-attribution).

### Workspace, context and setup

Existing optional [context pointers](../../orbyn-setup/references/project-context.md)
are read-only hints; ordinary source discovery works without a map. Shared methods
stay in the outer library; no installation, company-skill migration or consumer pin
sync is supported. State only observed file/read, request-inclusion and execution
evidence; [action scope](../../orbyn-setup/references/action-scope.md) implies no
runtime gate or research harness.

Use the optional [task record](task-record.md) for a durable handoff without
duplicating an existing tracker. Setup selects [orbyn-setup](../../orbyn-setup/SKILL.md)
automatically and preserves active external paths until migration is authorized.
External citations identify origins.

### Worktrees

When checkout isolation is needed or a worktree is requested, select
[orbyn-worktree](../../orbyn-worktree/SKILL.md). Resolve the primary clone and prefer
its sibling `<repo>-wt/<purpose>/` root, reusing a suitable owned checkout first.
Preserve active legacy layouts and local output. Isolation needs no new chat and
does not imply separate databases/services.

### Local memory

Explicit durable remember/find/correct/tag/category/forget requests route to
[reflect's local memory flow](../../reflect/references/memory.md). Keep task records
separate, resolve the active target and retrieve only its authorized scope. Existing
memory opt-in never implies capture of every task, host-memory writes or remote
publication. Revalidate recalled evidence before acting. Selected reusable lessons
follow [candidate handoff](../../orbyn-skill-creator/references/memory-learning.md).

### Full-stack ownership

For work crossing domain, transport, persistence and clients, use the
[Orbyn Engineering contract](fullstack-contract.md). Resolve the consuming project's
actual owners before applying example stack conventions.

### Upstream review

For external code/skill freshness, downloaded research or selective upstream
updates, use [orbyn-upstream-review](../../orbyn-upstream-review/SKILL.md). Keep raw
references in ignored `orbyn-references/`; adapt the existing owner and preserve
source revisions and library releases separately. Available-source review does not
require binary reverse engineering or automatic installation of new upstream
workflows.

### Security audit

For an explicitly requested portable/offline source audit, use
[orbyn-security-audit](../../orbyn-security-audit/SKILL.md). Existing findings remain
with remediation, and a hosted security scan retains its own workflow.

### Language and technology decisions

For an affected code path, select [language guidance](../../language-best-practices/SKILL.md)
from the actual files/manifests and load only its relevant local reference.
TypeScript schemas use that owner's
[local TypeScript guide](../../language-best-practices/references/typescript.md). Use
[stack selection](../../orbyn-stack-selection/SKILL.md) for a requested recommendation
or demonstrated technology mismatch; it produces the decision for architect and
the implementation owners, not an automatic rewrite. The human requests the outcome
once; the agent chooses these handoffs internally.

### Scope and resources

Use [engineering scope](engineering-scope.md) for onboarding, ordinary review,
mentoring or junior/senior/staff responsibility questions. Scale ownership and
explanation to the task without lowering correctness or creating role-specific
skill catalogs. Cross-team strategy belongs to the planning owner.
For prototypes, evidence or local servers, use [artifact lifecycle](artifact-lifecycle.md)
to choose storage, retain the human handoff and clean only owned disposable resources.

### Mobile

For demonstrated Expo/React Native work or EAS delivery, use the conditional
[mobile routing index](mobile-engineering.md). Generic mobile stack choices keep
stack-selection; bare native and mobile web retain their own owners.
