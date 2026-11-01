---
name: orbyn-security-remediation
description: Investigate and resolve existing security findings from Codex Security or a comparable record, capture evidence and add preventive checks without starting a security scan.
---

# Existing security findings

Never run, restart or rejoin any Codex Security scan unless the user explicitly requests that scan. Ordinary review, checkpoint qualification and local QA permission do not authorize scanning. Never launch a scan to close a remediation ticket.

## Method

1. **Read saved findings** and preserve original scan ID, revision, outcome and coverage. A canceled or failed scan is partial evidence, never a clean qualification.
2. **Consolidate duplicate causes,** retaining every original finding ID in the task ledger.
3. **Classify each finding** by tracing its reported path against current source: confirmed, already safe, duplicate, intentional with documented invariant, or unresolved. Do not equate a scanner label with a verified exploit.
4. **State the violated invariant** and trace attacker-controlled input to the actual authority or effect boundary. Check current callers, alternate paths and the legitimate behavior that must remain available.
5. **Correct that owner** with appropriate validation, authorization, atomicity, resource limits or compatibility. Preserve least privilege, and keep secrets and user content out of logs, fixtures and reports. Use [conditional finding patterns](references/finding-patterns.md) only when the finding involves those systems: keep concrete race/revocation/migration controls from the relevant pattern, without applying every historical product check.
6. **Test** the reported trigger, an alternate bypass and a legitimate control when authorized. Update preventive checks in the owning tests when testing is authorized, or in the authorized skill scope.
7. **Close out** in a Markdown task ledger: finding IDs, affected source, invariant, patch, focused checks and remaining limits. Mark fixed only with evidence; keep unavailable checks open.

## Ownership

The assigned engineer owns patches; use an independent reviewer when requested. Preserve unrelated work and candidate provenance. Follow [project instructions and scope](../orbyn-workflow/references/project-policy.md#scope-and-evidence) for testing and delivery scope.
