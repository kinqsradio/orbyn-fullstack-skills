# Contributing to Orbyn Fullstack Engineering Skills

Everyone can use the public library and propose improvements without access to
the Orbyn product repository. Anh Dang (`@kinqsradio`) is the creator and maintainer;
outside contributions use the same review and validation path.

Company-specific skills stay in their target repository's established paths;
follow the [ownership guide](skills/orbyn-setup/references/project-skills.md).
Contributing a reusable method does not authorize publishing company material.
Use the [nested workspace setup](docs/installation.md) for target contributions;
the library itself remains the outer engineering workspace.
Required instructions must work from disk under the
[offline contract](skills/orbyn-setup/references/offline.md).

## Agent-suggested contributions

An agent can identify a meaningful reusable gap from current authorized work and
offer a concrete general proposal under the
[feedback policy](skills/orbyn-skill-creator/references/contribution-feedback.md).
It asks once whether the user wants a public PR, a local draft first, or no
contribution. The main task continues either way. User permission already covering
that exact public submission carries through without another routine question.

Before public submission, review the proposed content/diff and destination. Keep
company procedures, private source/data, credentials, chat transcripts and local
history out; use synthetic public examples and preserve credits/licenses. Local
fix/draft permission and silence do not authorize a public fork, push, issue or PR.
No private consent transcript is required as public proof. Authors remain
responsible for the right to contribute under MIT; an agent cannot accept a CLA
or relicense someone else's work on the user's behalf.

This flow does not add telemetry, persistent memory, mandatory lesson logs or
automatic uploads. It uses the same checks and maintainer review as any other
contribution. Public submission does not itself authorize merge or consumer promotion.

## Shared contributor workspace

Use the outer library checkout for engineering policy and task routing. Target
contributions, including Orbyn, use independent `repo/<project>` clones and sibling
`repo/<project-slug>-wt/<purpose>` worktrees. Contributors use the same maintained
shared methods while respecting the target's own instructions, skills and checks.
No target installation or pin-sync step is part of onboarding. Library maintenance
happens in this root or its owned library worktree, outside target commits.
A host that cannot discover both roots must read the relevant files explicitly
and report the limitation; do not copy shared policy into the target to mask it.

## Make a contribution

1. Start locally or in permitted private contribution storage under the
   [worktree/privacy policy](skills/orbyn-worktree/SKILL.md). GitHub native forks
   of this public library are public. When deliberately proposing a public PR,
   use a verified public fork and promote only the reviewed library changes.
   Create a purpose-based branch such as `fix/preview-overflow` or
   `feat/api-contract-example`; never publish private company material or backups.
2. Change the owning skill or helper. Explain the user request, the decision it
   improves, expected input/output and adjacent tasks that should not select it.
   Improve an existing owner before adding another overlapping skill.
   Follow the [authoring standard](skills/orbyn-skill-creator/references/authoring-standard.md);
   `scripts/check-library.py` fails on its size, description and case-coverage limits.
3. Preserve source attribution and licenses. A direct adaptation needs an exact
   upstream URL/revision, applicable notice and a `provenance.json` entry. Reviewed
   inspiration is labelled separately; do not imply original authors contributed
   directly to this repository. Do not invent source history or Git authorship.
4. For routing or output-contract changes, add or adjust a case in the
   [evaluation suite](skills/orbyn-skill-creator/evals/cases.json). Include an
   adjacent non-trigger and a failure-sensitive rubric where appropriate. Keep
   public examples synthetic and preserve frozen holdout criteria for an actual
   comparison. Follow the [evaluation guide](skills/orbyn-skill-creator/references/evaluations.md).
   Run the checks below. Include a realistic use case and actual results in the
   PR template; clearly label any live routing/rendering checks not performed.
5. Say how it was built. We expect skills and policies to be made with agents, because
   they do this well, so every contribution names its tools, exact models and effort:
   in the PR's Agent disclosure section, and as a new `authoring` entry in
   `provenance.json` for each changed skill. If your agent opens the PR, it fills these
   in. CI fails a changed skill with no new entry.

   Credit everything. List every external skill or project you used, with its link,
   exact commit and licence. Copy or adapt only what we may modify and redistribute with
   credit as the only obligation, such as MIT, Apache-2.0, BSD, ISC, CC-BY or CC0. Record
   it in `provenance.json`, and keep its licence text and any NOTICE file. Copyleft licences
   such as GPL and AGPL, non-commercial terms, and code with no licence may only be
   reviewed for ideas, with no text copied. [CREDITS.md](CREDITS.md) is generated from those records.
6. Push your branch and open a PR to `kinqsradio/orbyn-fullstack-skills:main`. The
   [PR gate](.github/workflows/pr-gate.yml) labels it `needs-disclosure` until the
   description is complete. Once it is complete and CI is green, it is labelled
   `ready-for-review` and the maintainer is asked to review. Incomplete PRs are not
   sent for review. Maintainers review routing, authority, portability, evidence and
   licensing. A green check is necessary evidence, not automatic merge approval.

```sh
python3 scripts/sync-agent-skills.py --write
python3 scripts/library_manifest.py --write
python3 scripts/check-library.py
python3 -m unittest discover -s tests -v
git diff --check
```

The manifest update makes the proposed shared-file changes explicit; inspect it
with the diff. Do not edit hashes to conceal a mismatched source or missing file.
`skills/README.md` and both host discovery directories are generated. Every skill
needs a portable `LICENSE` and provenance entry. Keep substantial optional guidance
under linked references; do not pad every task with mandatory stages or panels.

## Working on a nested target

Keep target code, project instructions and local evidence in that independent
repository. Make reusable method improvements in a separate library branch/diff;
there is no copied-skill export or consumer pin promotion. Review actual content
for secrets and redistribution rights before public submission. See
[workspace ownership](docs/synchronization.md). Updating the library must preserve
other sessions' target work and active artifact paths.

## Scope and review

Good contributions improve a concrete engineering decision, behavior, useful
resource or evidence boundary. Avoid generic prompt collections, unverifiable
performance claims, keyword padding, mandatory vendor subscriptions and instructions
that expand user authority. General purpose and Orbyn-specific examples must be
distinguishable. Keep existing consumers compatible or document the migration.

For executable changes, include meaningful failure and recovery checks. For
documentation-only changes, validate links, metadata and realistic routing cases.
Do not add product builds, external messages or model calls merely to change a skill.

By submitting a contribution, you represent that you can license it under this
repository's MIT terms and include required third-party notices. No CLA or DCO
signature requirement is currently imposed. Security reports go through
[private reporting](SECURITY.md), not public issues.

## Evidence for skill evaluations

CI validates case structure and tests the evaluator with synthetic files. It does
not call models or prove quality gains. If you run a host trial, record the full
revision, suite hash, host/model/version/effort settings, trial count, captured
transcript, output artifacts and identified reviewer. Publish a concise result
summary and reproducible protocol; retain complete captures in ignored local
output or approved CI artifacts, with access pointers when available. Do not
imply local captures are downloadable public artifacts. Use the grader's report;
missing runs or rubric evidence remain unverified. A paired comparison requires
the same cases, host settings and pinned fixture/tool protocol, with one baseline
and one candidate. Preserve failed and timed-out attempts when reporting reruns.

Keep raw trial evidence outside tracked library content by default. A separate
reviewed publication can be appropriate, but is not required for each contribution.
Ship synthetic examples and reusable helpers rather than project session logs.
Do not commit real customer or private repository context. A
project's `.agents/orbyn-context.json` and design/brand guides belong to that
consumer, not the managed public skill export.

Skill maintenance also checks recursive discovery and Markdown heading fragments.
Use `SOURCE.md` for bundled upstream entrypoint text, preserving its original path
and byte hash in snapshot metadata. A catalog entry must link to a real maintained
owner; imported text cannot introduce active aliases or missing workflow dependencies.
Update [the catalog audit](docs/skill-audit.md) when ownership or evidence limits change.
