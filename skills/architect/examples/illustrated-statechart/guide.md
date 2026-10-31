# A different domain: airlock departure

This original spaceport design sketch demonstrates nested parent/parallel/region
groups, a guarded transition, a branch and a retry/back edge. It is an unchecked
proposal, not a safety-qualified control system. Its explicit geometry and
semantic records live in [spaceport.json](spaceport.json).

From the library root, with an existing parent and a new output path:

```sh
python3 skills/architect/scripts/illustrate-statechart.py \
  --input skills/architect/examples/illustrated-statechart/spaceport.json \
  --out output/my-spaceport-art
```

Open `index.html` in that output. Compare art, same-geometry overlay and exact
record table. Source JSON stays editable; the render receipt binds input, helper
and output hashes. To illustrate a different domain, author its own nodes, group
containment, routes, guards, labels, palette and optional safe drawing primitives.
The executable schema is documented in the helper's `--help`.

The [art contract](../../references/illustrated-statecharts.md) applies beyond
these examples. Use technical-illustration to author a different composition or
richer art when its geometry needs more than this lightweight helper. Preserve
the actual behavior rather than fitting it into this sample. For a real checked
counterexample, use the separate [leased-job demo](../leased-job/guide.md).

## Our engineering workflow

[workflow.json](workflow.json) illustrates the existing Orbyn task-to-closeout
policy for a change-delivery path. Read-only/explanation tasks do not require
building, committing or publishing; routine changes use proportional investigation
and isolation only when needed. It separates source verification, commit readback, pushed-ref observation,
PR review/CI, actual landing and resource disposition. Selected loops cover failed
checks and scoped review feedback; branches preserve a local-only handoff and a
closed-unmerged result. An abbreviated guard in the picture retains its complete
condition in the edge's `details.fullGuard` record.

```sh
python3 skills/architect/scripts/illustrate-statechart.py \
  --input skills/architect/examples/illustrated-statechart/workflow.json \
  --out output/my-workflow-art
```

This is an explanatory overview, not an executed model check or task-status
tracker. Retained/retired are closeout dispositions; they do not assert successful
delivery. Source, commit, push, PR and resources can coexist in different states.
The drawing adds no publication, merge or cleanup authority, and it does not
require a human approval checkpoint for routine already-authorized work.

Owning methods: [workflow](../../../orbyn-workflow/SKILL.md),
[PR delivery](../../../orbyn-workflow/playbooks/opening-a-pr.md),
[PR iteration](../../../orbyn-workflow/playbooks/pr-iteration.md), and
[task closeout](../../../orbyn-worktree/references/task-closeout.md).
