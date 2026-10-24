# Orbyn Engineering library instructions

This is a public skill library. It contains no Orbyn application source or
private-repository history. The consuming project's instructions, user scope and
host permissions take precedence over these reference defaults. Resolve the
target checkout and [project context](docs/agents/stack.md) before applying examples.

## Agent-led initial setup

When the human asks to set up this library in an existing project, read
[orbyn-setup](skills/orbyn-setup/SKILL.md) and complete the setup yourself. Resolve
the consuming root from the request/workspace; ask for a path only when it is
missing or ambiguous. Read that project's instructions before any writes.
Inventory skills/docs/config, classify ownership, choose a suitable preset, run
the helper dry-run, perform authorized backed-up migration/registration, create
or preserve valid context pointers and run the checks. Return the actual result,
backup location and limitations. Do not send the human a chain of skill names or
commands to execute. Preserve ambiguous foreign material and continue independent
work; never infer permission for model/provider changes or public export.

Keep one canonical skill folder in `skills/`, catalog relationships in
`skills/catalog.json`, and generated discovery links for both hosts. Read
[skill maintenance](skills/orbyn-skill-creator/SKILL.md) for changes. Do not
load every skill or install runtime providers merely because a skill mentions them.
Consumer-owned skills belong in that consumer’s `project-skills/` namespace, outside
the public catalog and sync; follow the [ownership guide](skills/orbyn-setup/references/project-skills.md).
Use [local resources first](skills/orbyn-setup/references/offline.md); external
citations are attribution/update pointers, and current online facts remain
unverified when network access is unavailable.

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
