# Orbyn Engineering library instructions

This is a public skill library. It contains no Orbyn application source or
private-repository history. The consuming project's instructions, user scope and
host permissions take precedence over these reference defaults. Resolve the
target checkout and [project context](docs/agents/stack.md) before applying examples.

Keep one canonical skill folder in `skills/`, catalog relationships in
`skills/catalog.json`, and generated discovery links for both hosts. Read
[skill maintenance](skills/orbyn-skill-creator/SKILL.md) for changes. Do not
load every skill or install runtime providers merely because a skill mentions them.

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
