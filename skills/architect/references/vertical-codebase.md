# Organize code around an owned capability

Use this reference when designing repository structure, reducing cross-feature
coupling or deciding whether code should stay local or become shared. Start with
the consuming project's actual stack, import graph and constraints. A request to
explain the current layout needs source findings, not a reorganization.

## Find the owner before choosing the folder

Inspect the relevant entry points, callers, tests and recent changes. Identify
the capability, its consumers and who owns its state and effects. Propose a
functional grouping when related code is repeatedly changed or understood
together. Routes can suggest a starting point; they are not proof that everything
used on a page belongs to that page. Justify the grouping with callers and change
history; folder names alone do not establish independence. Mark an inferred grouping
as a hypothesis when history or callers are unavailable.

Keep a capability's components, hooks, query helpers and local types close when
they share that owner. A local `components/` subfolder can still be useful; the
problem is unrelated capabilities sharing an unrestricted global bucket. A small
existing layout may need no new directory. Choose names that explain the work.

Preserve runtime, deployment and platform boundaries. A fullstack capability may
have corresponding API, web and mobile modules connected by a shared contract;
it does not require moving all implementations into one package. Shared domain
schemas stay with their canonical owner. UI organization never moves authority
checks out of the service or persistence boundary.

## Make coupling explicit

For each affected module, name its supported public entry points and consumers,
private details, and allowed dependency directions. A directory move improves
navigation but cannot prevent another feature from importing a private helper.
Avoid cycles and imports from domain contracts into client implementations.

Prefer an incremental change using the project's existing import rules or package
interfaces when they can enforce the contract, over a new workspace or a package
for every directory. Separate packages are appropriate when their ownership,
distribution or build isolation justifies the cost. Do not add a monorepo tool,
workspace or blanket barrel file solely to implement this guidance. Check actual
resolver and bundler behavior before claiming that an interface is enforced.
Import restrictions support maintainability; they are not an authorization or
security isolation boundary.

## Extract a capability, not a miscellaneous bucket

Keep a helper local while only its owner needs it. Before extraction, identify
actual consumers, common semantics, an owner and a stable interface. Two similarly
shaped helpers with different behavior may remain separate. A shared capability
can have its own public interface; a generic design system owns reusable visual
primitives, while business behavior remains with the relevant capability.

Explain the cost: local implementations may duplicate work, shared interfaces
require coordination, and package boundaries add build/configuration work. Choose
the smallest boundary that makes likely changes easier to reason about.

## Group packages by capability family

Applies when a repository already has, or needs, several packages: more than one
implementation of a capability, plugins, separate distribution or build
isolation. Without one of those, keep a single app with folders of the same
shape; split into packages only after a folder boundary proves too weak. The
"smallest boundary" rule above still decides.

A family has three roles:

- **Contract**: the seam or service definition, with types and no behavior.
- **Providers**: one or more implementations of the contract.
- **Consumers**: tools, UI or commands that call the contract.

Consumers and providers depend on the contract, never on each other. Business
rules sit in their own package and attach through a registry. The generic
runtime or gateway does not import them.

```text
packages/
  README.md              every group, one row each
  storage/
    README.md            what the group owns
    contract/            types and service definition
    local-disk/          provider
    cloud-bucket/        provider
  reports/
    README.md
    contract/
    pdf-export/          consumer of storage/contract
    rules/               business rules, registered by the app
  runtime/               generic host; knows contracts and the registry only
```

Group rules:

- Every package belongs to exactly one group.
- A new package joins an existing group. A new group adds its own README stating
  what it owns.
- The top packages README lists every group and its role in one table.

## Return a reviewable design

Provide an owner/path map, the public API and private details, allowed imports,
one relevant rejected alternative and its trade-off. If implementation is in
scope, plan one capability at a time: inventory callers, move related files,
update imports and remove the obsolete path after callers migrate. Account for
route discovery, lazy loading, aliases, assets, tests, mocks and external API
compatibility where affected. Avoid an indefinite second implementation or a
repository-wide folder rename without evidence that it solves the problem.

Select checks for the affected contract and authorization: inspect callers and
the import graph, use existing boundary/type/build checks where applicable, and
verify changed behavior when executable changes are authorized. Record which
checks ran. Static links, a proposed layout or a clean typecheck alone do not prove
runtime behavior, independent modules or better agent performance.

See the [synthetic task-editor example](../examples/vertical-task-editor.md).

When changing lazy/startup boundaries, use the workflow's [build budget and
measurement example](../../orbyn-workflow/playbooks/perf-issue.md#build-budgets-are-constraints-not-latency-results).
A folder move, chunk split or lazy-import declaration cannot establish reduced
startup work or latency; check actual dependency reachability and completed work.

## Reviewed inspiration and attribution

Dominik (TkDodo), [The Vertical Codebase](https://tkdodo.eu/blog/the-vertical-codebase),
published 13 April 2026; reviewed 24 October 2026. The article informed the focus
on functional cohesion and explicit public interfaces. This reference and example
are independently written for Orbyn Engineering. No article text, code or images
were imported; its website's copyright remains with the author. This citation is
reviewed inspiration, not an MIT license grant or a claim of author endorsement.
The architect skill's existing source attribution and license remain applicable.

Capability-family layout was shaped by DeepSeek's
[deepseek-harness](https://github.com/deepseek-ai/deepseek-harness/tree/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159)
(MIT, commit `fcc0ad4`; notice in [deepseek-harness-LICENSE.txt](deepseek-harness-LICENSE.txt)).
Reviewed inspiration; the wording and example are ours.
