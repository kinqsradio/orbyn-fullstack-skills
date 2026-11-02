## Problem and resulting behavior

Describe the concrete request or failure and what changes for a user of the skill.

## Agent disclosure

We expect skills and policies to be built with agents, and we need to know how. Name
exact models with their version. A PR with this section incomplete is not sent for review.

- Tools: <!-- Claude Code, Codex, Cursor and so on, with the version if you know it -->
- Models: <!-- exact IDs and what each did, such as claude-opus-5-5 (lead), claude-sonnet-5-5 (worker) -->
- Effort: <!-- low, medium, high -->
- Human role: <!-- what a person decided, reviewed or changed -->
- External sources: <!-- every external skill or project used: URL, exact commit, licence and copied or reviewed. Write "none" if there are none. Copy or adapt only what we may modify and redistribute with credit alone. -->

## Scope and routing

- Owning skill/helper:
- Expected trigger and input/output:
- Adjacent request that should not select it:
- Compatibility and nested workspace impact:

## Evidence

List commands and observed results. Distinguish static checks, helper behavior,
live agent routing and rendered output. Mark checks that were not performed.

- Evaluation case IDs changed (or why inapplicable):
- Static/helper checks:
- Recorded host trials: <!-- suite hash and host/model settings, or "not run" -->
- Baseline/candidate comparison and remaining limitations (if measured):

## Attribution and publication boundary

- [ ] I can contribute this material under MIT and preserved applicable notices.
- [ ] New/adapted material has an accurate provenance entry and source revision.
- [ ] I reviewed the diff for private content, credentials and consumer-only files.
- [ ] Any agent-prepared public submission is within the user's explicit scope; no private consent transcript is included as proof.
- [ ] Catalog, library discovery/index and asset inventory are current.
- [ ] Every changed skill has a new `authoring` entry in `provenance.json`.
- [ ] Target repositories and their instructions/skills stay independent under ignored repo/; this change adds no target installation or pin-sync step.

Related issue, if any:

Review is requested automatically once this description is complete and CI is green.
