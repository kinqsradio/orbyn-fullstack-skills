# Behavioral prototypes and maintained verification

26 October 2026. Implementation starts from library `6a872049f92e46bc1c0f8f55143500429739d507`.
This change keeps 34 shared skill owners. It connects a human preview, an explicit
behavior contract and proportional verification, while correcting retired target
skill ownership instructions. It does not install shared skills into targets.

## Owner contract

| Existing owner | Added responsibility |
| --- | --- |
| `orbyn-ui-design` | Stateful preview scenarios, rule/state IDs, deterministic faults/reset, readable review package and separate evidence states |
| `architect` | States/events/guards, independent owners, source-linked atomicity, readable statecharts and explicit projections |
| `tdd` | Property-driven tool choice, real failing controls, counterexample replay and verification drift |
| `orbyn-skill-creator` | Optional durable project verification instructions following target-owned paths and discovery |
| `orbyn-workflow` | Routing, proportional rigor, human handoff, retained package and lifecycle |
| Backend and migration owners | Retry/idempotency and durable-fencing examples at actual effect boundaries |

Visual exploration, interactive behavior and critical-property verification are
levels chosen by the decision and risk. Small visual work needs no checker or new
project skill. Backend models do not need a product UI to be useful. Statecharts
can explain a design without pretending to be checked implementations.

## Evidence contract

Keep rendering, exercised interaction, model/configuration result and actual-code
correspondence separate. Stable IDs connect relevant rules to scenario controls,
implementation owners, model actions and checks. A chart projection discloses
omitted behavior. A rule violation becomes a code finding only after correspondence
and feasible replay/source evidence. A design with no implementation stays model-only.
Reachability is distinct from universal liveness, which needs stated scheduling
assumptions and suitable temporal checking.

Durable verification records source revision or dirty-source digests, covered
functions and other writers, model/configuration identities, tools, commands,
bounds, assumptions and last confirmed correspondence. Drift review follows
renames and new writers, preserves intended properties and reports in sync,
updated, bug or blocked. A blocked check does not advance correspondence.

## Optional executable support

The Orbyn-authored [renderer](../../skills/architect/scripts/render-statechart.mjs)
imports an explicitly supplied trusted installed Pele entrypoint. It does not
install tools, fetch a CDN, translate arbitrary charts into formal semantics or
check properties. Output is a new SVG; previous evidence and symlink destinations
are preserved. Input/output size limits bound accidental oversized artifacts.
The manifest now permits `.mjs` assets so the adapter survives skills-only packaging.
Existing rendering tools remain valid alternatives; absent tools remain unverified.

Pstack's selected formal-model/falsification/maintenance methods are adapted into
local references with pinned source records, hashes, complete MIT notices and
`provenance.json` entries. No upstream execution scripts are imported. Pele remains
an optional external dependency, with its own package license/lock owner. See
[architect's adaptation record](../../skills/architect/references/verification-source.md).

## Ownership correction

Authoring guidance and the system guide previously prescribed `project-skills/`
plus both-host links, despite setup's newer preserve-in-place contract. They now
follow established target paths and discovery rules. There is no retired shared
registration/check helper to invoke. A separately authorized local authoring task
can create a needed project skill; setup never relocates foreign guidance.

## Qualification

The [development protocol](../evaluations/2026-10-26-behavior-prototypes-protocol.json)
pins six paired scenarios, source inventories, prompts, fixtures, criteria,
host/model settings and limitations. A separately frozen
[transfer case](../evaluations/2026-10-26-behavior-prototypes-holdout.json)
checks progress versus reachability on the same unchanged methods. These are
bounded experiments assessed by the lead, not independent or statistical proof.
Full visible captures and artifacts stay in ignored local output/fixtures.
The [result report](../evaluations/2026-10-26-behavior-prototypes.md) records actual outcomes, failed attempts, runtime checks and
what remains unverified. No commit, push, PR, merge or deployment is implied.
