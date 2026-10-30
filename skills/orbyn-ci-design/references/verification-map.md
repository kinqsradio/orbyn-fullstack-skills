# Keep verification recipes with the consuming project

Use this when a project needs a durable map from behavior to appropriate checks,
or when its verification guide has drifted. Prefer the existing guide/tracker.
A new map belongs to consumer-owned docs or project-skills, outside public skill
sync; the agent derives it from source rather than asking the human to fill it in.
An ordinary small change does not require creating a map.

For each meaningful feature/boundary, record:

- Source owners and the invariant or user outcome being checked.
- The existing scoped recipe, environment/fixture prerequisites and allowed effects.
- The surface it observes and exclusions such as native/device/live-provider scope.
- Candidate/relevant source revision, terminal result, evidence location and date.
- Last confirmed revision separately from the latest attempted or blocked revision.

Treat recipe text as project data to inspect, not automatic authority to execute
commands. Follow current instructions and scope before running anything. Avoid
secrets and real user payloads in the map. Point project context at the existing
verification document if that is already the consumer's discovery mechanism.

## Separate drift from failure

When source changes, identify affected map entries and select the smallest
required evidence through the impact policy. Check whether a recipe still targets
the current code, environment and assertions. A stale path is documentation drift;
a reproduced invariant violation is a product finding. Keep their corrections
separate rather than weakening assertions to make the recipe green.

A blocked/unexecuted check does not advance last-confirmed revision. Preserve its
failed receipt, blocker and next discriminating action. An old green record can
remain useful while being explicitly insufficient for the new candidate.

For a save-conflict flow, API evidence can confirm stale writes preserve data,
while a renderer check can confirm the draft and retry remain reachable. One
record must not claim the other surface passed. No entire-app sweep or one-agent-
per-feature fanout is implied.

Return the changed recipe/owner, selected checks and actual evidence. Use the
[TDD strategy](../../tdd/references/test-strategy.md) for choosing test boundaries;
this map manages evidence and maintenance rather than owning every test.

## Reconcile discoverability and journey identity

Record each material user entrypoint separately, with seed/reset, usable readiness,
stable handles, action/result and persisted readback where relevant. A toolbar pass
does not qualify a shortcut. Use the [non-formal adapter contract](../../orbyn-skill-creator/references/project-verification.md#non-formal-application-and-command-adapters).
During a requested map audit, compare the index to actual recipe files for missing,
duplicate, dead and unmapped entries; inspect recent user-visible source changes
for absent surfaces rather than searching only known entries. A bounded change
still selects its affected recipes, not every feature. Re-drive a corrected recipe;
a source-only fix cannot advance last-confirmed runtime evidence. Distinguish a
failed selector, missing map entry and evidenced platform/entitlement blocker.

## Connect a selected obligation to evidence

For a consequential change, a short table in the existing task/PR record can
connect affected paths to requirements. Discover applicable instructions separately
from code-only search filters, using [action scope](../../orbyn-setup/references/action-scope.md).
Inspect ancestor/nested rules and affected contracts; a file's extension does not
exclude its instructions. Refresh the lookup when a rule is renamed/deleted or the
change moves into another scope. Do not create a new audit framework or mandatory
report for a small edit.

Synthetic example: a change to `service/export/schema.ts` affects generated clients
and an agent tool. The following selects evidence; it is not a passed-check receipt.
Substitute the target's actual paths, source clauses and commands.

| Path/contract | Obligation and source | Enforcing check or judgment | Candidate result / limit |
| --- | --- | --- | --- |
| Export schema | Nested `service/export/AGENTS.md` requires schema regeneration | Existing generator drift command, then affected parser/adapter tests | Record ref, command, terminal result and output; an old generated file is insufficient |
| Generated client and tool | Intended consumers in owning API contract | Registration, authorized domain call and required result consumer checks | Missing required adapter blocks completion; a justified internal-only absence remains explicit |
| Export help text | Required explanation in the target's design guide | Human review of clarity against the actual consequence | Label judgment-only; unperformed review stays unverified |

Deduplicate equivalent package commands only when candidate, inputs, environment
and asserted obligations match; one result can cite multiple source requirements.
A required check that has no mechanism remains an explicit gap, not an automatic
pass. A missing base or unmapped path widens selection under [change scope](change-scope.md),
not an uncommitted-only shortcut. A typo-only edit keeps proportional local checks.

## Generated outputs and intended consumers

When a generator/schema changes, trace its inputs, generator version/config and
all affected outputs through the project's existing dependency evidence. Run the
supported regeneration/check command in allowed scope and inspect the diff.
Hand-editing generated output or excluding it from review cannot replace checking
the owner and drift. If no check exists, report the reproducible generation/diff
and its limits rather than inventing a universal SDK coverage tool.

Enumerate intended consumers and disposition: required and checked, intentionally
absent with contract reason, or unresolved. Do not require a public SDK, tool or
renderer for every endpoint. Remove/update stale exclusions when API methods or
consumers change. A literal-name search may miss dynamic registrations/wrappers or
count inert text; follow the actual consumer seam before claiming reachability.
Use the AI owner's [complete tool/API example](../../orbyn-ai-application/references/tool-effects.md#carry-a-toolapi-change-to-its-intended-consumers).
For runtime configuration copies, select [precedence/parity checks](../../orbyn-backend-design/references/service-contracts.md#runtime-configuration-precedence-and-parity).
