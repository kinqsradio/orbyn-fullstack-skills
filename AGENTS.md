# Orbyn Engineering library instructions

This is a public skill library. It contains no Orbyn application source or
private-repository history. The consuming project's instructions, user scope and
host permissions take precedence over these reference defaults. Resolve the
target checkout and [project context](docs/agents/stack.md) before applying examples.

## Nested contribution repositories

Use only the ignored nested `repo/` workspace for independent target clones and
sibling worktrees. Follow the [workspace contract](skills/orbyn-setup/references/repository-workspaces.md).
Open the outer library as the agent workspace and identify the target Git root
before editing. Read both the relevant shared methods and the target's own
instructions, contribution rules and skills. Preserve upstream guidance in place;
shared methods never replace target policy, user scope or host permissions.
Nesting alone does not prove effective host discovery; read required local files
explicitly and report what was actually observed.

## Agent-led initial setup

For a setup request, use [orbyn-setup](skills/orbyn-setup/SKILL.md). Complete the
workspace preparation and checks yourself; do not ask the human to choose an
installation layout or invoke individual helpers. No shared skills are installed,
copied, linked or synchronized into target repositories. Company skills and
existing docs/settings stay with their owner. Existing external checkouts require
coordinated, recoverable migration; do not move active paths or lose local output.
Never infer authority for model/provider changes, publication or production effects.

## Offer reusable improvements with consent

When current work demonstrates a meaningful shared-skill gap, follow the
[contribution feedback policy](skills/orbyn-skill-creator/references/contribution-feedback.md).
Prepare a concrete general proposal and ask once whether the user wants a public
PR, local draft or no contribution. Honor existing exact-scope authority; silence
does not authorize publication. Preserve the main task, company-only material and
local work. No telemetry, persistent memory or automatic self-publication is implied.

Keep one canonical skill folder in `skills/`, catalog relationships in
`skills/catalog.json`, and generated discovery links for both hosts. Read
[skill maintenance](skills/orbyn-skill-creator/SKILL.md) for changes. Do not
load every skill or install runtime providers merely because a skill mentions them.
Target-owned skills remain in their existing target paths, outside
the public catalog; follow the [ownership guide](skills/orbyn-setup/references/project-skills.md).
Use [local resources first](skills/orbyn-setup/references/offline.md); external
citations are attribution/update pointers, and current online facts remain
unverified when network access is unavailable.

For external code/skill freshness and downloaded research, follow
[upstream review](skills/orbyn-upstream-review/SKILL.md). Use ignored
`orbyn-references/` for raw downloads; never commit that directory or `openSrc/`.
Only reviewed adaptations and deliberately licensed offline support enter the
public library. Do not edit installed plugin caches or replace our skill owners
with an upstream collection.

Use evidence-led investigation and explicit ownership across the domain, API,
persistence, clients and operations. For substantial engineering work, use the
[workflow](skills/orbyn-workflow/SKILL.md) and bounded delegation when the required
host configuration is available. A child completes its assigned slice directly.
If a named model/processing mode cannot be preserved, report the limitation and
continue permitted direct work. No recursive agent chains or unrequested chats.

Preserve unrelated changes, user data and configuration. Make public contributions
from an explicit allowlist; never copy a consumer's history, environment files,
private instructions or reports. [Workspace ownership](docs/synchronization.md) defines
the boundary. Do not publish, merge, message others or deploy solely because a
skill describes that step. Existing user authorization still applies.

Choose checks for the changed contract and respect explicit exclusions. Library
CI and helper checks are normal contribution evidence; they do not qualify a
consumer application or live agent behavior. Never launch a Codex Security scan
without a specific user request. [Security](SECURITY.md) defines private reporting.

Before delivery, run the relevant library checks in [CONTRIBUTING.md](CONTRIBUTING.md),
inspect the actual diff, and report artifacts, evidence, limits and actual
local/committed/pushed/merged/published state. Do not claim independent review for
your own edits. New branches use purpose-based `feat/`, `fix/`, `docs/`, `chore/`
or `refactor/` names without agent/vendor/model branding.

For worktree isolation, naming and cleanup, follow
[orbyn-worktree](skills/orbyn-worktree/SKILL.md). Use the primary clone’s sibling
`<repo>-wt/<purpose>/` root by default; preserve existing owned work and output.

For implementation, route actual files/manifests through
[language guidance](skills/language-best-practices/SKILL.md), loading only the
applicable reference. For a requested technology choice, use
[stack selection](skills/orbyn-stack-selection/SKILL.md) before architecture and
implementation. Existing project decisions and a research-only boundary remain
in force; examples do not mandate Orbyn's TypeScript stack.
