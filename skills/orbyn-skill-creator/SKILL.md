---
name: orbyn-skill-creator
description: "Create, refine, merge or retire Orbyn repository skills while keeping task routing, technology boundaries, host discovery and documentation consistent."
---

# Maintain Orbyn skills

Read the consuming project's instructions and relevant guides in place. Use the
[portable policy and routing defaults](../orbyn-workflow/references/project-policy.md)
only where guidance is missing. Inspect nearby skills before editing. Prefer
improving the existing owner over creating a second skill that attracts the same
requests.

Route from the user's natural-language request. Complete authorized ownership,
authoring, migration, registration and validation steps without asking the user
to invoke separate skills. Helper flags are an execution contract for the agent.

## Choose the owner before authoring

Classify the request using the [company/repository skill boundary](../orbyn-setup/references/project-skills.md).
Consumer conventions and local adaptations stay in that consuming checkout's
established paths under its own ownership and discovery rules, outside the shared
catalog, public manifest and upstream lock. A library improvement must be explicitly
in public contribution scope; never infer permission from generic wording or copy
company material into the shared skill tree. For local skills, follow the consumer's
authoring/discovery checks and the [consumer notes](references/library-maintenance.md#consumer-and-local-skills).
The steps below apply to library-owned skills.

## Define a useful contract

Write the trigger, expected input, result and boundaries. Identify the applicable
stack and role, the skills this one genuinely depends on, and its handoff. Use
`orbyn-research` for unknown host/specification behavior, and confirm a tool exists
here before relying on it. Make examples realistic to Orbyn's architecture.

Keep essential choices in `SKILL.md`; put conditional templates or deep guidance
in linked references. Keep model/session/permission policy with its owner rather
than repeating it in every skill. Name Orbyn-specific entrypoints `orbyn-*`. A
decision principle normally belongs in an existing owner's entrypoint and conditional
reference; a separate skill needs a distinct task trigger and useful result. Keep
third-party attribution in source/provenance records, never as an inherited active
agent identity. Keep essential instructions and required references usable from
disk under the [offline contract](../orbyn-setup/references/offline.md).

## Author and integrate

Follow the [authoring standard](references/authoring-standard.md) for the description,
entrypoint order, prose, helper code and required cases. Its checked limits fail
`python3 scripts/check-library.py`.

Use a matching folder/name with lowercase letters, digits and hyphens (under 64
characters), and concise `name`/`description` frontmatter. Keep the description on
one line for the repository catalog generator. Describe actual routing, not a
catchall. Include only resources needed to perform the task. Add no placeholder
folders, mandatory panels or new approval flow without a reason.

Register the skill in `skills/catalog.json` with its category and maintainer-facing
routing relationship. Update the owning task route in the workflow/system guide
when needed. Use `python3 scripts/sync-agent-skills.py --write` to refresh the
catalog index and host links; review its diff. Never overwrite unrelated host
settings or install global skills/MCP providers as part of repository authoring.

For a rename or retirement, migrate incoming links and discovery paths first.
Keep source-to-local attribution maps correct, and keep the provenance of every
import. Update affected documentation and remove obsolete competing guidance.

## Validate the whole path

Run `python3 scripts/check-agent-assets.py` and
`python3 scripts/sync-agent-skills.py --check`. Check a few realistic routing cases:
expected trigger, adjacent task that should not trigger, missing tools/evidence,
and the downstream handoff. Check references and role/stack boundaries. Report
metadata and routing inspection as static evidence, separate from live model behavior.

Use an available host skill validator for frontmatter when present. Execute new
helper scripts in disposable scope and inspect their outputs. A live skill trial,
external effect or product test still needs applicable authorization. Skip paid
model panels for documentation validation.

Update an [evaluation](references/evaluations.md) case when its contract changes,
and never change frozen criteria after observing a held-out result.
`python3 skills/orbyn-skill-creator/scripts/evaluate.py validate` checks the suite.
Report checks actually performed, remaining behavior gaps, changed files and
local/committed delivery state.

## Read when the task needs it

- Offering a demonstrated reusable gap back to the library:
  [contribution feedback](references/contribution-feedback.md).
- A selected remembered lesson: [memory-to-skill handoff](references/memory-learning.md).
- A durable project check of a critical behavioral property:
  [project verification](references/project-verification.md).
- Positive, adjacent, no-skill and outcome cases, or a claimed improvement:
  [evaluation guide](references/evaluations.md).
- An explicitly requested reproduce/fix/PR-feedback execution trial:
  [disposable contribution lab](references/contribution-execution.md).
- Explicitly requested multi-suite CI or release/capacity exercises:
  [disposable pipeline method](references/pipeline-execution.md).
- External skill freshness and source comparisons:
  [upstream review](../orbyn-upstream-review/SKILL.md).
- A full sweep, `SOURCE.md` text, a rewritten derived skill, consolidation or the
  public contract: [library maintenance](references/library-maintenance.md).
- A shared edit before release: [release handoff](../orbyn-upstream-review/references/release-handoff.md).
