# Review a change against a model

Use when code or design changes after a model exists: a branch, a pull request, a new tool or a widened grant. The person must name the baseline model. A branch range alone is not a baseline; if none exists, ask or start a new model and say no baseline comparison ran. Write `change-review.md` and a new model revision.

## Steps

1. Bind the baseline: its `model_id` and `revision`, and the revision of the code it describes. Resolve the range to local commits with the read-only Git forms in the [method reference](../threat-model.md#read-only-rules). Record both endpoints and whether the comparison is endpoint-to-endpoint (`a..b`) or merge-base-to-head (`a...b`). Never mix the working tree with a different revision without saying so. If an object is not local, record the gap; do not fetch.
2. Start the new revision from the full baseline: same `model_id`, new `revision`, `parent_revision` set to the baseline's. A missing record in a proposed update is a gap to investigate, not a retirement. Run the checker with `--baseline`; it refuses a dropped threat id.
3. Trace each changed actor, asset, flow, boundary, dependency and lifecycle state to existing threats and controls. Look at new authority, disclosure, modification, accountability, availability, recovery and privilege-crossing effects. Add a threat only when real flows and evidence ground its prerequisites. Check a protective counterexample first.
4. Keep a threat's id while its scenario persists. Modify it when premises or confidence change; add a new id for a distinct scenario; retire only with evidence it no longer applies; reopen the same id when evidence returns. A proposed fix is not resolution: `resolved` needs an observation that the control now holds.
5. List every addition, modification, retirement and reopening once, with evidence.
6. For a changed tool, grant or credential, check whether existing consumers gained authority, and whether earlier approvals still apply. Apply [tool and shared credential boundaries](tool-credential-boundaries.md).
7. Propose treatments and `not_run` checks for new or materially changed open threats. Leave risks unrated unless a rubric was supplied.

Report separately: changed scenarios, carried findings, conflicts, proposed treatment, unrun checks, and the code not examined.
