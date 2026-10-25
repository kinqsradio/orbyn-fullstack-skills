# Selected memory to a reviewable skill improvement

Use after an explicitly selected local lesson demonstrates a reusable gap. The
[memory owner](../../reflect/references/memory.md) keeps records private and scoped;
the [contribution policy](contribution-feedback.md) governs publication. Do not
automatically learn from every task or convert private experiences into Git history.

The agent prepares a brief with exactly these fields: `title`, canonical `skill`,
full 40-character library `base_revision`, `problem`, `proposed_change`,
`synthetic_case`, `counterexample`, `validation_plan`, and `delivery`. Delivery is
`manual`, `local-branch` or `fork-branch`. The proposed change is independently
written; raw conversation text, identifiers and private evidence stay local.

Use the [memory helper](../../reflect/scripts/memory.py):

```text
propose --input brief.json --selection source-revisions.json --op UNIQUE_ID
candidate CANDIDATE_ID
prepare-patch CANDIDATE_ID --checkout OWNED_LIBRARY_CANDIDATE --files SELECTED_FILES --reviewed
```

Supply the same explicit private root and scope as the selected memories. Sources
must be active, unexpired and at their expected revisions. A correction invalidates
the draft and any prepared patch. Forgetting a source removes the dependent draft
and marks its managed patch for deletion. `candidate` reports current state; a
proposal is not evidence that the skill improved.

Prepare the actual change in one owned library branch/worktree using the existing
authoring workflow. `prepare-patch` reads that checkout without staging/committing.
Its HEAD must equal the frozen base. It emits a standard UTF-8 patch of selected
regular non-executable text files in the owning skill and explicit catalog/eval/
manifest/audit support paths. It includes new files but deliberately refuses
deletions, binary/mode/symlink changes and unrelated private paths. Larger changes
use the ordinary reviewed contribution workflow. No whole-tree export is allowed.
Patch paths use portable letters, digits, underscores, dots, slashes and hyphens;
whitespace/control characters are refused so a filename cannot inject diff headers.

`--reviewed` records the caller's acknowledgement of reviewing the exact content
within existing user scope. It is not automatic sanitization, licensing evidence,
evaluation or permission from the helper. Review the actual patch and hash. The
patch contains only selected library changes; the memory/candidate linkage stays
in local storage. Private code can still be present in an allowed path, so a path
allowlist does not replace content review.

Run library validation and the candidate's failure-sensitive/adjacent cases under
the [evaluation method](evaluations.md). Record actual source/base/diff/settings,
failures and limits in existing evidence artifacts. A helper receipt says
`prepared-not-evaluated`; it never awards a passing model score from a flag or
advances a draft to accepted. A new source/base/diff needs reconciliation and
fresh affected checks. Use the existing evaluator rather than a second learning
score or model runner.

## Delivery choices

- Manual/local: retain the base-bound patch and evidence. This works offline and
  without a GitHub account; no commit is necessary.
- Local branch: within explicit commit scope, apply/verify and commit the approved
  files on an owned `fix/learning-<topic>` or `docs/learning-<topic>` branch.
- Fork branch: within explicit remote scope, verify account, visibility, upstream,
  branch and reachable new commit history, then push the selected branch using
  the existing [worktree policy](../../orbyn-worktree/SKILL.md). Public GitHub forks
  of this library cannot store private memories. A separate branch is not privacy.
- Upstream PR: only when requested, use the ordinary contribution/PR workflow.
  A fork commit does not require an upstream PR and does not authorize a merge.

The helper itself performs no commits, pushes, fork creation or remote operations.
The existing agent workflow carries out those effects when authorized, preserving
one canonical candidate. Report prepared, checked, committed, pushed and accepted
separately. Reconcile drift with the [release handoff](../../orbyn-upstream-review/references/release-handoff.md).
Do not copy shared skills into targets or update a retired consumer pin system.
