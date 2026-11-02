# Threat-model artifacts

One run writes these files to its [run folder](../threat-model.md#run-folder), and nowhere else:

| File | Written by | Holds |
| --- | --- | --- |
| `SYSTEM_UNDER_REVIEW.md` | evidence step | Evidence and gaps, per the [evidence guide](evidence-guide.md) |
| `selection.md` | selection steps | Architecture and method choices and the omitted alternatives |
| `threat-model.json` | analysis | The model. The authoritative record |
| `report.md` | report step | A readable view derived from the JSON. Say first that it is a quick or a deep run, and what was not done |
| `challenge.md` | challenge step | What the fresh pass tried and found |
| `change-review.md` | change mode | Changed scenarios against a baseline |

Check the JSON before deriving prose:

```sh
python3 <skill>/scripts/check_threat_model.py <run>/threat-model.json --root <target>
```

The script reads only. It checks structure, id references, the evidence rules below, and with `--root` that every `path:start-end` names a real regular file inside the target and a line range that exists. It cannot tell whether a claim is true. It exits 1 on a broken rule and 2 on unreadable or wrongly shaped input, naming the fault either way.

## Shape

```json
{
  "schema": "orbyn-threat-model/1",
  "model_id": "share-links",
  "revision": "1",
  "parent_revision": null,
  "status": "partial",
  "depth": "quick",
  "target": {"name": "example-service", "revision": "0123abc", "working_tree": "clean"},
  "decision": "Before we ship expiring share links",
  "architectures": {"primary": "web", "secondary": []},
  "methods": [],
  "scope": {"in": ["share-link creation, read, revoke"], "out": ["billing"]},
  "evidence": [
    {"id": "E1", "kind": "implementation", "locator": "src/share/revoke.ts:40-58", "summary": "Revoke deletes the link row."},
    {"id": "E2", "kind": "implementation", "locator": "src/share/stream.ts:12-30", "summary": "The stream reads the link once at connect."}
  ],
  "assets": [{"id": "A1", "name": "Shared document content"}],
  "actors": [{"id": "P1", "name": "Former link recipient", "capability": "Holds a link and an open stream; no account."}],
  "boundaries": [{"id": "B1", "name": "Link holder to document stream", "guide": "Identity and resource authority", "owner": "web"}],
  "flows": [],
  "controls": [{"id": "C1", "name": "Link row lookup at connect", "evidence_refs": ["E2"], "status": "observed"}],
  "threats": [
    {
      "id": "T1",
      "title": "Revoked link keeps streaming",
      "basis": "observed_weakness",
      "objective": "A1",
      "actor": "P1",
      "boundary": "B1",
      "prerequisites": ["Recipient connected before revocation"],
      "evidence_refs": ["E1", "E2"],
      "existing_controls": ["C1"],
      "counterevidence": "No revocation check found after connect in the files read.",
      "decisive_observation": "Does any later frame re-check the link?",
      "confidence": "medium",
      "confidence_rationale": "Both files read; the transport layer was not.",
      "proposed_outcome": "Re-check the link on each frame or close the stream on revoke.",
      "verification_refs": ["V1"],
      "handoff": {"to": "audit", "ref": "tm:T1"}
    }
  ],
  "verification": [
    {"id": "V1", "threat_ref": "T1", "status": "not_run",
     "plan": "Open a stream with a synthetic link, revoke it, read further frames.",
     "pass": "No payload after the revoke commits; an authorized reader still streams.",
     "fail": "A payload frame arrives after the revoke.",
     "inconclusive": "The revoke commit time is not observable."}
  ],
  "gaps": [
    {"id": "G1", "text": "Transport middleware was not supplied.", "limits": "B1", "smallest_observation": "The stream route's middleware list."}
  ],
  "limitations": ["Quick run: no separate challenge pass."],
  "redactions": []
}
```

## Rules the checker enforces

- `status` is `complete` or `partial`; `depth` is `quick` or `deep`. Complete describes the stated scope only.
- `threats`, `evidence` and `verification` are always present as lists, and a complete model has at least one record in each. A partial model may leave them empty.
- Ids are unique across the file, written in ASCII digits with no leading zero (`T1`, never `T01`), and every reference resolves to the right kind of record.
- Evidence `kind` is one of `implementation`, `configuration`, `documentation`, `caller_claim`, `proposed_design`. `execution` is accepted only for output an authorized person actually ran; this mode never runs the target.
- Every actor states its `capability`: what it can already do or reach.
- Locators are `path:start-end` (or `path:line`), repository-relative, with `start` no greater than `end`, and never absolute or containing `..`, with or without `--root`. A `caller_claim` uses `session:<label>`. Under `--root`, an `execution` locator may instead name a file in the run folder, the folder holding the model. An optional `excerpt` must appear in the cited lines.
- A secret-looking file, such as `.env`, a private key or a credentials file, is never opened. Its line range goes unchecked, and an excerpt on it is refused whatever the excerpt says or whether the file exists, so the checker cannot be used to test a guess at a value.
- `basis` is `observed_weakness`, `design_hypothesis` or `protected`. Missing evidence is a record in `gaps`, never a threat.
  - `observed_weakness` cites at least one `implementation` or `configuration` evidence record, and its `handoff.to` is never `none`. Documentation, a caller claim or a design is not enough.
  - `protected` names a control that cites evidence, and stays in the file as a counterexample.
  - `gap_refs` on a threat link the gaps that limit it.
- Every boundary's `guide` is the exact name of a row in the [boundary guide](../threat-boundaries.md). A threat names its boundary by id, so it inherits that row.
- Every threat states actor, boundary, prerequisites, counterevidence and the observation that would decide it.
- A threat carries no `severity`, `rating`, `score`, `likelihood` or `cvss`, in any letter case, unless the model has a top-level non-empty `rubric` the person supplied. Severity belongs to a confirmed audit finding.
- Every threat that is not `protected` cites a verification. A threat's `verification_refs` and each verification's `threat_ref` must point at each other.
- Every verification is `not_run`, with `pass`, `fail` and `inconclusive` text that differs beyond letter case and spacing. Planned is not passed.
- `retired`, when present, is an object with a `reason` and at least one `evidence_refs` entry. See [revisions](#revisions).
- Redact before writing. List each redaction in `redactions` as kind, location and placeholder, never the value.

## Handoff

`handoff.to` is `audit` for an observed weakness or a design hypothesis worth independent verification, `remediation` only for a weakness the person already accepted as real, `decision` when the answer is a design choice, and `none` for protected records. `ref` is the id the next stage keeps and must equal `tm:` plus the threat's own id, such as `tm:T1`. The audit keeps it as the first segment of every finding fingerprint, and the converter below keeps it as the coverage unit's `attack_class`.

To seed the audit, run the converter on a checked model:

```sh
python3 <skill>/scripts/threats_to_ledger.py <run>/threat-model.json --root <target> --out <run>/coverage-ledger.json
```

It refuses an invalid model, refuses an existing output file, and claims no review. It refuses a path Git does not confirm is ignored, including when Git cannot answer and a `.git` sits anywhere above the path. An unignored path passes only when no `.git` exists above it.

It seeds only threats still open for investigation, as one `planned` unit each. The others are not seeded, and the converter prints each with its reason: `retired`, `protected`, `resolved` (a `partly_resolved` threat stays open), `decision` (`handoff.to` is `decision`) or `no handoff` (`handoff.to` is `none`). The ledger format has no field for these, so keep that line in the run's coverage notes. Read the [audit protocol](../protocol.md#2-track-actual-coverage) for what the auditor does next.

Before closing the audit, confirm that no id was lost:

```sh
python3 <skill>/scripts/check_threat_model.py <run>/threat-model.json --ledger <run>/coverage-ledger.json --findings <run>/findings.json
```

Every open threat must still have a unit, and every `tm:` unit must name a threat. A finished unit, `covered` or `candidate`, must have a finding whose `fingerprint` is its `tm:T<n>` or starts with `tm:T<n>/`, and a `candidate`'s `result_fingerprints` must all be such findings. A threat disproved on review is a `rejected` finding, so its id is kept there. A `covered` unit keeps `result_fingerprints` empty as the ledger validator requires; the checker looks in the findings.

## Revisions

A new revision of a model keeps the `model_id`, takes the next `revision`, names its parent and keeps every threat id. Check it against its parent:

```sh
python3 <skill>/scripts/check_threat_model.py <run>/threat-model.json --root <target> --baseline <previous>/threat-model.json
```

The checker refuses a different `model_id`, a `parent_revision` that is not the baseline's `revision`, and any baseline threat id missing from the new file. A threat that no longer applies is retired with evidence, not deleted: it stays in the file with `"retired": {"reason": "The export route was removed.", "evidence_refs": ["E41"]}`, and the converter does not seed it. Never reuse a retired id. To reopen one, remove `retired` from the same id. A change that fixes a threat adds `"resolution": {"status": "resolved", "evidence_refs": ["E40"], "note": "Revoke now closes the stream."}` to that threat, citing implementation evidence that the control now holds; the threat keeps its `basis` and its id. When the change closes only part of the scenario, use `"status": "partly_resolved"` and a `remaining` text naming what is still open.
