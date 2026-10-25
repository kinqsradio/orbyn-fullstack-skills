# Orbyn Engineering library instructions

This is a public skill library. It contains no Orbyn application source or
private-repository history. The consuming project's instructions, user scope and
host permissions take precedence over these reference defaults. Resolve the
target checkout and [project context](docs/agents/stack.md) before applying examples.

## Nested contribution repositories

The optional ignored `repo/` workspace holds independent target clones and
sibling worktrees. Follow the [workspace contract](skills/orbyn-setup/references/repository-workspaces.md).
For new setup without a chosen destination/layout, ask once: nested
(recommended/default) or an existing project in place. Honor explicit paths and
delegated default choices; wait for an unresolved answer before dependent writes.
Preserve existing checkouts rather than moving them to enforce a default.
Resolve the target's own Git root and read its applicable instructions and skills
before editing. Library maintenance defaults do not replace target contribution
rules, stack, tests or agents. Higher-priority host/user instructions still apply;
do not assume a nested `.git` automatically stops ancestor instruction loading.

Preserve upstream-owned instructions and skills in their established locations.
Use portable methods where compatible; do not relocate their guidance merely to
fit our namespace. A target contribution does not itself authorize installing
skills or changing this library. Keep target source, history, credentials and
local setup additions outside the public library's index, catalog and exports.

## Agent-led initial setup

When the human asks to set up this library in an existing project, read
[orbyn-setup](skills/orbyn-setup/SKILL.md) and complete the setup yourself. Resolve
the consuming root from the chosen layout and request; ask for a path when it is
missing or ambiguous. Read that project's instructions before any writes.
Inventory skills/docs/config, classify ownership, choose a suitable preset, run
the helper dry-run, perform authorized backed-up migration/registration, create
or preserve valid context pointers and run the checks. Return the actual result,
backup location and limitations. Do not send the human a chain of skill names or
commands to execute. Preserve ambiguous foreign material and continue independent
work; never infer permission for model/provider changes or public export.

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
Consumer-owned skills belong in that consumer’s `project-skills/` namespace, outside
the public catalog and sync; follow the [ownership guide](skills/orbyn-setup/references/project-skills.md).
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
private instructions or reports. [Synchronization](docs/synchronization.md) defines
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
