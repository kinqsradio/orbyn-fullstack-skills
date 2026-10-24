# Contributing to Orbyn Fullstack Engineering Skills

Everyone can use the public library and propose improvements without access to
the Orbyn product repository. Anh Dang (`@kinqsradio`) is the creator and maintainer;
outside contributions use the same review and validation path.

Company-specific skills stay in the consuming repository under
`project-skills/<company-or-repo>/<namespaced-skill>/`; follow the
[ownership guide](skills/orbyn-setup/references/project-skills.md). Contributing
a reusable method does not authorize publishing company procedures or assets.
Required instructions must work from disk under the
[offline contract](skills/orbyn-setup/references/offline.md).

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
5. Push your branch and open a PR to `kinqsradio/orbyn-fullstack-skills:main`.
   Maintainers review routing, authority, portability, evidence and licensing.
   A green check is necessary evidence, not automatic merge approval.

```sh
python3 scripts/sync-agent-skills.py --write
python3 scripts/sync-public-skills.py manifest --write
python3 scripts/check-library.py
python3 -m unittest discover -s tests -v
git diff --check
```

The manifest update makes the proposed shared-file changes explicit; inspect it
with the diff. Do not edit hashes to conceal a mismatched source or missing file.
`skills/README.md` and both host discovery directories are generated. Every skill
needs a portable `LICENSE` and provenance entry. Keep substantial optional guidance
under linked references; do not pad every task with mandatory stages or panels.

## If you made the change in a consuming project

Follow [synchronization](docs/synchronization.md). Export is a local, explicit
allowlisted operation into a clean upstream contribution branch. Review the
result before pushing a public PR. The tool never copies the private repository's
Git history, root instructions, app source or environment files. A hash manifest
is not a secret detector: authors still review the actual content before public
publication.

After the public change merges, update the consumer to that exact revision and
its file hashes. Consumer CI catches un-reconciled changes; it does not grant a
public write token or automatically publish private material.

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
