# Orbyn Fullstack Engineering Skills

**34 connected agent skills for full-stack engineering with Codex, Claude Code and Cursor.**

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
| Contribute a fix or iterate a PR    | `orbyn-workflow` + `how`                    | Issue intake, reproducible evidence and bounded review/CI iteration |
| Draft a post or carousel           | `social-content` + `social-preview`        | Evidence-backed copy and local visuals                   |
| Review external code/skill updates | `orbyn-upstream-review`                    | Pinned comparison, ignored references and scoped updates |

Twenty engineering principles are now conditional methods under their execution
owners, with essential rules in those owners' entrypoints. They retain their
examples and licenses without adding discovery choices. The default core preset
is a 14-skill reading group; see the [consolidation record](docs/work/skill-consolidation.md). Five REA-related skills are optional specialists for artifact
investigation and REA maintenance, with local methods, recovery/evidence guidance
and [worked examples](skills/reverse-engineer-anything/references/worked-examples.md).
They do not install reverse-engineering tools or upgrade the pinned engine.

## Clone the engineering workspace, then ask your agent

```sh
git clone https://github.com/kinqsradio/orbyn-fullstack-skills.git
```

Open **orbyn-fullstack-skills** as the agent workspace in Codex, Claude Code,
Cursor or your local tool-using agent. Tell it:

> Set up the nested workspace for `<target repository URL>`. Read our engineering
> policy and the target's own instructions and skills. Preserve existing work,
> clone or safely reconcile the target under `repo/`, check the workspace, and
> complete the setup yourself. Do not install or migrate shared skills into it.

**Nested is the only supported layout.** Targets have independent Git histories:

```text
orbyn-fullstack-skills/
├── AGENTS.md
├── skills/
└── repo/
    ├── Orbyn/
    ├── orbyn-wt/
    │   └── save-retry/
    ├── another-project/
    └── another-project-wt/
        └── fix-pagination/
```

| Target repository | Its task worktree |
| --- | --- |
| `repo/Orbyn/` | `repo/orbyn-wt/save-retry/` |
| `repo/another-project/` | `repo/another-project-wt/fix-pagination/` |

Each target has its own sibling `<repo-slug>-wt/` container when worktrees are
needed. The task folder is created with Git and shares its primary repository's
history. Separate targets keep separate histories. Small work can use an already
suitable checkout; setup does not require an empty worktree or a new branch for
every task. Everything under `repo/` stays outside the library's Git index.

The agent uses [orbyn-setup](skills/orbyn-setup/SKILL.md), prepares the workspace,
reads the target's instructions in place and checks both Git roots. You do not
need to invoke each skill, choose installer flags, namespace company skills or
maintain consumer pins. There is no target installation or sync process. Existing
external checkouts require a coordinated migration that preserves active paths,
private configuration, ignored output and worktrees. Setup never moves them just
to satisfy the layout. See the [setup guide](docs/installation.md).

The outer workspace owns shared skills and host discovery. Target repositories
own their source, contribution policy, existing instructions and skills. A target's
Git boundary or host settings may limit automatic discovery: agents must read the
required local guidance explicitly and distinguish actual host observation from
filesystem checks. Nesting does not override target rules or host permissions.

**A target can own agent instructions now or add them later.** Orbyn may have its
own `AGENT.md`, `AGENTS.md`, `CLAUDE.md` or local skills for application-specific
commands, module owners and verification rules. Agents read that guidance alongside
the outer library's methods. Retiring Orbyn's duplicated installation does not
reserve or ban those filenames. Keep shared methods in this library and project
facts in the target; do not copy the shared policy back into it. Follow the
[instruction contract](skills/orbyn-setup/references/repository-workspaces.md#project-owned-instructions-now-and-later)
when the two sets differ. A future Orbyn instruction file is permitted; this change
does not create one automatically.

Python 3.11+ and Git support the local checks. A local model can use the same
files offline; setup does not install a provider, subscription or runtime. Optional
reading groups select relevant methods without copying files. For isolated work,
use sibling `repo/<project-slug>-wt/<purpose>/` under the
[worktree policy](skills/orbyn-worktree/SKILL.md).

Downloaded upstream research stays in ignored `orbyn-references/` or `openSrc/`.
Neither target repositories nor raw research enters the library's Git index or
public content. Agents [review freshness and selectively improve existing owners](skills/orbyn-upstream-review/SKILL.md).

Then describe ordinary work:

```text
In repo/widget, reproduce this failure using its own contribution rules.
Implement the fix in repo/widget-wt/save-retry and obtain the required evidence.
Write a LinkedIn introduction from these feature notes and preview the carousel.
```

## Bring your own stack

Orbyn uses TypeScript, React, Electron, React Native, API services and PostgreSQL;
those are examples, not prerequisites. The workflow resolves **your** schema,
transport, persistence, component and operational owners from current source.
Use the optional [project context map](skills/orbyn-setup/references/project-context.md)
to point to your existing stack, design, brand and verification guides. The map
belongs to your project and stays outside the public library. See
[stack ownership](docs/agents/stack.md). Framework-specific examples do not
authorize adding that framework to your project.

The optional host model presets describe Orbyn's reference setup, not a required
model purchase. Workspace setup does not apply them. Use the host/model guidance
only when requested and supported by your environment.

## Use it, adapt it, contribute back

You can use, modify and redistribute the MIT-licensed material with the required
notices. Company conventions and existing skills stay in their target repository's
[established paths](skills/orbyn-setup/references/project-skills.md), separate
from the shared library. Read and adapt both guidance sets without moving or
replacing upstream instructions. The [offline contract](skills/orbyn-setup/references/offline.md) keeps instructions
and licensed source references available locally. To contribute, fork this repository, create a branch,
make a focused change, run validation and open a pull request here. New skills
need a concrete routing gap and a useful input/output contract.

[CONTRIBUTING.md](CONTRIBUTING.md) covers skill changes, provenance and checks.
[Workspace ownership](docs/synchronization.md) explains the single-source model:
shared methods change in this library, while target code and project policy change
in their independent nested repository. A public library merge requires no target
pin update. Report the library revision used for evidence and coordinate updates
without discarding another session's local work.

When current work reveals a demonstrated reusable gap, the agent can prepare a
concrete proposal and ask once whether you want a **public PR**, **a local patch
to review first**, or **keep it local**. No special reflection invocation or
manual PR drafting is needed. The
[feedback policy](skills/orbyn-skill-creator/references/contribution-feedback.md)
keeps your main task moving, respects declines and existing specific permission,
and keeps company-only material local. Public improvements use synthetic examples
and preserve applicable credits. This is optional contribution, not telemetry
or automatic cross-user learning; silence does not upload anything, and a public
merge does not authorize changing your target repository.

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
actual task logs and raw traces stay outside public library content in the consumer's
approved local output or CI artifacts. Workspace setup creates no target logging directory.

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

The [25 October contribution assessments](docs/evaluations/2026-10-25-contribution.md)
record 12 passing outcomes and one underspecified, unverified case in each
condition. Expected-owner body reads were 9/13 at baseline and 13/13 with the
new workflow. A separate clarified-case pair passed 1/1 in both conditions.
These observations support connected routing, not an outcome-quality gain or
end-to-end contribution qualification.

The [disposable contribution execution study](docs/evaluations/2026-10-25-contribution-execution.md)
then exercised real reproduction, fixes, tests, commits, local pushes and paginated
PR feedback. Both conditions eventually produced correct outcomes in 2/2 trials;
the corrected candidate also stopped dependent pushes after a failed commit in
2/2, versus 0/2 at baseline. The local PR service is a controlled offline fixture,
and an earlier host-blocked worktree experiment is reported separately. These
small development trials do not qualify hosted GitHub behavior.

The [bulk CI and release exercise](docs/evaluations/2026-10-25-bulk-ci.md) adds
offline indexed failure analysis and artifact-bound stage verification. It ran
54,000 actual fixture testcases across 18 slots and separately measured up to
one million generated records, including 500,000 candidate failures. The complete
failure export is independent of the compact top-group summary. These local
capacity/evidence checks do not establish live-agent or production qualification.

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

Use only ignored `repo/<project>/` and sibling `repo/<project-slug>-wt/<purpose>/`
paths for targets. The agent completes setup without an installation-layout
question. Preserve existing external paths until a coordinated migration is
safe and authorized. Nested targets keep independent Git histories and their own
instructions/skills, outside library commits. Read both sets of guidance under
the [workspace contract](skills/orbyn-setup/references/repository-workspaces.md).
The library has one shared skill source; no target installation or repinning follows.

## Production best practices

The existing owners also cover maintainable modules, polyglot contracts, bounded
APIs and pagination, retry-safe effects, privacy-aware diagnostics, useful test
boundaries, async UI recovery and consumer-owned verification recipes. TypeScript
lives beside the other language guides under language-best-practices; its retired
reading-group alias resolves to that owner without creating another active skill.
The agent selects the relevant methods from the task and preserves project policy.
