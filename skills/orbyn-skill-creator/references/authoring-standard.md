# Skill authoring standard

Use this when creating or substantially revising a library skill. Each rule comes
from a defect found in this library. `python3 scripts/check-library.py` enforces
the ones marked **checked**.

## Earn the skill

Name the decision the skill changes. Write one request where an agent without it
would do the wrong thing, and what it does instead. If you cannot, add a sentence
to the existing owner or stop.

| Situation                                  | Put it in                                  |
| ------------------------------------------ | ------------------------------------------ |
| A rule for work an existing skill covers   | That skill's entrypoint or reference       |
| A distinct task with its own useful result | A new skill                                |
| One project's convention                   | That project's own skill, not this library |

## Write the description for routing

The description is the only text an agent sees when choosing a skill. Keep it as
one literal line of at most 300 characters (**checked**), in this shape:

1. What it does, starting with a verb.
2. The request that should select it.
3. The nearest neighbour and when to use that instead.

Weak: `Helps with migrations and related planning work.`

Strong: `Execute an authorized large migration through to its measurable end state,
tracking every unit. Use orbyn-plan when the deliverable is only a plan.`

Name the neighbour whenever two skills could attract the same request. Test the
pair with one case for each direction.

## Order the entrypoint by the task

Write `SKILL.md` for someone doing the work. Use this order:

1. A short opening: when to use it and what to read first.
2. `## Method`: the steps in order, with one worked failure case.
3. Decisions and boundaries the agent needs on every run.
4. `## Read when needed`: one "for X, read Y" line per reference.

Keep the entrypoint at or under 1,200 words (**checked**), and aim for 400 to 800.
When a section applies to only some runs, move it to a reference and leave a line
saying when to read it. When you add a topic, place it by task order. Appending it
to the end is how entrypoints grow out of order.

Keep the steps themselves in `SKILL.md`. A paragraph that sends the agent to
a short file for the real sequence wastes a read and risks being skipped. Keep
references one link from the entrypoint, each on one topic, and give them a name
that says what they hold. `operating-method.md` says nothing.

## Spend context on the agent's task

Everything in `SKILL.md` costs context on every run. Keep attribution, lineage and
change history in `provenance.json` and `tools/THIRD_PARTY_NOTICES.md`, because the
agent cannot act on them. Do not repeat a rule another skill owns; link to it.

## Write instructions

Follow [unslop](../../unslop/SKILL.md). Then check these:

- Say what to do. "Record the failed attempt" beats "a missing record does not
  establish absence".
- Show one concrete input and result for each important rule. An example is what
  an agent copies.
- Keep "never" for real safety limits, such as production effects, publication and
  deletion. A sentence full of "not" often hides the instruction.
- Replace abstract nouns such as "owner", "authority" and "evidence" with the actual
  file, person or check when you can.
- Keep project paths out of shared skills. Say "the project's theme file", and label
  a real path as an example.

## Add code that an agent can trust

- Use the standard library when it is enough. State what a script reads, writes and
  runs.
- Exit non-zero on failure, and name the cause in the message. Never report success
  after a skipped or failed step.
- Write output atomically, and never overwrite user data without a check.
- Keep paths inside the expected root. Pass arguments as a list, never through a
  shell string.
- Add a test that fails before each fix.
- For UI fixtures, follow [orbyn-ui-design](../../orbyn-ui-design/SKILL.md): keyboard
  access, visible focus, light and dark contrast, reduced motion and phone width.

## Prove routing

Every catalog skill needs at least two positive development cases and a holdout
that expects only that skill in [the case suite](../evals/cases.json) (**checked**).
Add one adjacent case naming the neighbour in `expected_skills` and this skill in
`forbidden_skills`. Write the
holdout from how a user would phrase the request, without reading your description
while you write it.

These cases check that the suite is coherent. They become behaviour evidence only
after a recorded trial under the [evaluation guide](evaluations.md). Say which of
the two you have when you report the change.

## Say how it was built

Add an `authoring` entry to the skill's record in `provenance.json` for every change:
`tool`, exact `model`, `effort`, `date` and `scope`. A PR also fills in its Agent
disclosure section. Never guess past work: older history stays `unrecorded`. Both are
**checked**, so a changed skill with no new entry fails CI.

## Credit every source

Reference every external skill or project you used, with its link, exact commit and
licence, in `provenance.json`. Copy or adapt only what we may modify and redistribute with
credit as the only obligation, such as MIT, Apache-2.0, BSD, ISC, CC-BY or CC0, and keep
its licence text and any NOTICE file. Copyleft, non-commercial and unlicensed sources may be
reviewed for ideas, with no text copied. **Checked:** a bundle under another licence
fails `check-library`.

## Before you finish

- [ ] The skill changes a decision you can name.
- [ ] The description names its trigger and nearest neighbour.
- [ ] The method is in `SKILL.md`, in task order, with a worked failure.
- [ ] Each reference has a "when to read" line.
- [ ] Attribution lives in provenance, and no project paths are hard-coded.
- [ ] Cases cover a positive, an adjacent request and a holdout.
- [ ] `python3 scripts/sync-agent-skills.py --write` ran and you reviewed its diff.
- [ ] `provenance.json` has a new `authoring` entry for this change.
- [ ] `python3 scripts/check-library.py` passes.
