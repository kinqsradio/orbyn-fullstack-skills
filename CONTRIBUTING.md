# Contributing to Orbyn Fullstack Engineering Skills

Everyone can use the public library and propose improvements without access to
the private Orbyn product. Anh Dang (`@kinqsradio`) is the creator and maintainer;
outside contributions use the same review and validation path.

## Make a contribution

1. Fork this repository and clone your fork. Create a purpose-based branch such
   as `fix/preview-overflow` or `feat/api-contract-example`.
2. Change the owning skill or helper. Explain the user request, the decision it
   improves, expected input/output and adjacent tasks that should not select it.
   Improve an existing owner before adding another overlapping skill.
3. Preserve source attribution and licenses. A direct adaptation needs an exact
   upstream URL/revision, applicable notice and a `provenance.json` entry. Reviewed
   inspiration is labelled separately; do not imply original authors contributed
   directly to this repository. Do not invent source history or Git authorship.
4. Run the checks below. Include a realistic use case and actual results in the
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
