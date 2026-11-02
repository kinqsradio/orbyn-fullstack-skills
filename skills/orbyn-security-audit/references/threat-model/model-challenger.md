# Challenge a model

A fresh pass, not the author, tries to disprove an existing threat model. Run it on `threat-model.json` before the report is final, or on an older model the person names. Write `challenge.md` and add the outcomes to the model as gaps, confidence changes and conflicts. Give no approval verdict.

## For each open threat

1. Check prerequisites, actor capability, reachability and the claimed control against the cited lines. Re-read the code; do not trust the summary.
2. Look for a protective counterexample or another explanation before strengthening the threat. A control counts only when you can name the bypass or failure that would defeat it and the evidence that rules it out. If nothing rules it out, the threat stays open.
3. Look for what the model omitted: other paths to the same objective, authorized-role misuse, order and retries, recovery and degraded modes, dependencies, interactions between architectures.
4. Record one outcome: confidence up or down with its reason; a new gap; or a conflict with two evidenced alternatives. Absence of evidence is a gap, not a conflict.
5. Name the observation or test that would settle competing claims. Do not invent its result.

## Rules

- Keep the depth honest. A quick model stays quick; say which parts the challenge did not reach.
- Do not merge two threats on a similar label. A different actor, prerequisite, element or boundary means they stay distinct; link them.
- Resolve a conflict only with an observation. Keep a threat open when no resolution evidence exists.
- Do not alter a control, risk or method merely to fit a narrative.
- With tools or shared credentials in scope, apply [tool and shared credential boundaries](tool-credential-boundaries.md). A check inside the runtime does not constrain an attacker who controls that runtime.
