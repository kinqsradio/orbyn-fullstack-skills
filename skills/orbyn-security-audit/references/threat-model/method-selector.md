# Choose a method

The default is the baseline in the [method reference](../threat-model.md#baseline-questions) plus the architecture file. Add a named method only when it answers a distinct question and you can supply what it needs. Selecting a method is not running it. Write the choice and the omitted alternatives in `selection.md`.

## Choose

1. State the decision, the architecture boundaries, the unresolved questions, the available evidence and the effort limit. If no limit was given, propose a bounded first pass and say so.
2. For each proposed method give: its question, why the baseline does not already answer it, required inputs, the source and version you will use, the output, and its limits. Choose none when none adds value.
3. Compare two or three plausible alternatives and say why each is omitted or deferred.
4. Never substitute a similarly named variant for the one asked for. Never reconstruct a specialist procedure from its name: if the source is unavailable, record the gap.

## Fit

| Question | Method family | Needs |
| --- | --- | --- |
| What can go wrong per component or per directional flow? | STRIDE per element, STRIDE per interaction | Elements, flows, boundaries, protections. Choose one variant, not both. |
| How could an adversary reach one goal, and by which routes? | Attack trees | A grounded goal and its prerequisites. |
| How could a legitimate workflow be abused? | Misuse and abuse cases | The normal workflow, assets, actor assumptions. |
| What personal-data harms arise? | LINDDUN | Data subjects, purposes, flows. A security pass does not complete it. |
| What can go wrong in an agent's layers and interactions? | CSA MAESTRO | Agent goals, tools, autonomy, data. Do not force an ordinary system into seven layers. |
| Which known technique or pattern names a grounded scenario? | ATT&CK, CAPEC, ATLAS | A scenario already grounded in evidence. These label a scenario; they are not evidence of one. |
| How severe is a technical weakness? | CVSS | Supported metrics and an official calculator. Severity is not business risk. |
| How do I score a risk? | A rubric the person supplies | Never invent one. |

Workshop-style methods (card decks, Elevation of Privilege, persona exercises) need real participants. Do not simulate a session, votes or consensus.

## Third-party method terms

Method names and frameworks belong to their owners. See [third-party method notes](method-notes.md) before citing one in a report.
