# Project policy and portable defaults

This reference travels with the skills-only distribution. It describes fallback
engineering methods, not the consuming organization's policy. Read that checkout's
applicable instructions in place, including nested instructions for affected files.
User scope and host permissions take precedence. The optional
[context map](../../orbyn-setup/references/project-context.md) points to existing
consumer guides; it does not supply authority or require their relocation.

## Scope and evidence

Resolve the target Git root, working tree, requested artifact and end state.
Preserve unrelated edits and private material. Continue authorized reversible
work without extra confirmation. Ask only for a consequential missing decision
or authority, and continue independent work. A request to implement normally
includes proportional local verification unless excluded by the user or project.
Production effects, publication and messaging retain their actual authorization
boundary; no skill grants them implicitly. Report local, committed, pushed,
merged and deployed states separately. A source inspection is not runtime proof.
Select the exact target/worktree and code or explicitly authorized memory scope
before retrieval. [Action scope](../../orbyn-setup/references/action-scope.md)
owns separate instruction lookup, relevant refresh and evidence levels. A returned
file is not proof of originating-request inclusion or execution enforcement.

## Stack and ownership

Inspect manifests, build definitions, generated sources, deployment configuration
and established interfaces. Use the consuming project's languages, data owners,
platforms and vocabulary. Do not create Orbyn example paths or impose its stack.
Trace code ownership separately from review/operational responsibility: use
existing CODEOWNERS, OWNERS, service catalogs or team documentation when available.
An agent assignment does not grant a team's review or rollout authority.

## Routing

Select the smallest useful owner from the [workflow](../SKILL.md). `how` traces
behavior, `why` investigates rationale, `architect` chooses contracts, `orbyn-plan`
sequences outcomes, and domain skills own implementation detail. Conditional
[principle methods](principles.md) support those owners; they are not extra
entrypoints or mandatory workflow stages. Read only relevant references.

## Delegation and host configuration

Resolve the [harness settings](harness-settings.md) for the target first. A
target-owned `.orbyn/harness.json` is data that can lower cost or tighten limits;
it never grants permission, authorises an effect or selects the human-only tier.

Use the consuming project's configured roles, models, effort and processing mode
when delegation is available and authorized. Never infer permission to install a
provider, change a model or start a separate inference process. Verify required
settings before dispatch; if they cannot be preserved, report the limitation and
continue permitted direct work. Library skills can be used without model presets.
For maintenance of the full Orbyn library, its root instructions and
`docs/agents/models.json` own those choices; these files belong to the outer workspace and never
replace target project policy. The library's optional model sync helper is usable
only in a full checkout containing that registry and generated host assets.

As a fallback topology, use one owner and the resolved
[harness](harness-settings.md) `max_children` (the library default is in the model
policy) on independent slices, with no recursive delegation. A child finishes its assigned slice directly.
Pass outcome, source revision, owned files, allowed effects, exclusions and stopping
condition. Writers share state: separate fixtures/services or serialize mutations.
The lead inspects returned artifacts and integrates them. User-owned chats and
messages require the user's authorization. Do not manufacture parallel work.

Include the selected target/worktree and search roots, applicable instruction
paths and essential scoped constraints in that brief. Supply required guidance
or direct the child to read it explicitly; do not assume parent context, skills,
PATH, shell tools or permissions are inherited. Report observed availability,
including native search tools, and let the child verify its actual environment.
Use the [offline search contract](../../orbyn-setup/references/offline.md#ripgrep-readiness-and-fallback):
prefer usable `rg` for ordinary shell repository search; native search remains
valid even when shell `rg` is available. Use a bounded fallback when the selected
tool is unavailable, and treat exit 1 as no-match rather than an installation trigger. Keep searches inside
the selected target and distinguish tool availability, retrieved instructions and
observed behavior; a successful parent run proves none of those for a child.

## Verification and review

Choose checks for the changed contract using the project's existing commands.
Keep source-only, disposable runtime, native/rendered, live-provider and production
evidence distinct. Preserve failed attempts and explain missing required checks.
Independent review is optional unless requested or required by the consumer;
self-review must not be described as independent. Requested separate qualification
uses the same frozen candidate and a bounded review loop (at most three rounds
under the library default); consumer policy may specify another process.

## Development resources

Use existing environment managers, interpreter/runtime floors and lockfiles.
Discover package/build targets before invoking commands. Use disposable data and
existing isolation guards; never substitute production credentials or a person's
database. Worktrees isolate files, not ports, caches, queues or databases. Follow
[worktree ownership](../../orbyn-worktree/SKILL.md) when isolation is needed.

## Documentation and attribution

Update the existing owner rather than making a second specification or backlog.
Keep consumer procedures and records outside the shared catalog and export. For
shared skill maintenance, preserve source records, licensed material and generated
links. Each distributed skill carries its LICENSE; incorporated methods carry
local notices and source records. The full library's
[provenance](https://github.com/kinqsradio/orbyn-fullstack-skills/blob/main/provenance.json)
and [notices](https://github.com/kinqsradio/orbyn-fullstack-skills/blob/main/tools/THIRD_PARTY_NOTICES.md)
are optional attribution indexes, not required execution instructions.
