# Orbyn Fullstack Engineering Skills

**54 connected agent skills for full-stack engineering with Codex, Claude Code and Cursor.**

Architecture, API design, data migrations, language-aware implementation, web and mobile UX,
debugging, review, CI and delivery—organized around a feature's complete path
from domain model to user-visible behavior.

[![Validate skills](https://github.com/kinqsradio/orbyn-fullstack-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/kinqsradio/orbyn-fullstack-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Created and maintained by [Anh Dang](https://github.com/kinqsradio) under the
**Orbyn Engineering** brand. The library turns engineering practice into connected,
project-aware workflows for agents. The application lives in a separate repository.

Anh is a University of Melbourne student and the creator of Orbyn. Follow the
engineering work, share an example or contribute an improvement:

- [LinkedIn — Anh Dang](https://www.linkedin.com/in/tran-duc-anh-dang-392b7a231/)
- [GitHub — @kinqsradio](https://github.com/kinqsradio)
- Personal contact: [anhdang.contact@gmail.com](mailto:anhdang.contact@gmail.com)
- Orbyn contact: [anhdang@orbyn.dev](mailto:anhdang@orbyn.dev)

This MIT-licensed fullstack library works in projects beyond Orbyn. Consuming
teams retain their own instructions, stack and company skills; no Orbyn account
is required. Orbyn's own engineering uses its canonical maintained skills, with
reviewed improvements flowing through this public library.

## The approach

**Ground the work → define its contract → change the connected layers → obtain
the right evidence → report actual delivery.**

A feature can involve a shared schema, API, transaction, background job and two
clients. The skills keep ownership and failure behavior visible across that path.
They distinguish a source finding from a runtime observation, a web preview from
native evidence, and a pushed commit from a deployment.

This is an opinionated engineering workflow, not a claim that prompts guarantee
correct software. [The engineering contract](skills/orbyn-workflow/references/fullstack-contract.md)
explains the handoffs. [The catalog](skills/README.md) lists every skill.

## Start with a task

| Your task                          | Start here                                 | Result                                                   |
| ---------------------------------- | ------------------------------------------ | -------------------------------------------------------- |
| Understand unfamiliar behavior     | `how` / `why`                              | Source trace or documented rationale                     |
| Deliver a cross-stack feature      | `orbyn-workflow`                           | Owned changes and proportional evidence                  |
| Decide the data/interface model    | `architect`                                | Caller-facing contract and lifecycle                     |
| Implement an API effect            | `orbyn-backend-design`                     | Validation, authority, transaction and client errors     |
| Change a stored format             | `orbyn-data-migration`                     | Compatibility, writer cutover and recovery               |
| Improve web/mobile task flows      | `orbyn-ui-design` + `orbyn-content-design` | Rendered UI with concise product language                |
| Implement across languages         | `language-best-practices`                  | Target-aware local guides and resource/error contracts   |
| Choose a technology stack          | `orbyn-stack-selection`                    | Constraint-led comparison, operating costs and exit path |
| Model TypeScript state             | `language-best-practices`                  | Shared schemas and explicit valid variants               |
| Review a risky patch               | `interrogate`                              | Concrete findings with scenarios and evidence            |
| Build contribution/release CI      | `orbyn-ci-design`                          | Scoped execution and reviewable promotion                |
| Draft a post or carousel           | `social-content` + `social-preview`        | Evidence-backed copy and local visuals                   |
| Review external code/skill updates | `orbyn-upstream-review`                    | Pinned comparison, ignored references and scoped updates |

Twenty focused principle skills refine difficult decisions; they are not twenty
mandatory stages. Five REA-related skills are optional specialists for artifact
investigation and REA maintenance. They do not install reverse-engineering tools.

## Clone, then ask your agent to set it up

```sh
git clone https://github.com/kinqsradio/orbyn-fullstack-skills.git
```

Open your existing project in Codex, Claude Code or another tool-using agent and
provide the local clone path. For example:

> Set up Orbyn Engineering skills from `/path/to/orbyn-fullstack-skills` in my
> existing project at `/path/to/my-project`. Read its instructions first. Inspect
> existing skills and docs, preserve company work and settings, choose the relevant
> skills, migrate clear company-owned skills into a local namespace with a backup,
> configure discovery and project pointers, and run the setup checks yourself.
> Keep company content outside public sync. Ask only for a consequential decision
> you cannot resolve from the project.

The agent reads the clone’s `AGENTS.md` and setup skill, chooses its helpers and
completes the authorized steps. You do not need to invoke individual skills,
select flags, create catalogs or move folders by hand. The default core includes
setup and skill ownership routing. The clone also works with a local model and
available filesystem/shell tools; no hosted subscription or API key is required
for static setup checks. Python 3.11+ and Git are tooling prerequisites.

Project installation supports Codex, Claude Code and Cursor discovery paths while
preserving existing target instructions and settings. Host-path checks establish
file layout; runtime compatibility is reported separately. No model, user-wide
configuration or provider is installed automatically.

For isolated work, agents use a sibling `<repo>-wt/<purpose>/` checkout under the
[worktree policy](skills/orbyn-worktree/SKILL.md), preserving active existing work.

Downloaded upstream code and research stay in ignored `orbyn-references/`.
Agents [review freshness and selectively adapt improvements](skills/orbyn-upstream-review/SKILL.md)
without committing raw research, replacing company skills or editing plugin caches.

The agent preserves existing docs, instructions, models, connectors and secrets.
It inventories conflicting skill copies before migration and keeps a recoverable
backup. It can complete clear owned changes autonomously; unresolved ownership
or missing permissions remain explicit. Keep the clone at a stable path or ask
for a reviewed pinned vendor copy for a portable team installation.

Then describe ordinary work:

```text
Trace this save action from the screen to its database effect.
Implement an authenticated task move API using our existing patterns.
Plan this stored-format transition; do not run it in production.
Write a LinkedIn introduction from these feature notes and preview the carousel.
```

The workflow selects relevant methods and local company skills. CLI options,
presets and explicit helper commands are available to the agent and CI in the
[installation guide](docs/installation.md); they are not extra required human
invocations. Host discovery can vary and may need a fresh session. Agents can
read the local `SKILL.md` directly when discovery is unavailable; installing
instructions does not prove a host loaded them or grant external-action authority.

## Bring your own stack

Orbyn uses TypeScript, React, Electron, React Native, API services and PostgreSQL;
those are examples, not prerequisites. The workflow resolves **your** schema,
transport, persistence, component and operational owners from current source.
Use the optional [project context map](skills/orbyn-setup/references/project-context.md)
to point to your existing stack, design, brand and verification guides. The map
belongs to your project and stays outside skill synchronization. See
[stack ownership](docs/agents/stack.md). Framework-specific examples do not
authorize adding that framework to your project.

The optional host model presets describe Orbyn's reference setup, not a required
model purchase. The installer does not apply them. Use the host/model guidance
only when requested and supported by your environment.

## Use it, adapt it, contribute back

You can use, modify and redistribute the MIT-licensed material with the required
notices. Company conventions belong in your consuming repository’s
[project-skills namespace](skills/orbyn-setup/references/project-skills.md),
separate from the shared library and public sync. The installer supports explicit
backed-up migration of selected existing host skills and preserves company docs.
The [offline contract](skills/orbyn-setup/references/offline.md) keeps instructions
and licensed source references available locally. To contribute, fork this repository, create a branch,
make a focused change, run validation and open a pull request here. New skills
need a concrete routing gap and a useful input/output contract.

[CONTRIBUTING.md](CONTRIBUTING.md) covers skill changes, provenance and checks.
[Synchronization](docs/synchronization.md) explains the upstream/consumer model:
shared content can be edited while working in a private consumer, exported through
an explicit skill-only allowlist, reviewed here, and pinned back into the consumer.
No private history, application source or project configuration is exported.

## Examples and evaluations

Start with the worked examples for [architecture](skills/architect/examples/proposal-approval.md),
[backend effects](skills/orbyn-backend-design/examples/retry-safe-effect.md),
[data migration](skills/orbyn-data-migration/examples/session-cutover.md),
[UI recovery](skills/orbyn-ui-design/examples/failed-save.md) and
[social writing](skills/social-content/examples/engineering-update.md). Each shows
synthetic inputs, a useful result and a concrete failure to avoid. An optional
[task record](skills/orbyn-workflow/references/task-record.md) connects decisions,
verification and continuation without a second project tracker.

Routine work relies on its diff, PR and CI. When a long task or handoff needs a
checkpoint, the agent maintains the minimum useful project-owned record without
another human invocation. The template includes helpers and synthetic examples;
actual task logs and raw traces stay outside public skill sync in the consumer's
approved local output or CI artifacts. Installation creates no logging directory.

The [evaluation toolkit](skills/orbyn-skill-creator/references/evaluations.md)
contains versioned routing and outcome cases with review rubrics. Prepare
frozen tasks, capture trials in an authorized host, grade evidence and compare a
complete baseline/candidate pair. Missing trials stay unverified. These are tools
for measurement. The [23 October Codex evaluation](docs/evaluations/2026-10-23-codex.md)
records 17/17 routing and 5/5 artifact passes against a previous-library baseline
of 16/17 and 5/5. It supports one routing correction, with explicit trial limits;
it does not establish general model improvement or Claude runtime behavior.

The [24 October setup and handoff trials](docs/evaluations/2026-10-24-setup-handoffs.md)
compare six focused cases against the released library. The final candidate
passed 1/1 routing and 5/5 outcome cases versus 1/1 and 4/5 at baseline. The
corrected recovery answer explicitly states crash/power-loss limits. Earlier
failures are retained in the report and full captures stay in ignored local output.
These are single-run development results with unblinded lead grading, not
independent qualification.

For substantive continuation, the optional [handoff contract](skills/orbyn-workflow/references/handoffs.md)
records scope, candidate, ownership, observed checks and next action. Its offline
checker rejects stale revisions and inconsistent completion claims; receiving
agents still inspect the actual evidence. Small tasks do not need a packet.

CI validates metadata, references, attribution, catalog/discovery consistency,
the distribution manifest and helper/synchronization behavior. It does not prove
live model routing, rendered design quality, native UX or production correctness.

## License

Original Orbyn material is MIT licensed. Applicable support-file licenses,
copyrights and provenance are preserved in [LICENSE](LICENSE),
[AUTHORS.md](AUTHORS.md), [provenance.json](provenance.json) and
[license notices](tools/THIRD_PARTY_NOTICES.md). Orbyn branding identifies this
project; it does not imply endorsement of forks or third-party services.

Report bugs with the issue forms. Report vulnerabilities privately using
[SECURITY.md](SECURITY.md); do not include credentials or private project content
in an issue or PR.

## Language-aware engineering and stack decisions

Use the library with JavaScript, Python, Go, Rust, Java, Kotlin, C#, Swift, C,
C++, SQL and shell projects, plus the existing TypeScript contract guidance.
The [language skill](skills/language-best-practices/SKILL.md) loads a focused local
guide for the affected code; [stack selection](skills/orbyn-stack-selection/SKILL.md)
compares project constraints, primary evidence, operating costs and migration paths.
The agent routes these from the task; no separate skill invocation is required.
Guidance and worked examples run from disk; current online support/pricing still
requires verification. Contribution work stays local/private until deliberate
publication under the [fork policy](skills/orbyn-worktree/SKILL.md).

## Contribution workspaces

For contribution work, the optional ignored `repo/<project>/` and
`repo/<project>-wt/<purpose>/` layout keeps target repositories together without
adding them to this library. Agents follow each target's own instructions and
skills, using our methods where compatible. See [nested workspaces](skills/orbyn-setup/references/repository-workspaces.md).
Public library changes and downstream product adoption remain separate decisions;
updating this library does not automatically repin a consuming project.

## Production best practices

The existing owners also cover maintainable modules, polyglot contracts, bounded
APIs and pagination, retry-safe effects, privacy-aware diagnostics, useful test
boundaries, async UI recovery and consumer-owned verification recipes. TypeScript
lives beside the other language guides under language-best-practices; its old
installer name upgrades to that owner without creating another active skill.
The agent selects the relevant methods from the task and preserves project policy.
