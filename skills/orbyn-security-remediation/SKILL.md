---
name: orbyn-security-remediation
description: "Resolve existing security findings from a threat model, audit or scanner record: classify, fix at the owning boundary, add a preventive check and hand back for verification, without starting a scan. Use orbyn-security-audit to find new ones."
---

# Existing security findings

Never start, restart or rejoin a hosted security scan, and never begin a new audit, unless the user explicitly requests it. Ordinary review, checkpoint qualification and local QA permission do not authorize one. Never launch a scan to close a remediation ticket. Run this work on the lead tier, never the scout tier.

## Where this sits

Security work runs threat model, audit, remediation, verification. This skill is stage three, and it hands back for stage four.

- **In:** a finding with a stable id: a `confirmed` audit finding, a saved scanner record, or a threat from a [threat model](../orbyn-security-audit/references/threat-model.md) that the person accepts as real. A bare `design_hypothesis` is not yet a defect: send it to [orbyn-security-audit](../orbyn-security-audit/SKILL.md) for independent verification, or to the person as a design decision.
- **Out:** a ledger and a patch, with each finding `patched` and a named check. Not `closed`.
- **Back:** a fresh verifier in the audit skill re-reads each patch against the invariant and the threat's own check, and returns `closed`, `still open` or `regression`. You do not grade your own fix. When the change is small, the owning test passes and the person says that is enough, record that choice and close it.

## Method

1. **Read saved findings** and keep the original id exactly. The ledger's id for a finding is its `fingerprint`; for one that came from a threat model it is `tm:T<n>` or `tm:T<n>/<slug>`, and a threat the person accepted directly is `tm:T<n>`. Copy that string unchanged into every ledger row, check name and handback, and never renumber or shorten it. Keep the scan or audit id, revision, outcome and coverage. A canceled or failed scan is partial evidence, never a clean qualification.
2. **Consolidate duplicate causes,** keeping every original id in the task ledger.
3. **Classify each finding** by tracing its reported path through current source: confirmed, already safe, duplicate, intentional with a documented invariant, or unresolved. A scanner label is not a verified exploit.
4. **State the violated invariant** and trace attacker-controlled input to the real authority or effect boundary. Check current callers, alternate paths and the legitimate behaviour that must stay.
5. **Fix the owner** with validation, authorization, atomicity, resource limits or compatibility as the invariant needs. Preserve least privilege. Keep secrets and user content out of logs, fixtures and reports. Read [conditional finding patterns](references/finding-patterns.md) only when the finding involves those systems.
6. **Test** the reported trigger, an alternate path to the same effect, and a legitimate control, when testing is authorized. Add the preventive check to the owning tests, or to the authorized skill scope.
7. **Hand back** in a Markdown ledger with one row per id above: affected source, invariant, patch, focused checks run with results, checks not run, and remaining limits. Keep unavailable checks open.

### Worked failure

Finding `tm:T1`: a revoked share link keeps streaming to a recipient who connected before revocation. The first patch rechecks the link when a stream opens. The reported trigger, a new connection after revocation, now fails, and the ledger says `patched`. The verifier runs the threat's own check: it opens a stream first, then revokes. Frames still arrive, because the already-open stream never rechecks. The result is `still open`.

The corrected patch rechecks the link on each frame and closes the stream on revoke. The ledger adds the alternate-path test (connected then revoked) beside the reported-trigger test and the authorized-reader control. The lesson is step 6: a trigger passing proves one path.

## Ownership

Patches are written by the `security_engineer` role at lead tier, and a fresh `security_verifier` at lead tier verifies them. Preserve unrelated work and candidate provenance. Findings from a private threat model or audit are sensitive: keep them in the run folder and the ledger, and do not paste them into public issues, commits or pull requests. Follow [project instructions and scope](../orbyn-workflow/references/project-policy.md#scope-and-evidence) for testing and delivery scope.
