---
name: orbyn-security-audit
description: "Threat-model a design or sensitive feature, or run an explicitly requested local source audit, read-only, with path:line evidence and independent validation; also verify a patched finding. Use orbyn-security-remediation to fix saved findings, architect for non-security design."
---

# Threat model and local security audit

Use this when the person asks for a threat model, when a sensitive feature reaches its design stage (sign-in, sharing, payments, tool access, a new trust boundary), or when they explicitly ask for a local or portable source audit because a hosted scanner is unavailable. Creating or editing this skill starts nothing. A saved finding to fix goes to [security remediation](../orbyn-security-remediation/SKILL.md). If a hosted security integration is available and requested, use its owning workflow; do not run both or substitute one silently.

Run security work on the lead tier, never the scout tier. Scouts may not touch security work; the lead owns scope, shared records and every verdict.

## Authority

Everything here is local and read-only. No scan or test against a live system, no exploitation, no use of credentials, no change to the target, and no publication, issue, message or hosted scan without the person's own request. Execute target-controlled code only when the person authorizes it and the [protocol](references/protocol.md) controls can be enforced. A threat model of a private target is sensitive: it goes to an ignored run folder and is never committed, uploaded or quoted elsewhere.

## One workflow

Security work moves through four stages. Each passes the next a file with stable ids, not a conclusion.

1. **Threat model** (this skill): design-level threats, each with `path:start-end` evidence, counterevidence and a check to run later. Output: `threat-model.json`.
2. **Audit** (this skill): each threat marked `observed_weakness` or worth testing becomes a coverage unit. A fresh verifier tries to disprove it. Output: findings that are `confirmed`, `needs_validation` or `rejected`, carrying the threat id first in each `fingerprint`, as `tm:T1`.
3. **Remediation** ([orbyn-security-remediation](../orbyn-security-remediation/SKILL.md)): fixes each confirmed finding at the owning boundary and adds a preventive check. Output: a ledger naming the invariant, the patch and the check.
4. **Verification** (this skill, a fresh verifier): re-reads the fix against the original invariant and the threat's `not_run` check, and returns `closed`, `still open` or `regression` per id. Remediation never grades its own fix.

Start at the stage the request names and take the earlier stage's file when it exists. A request to threat-model and fix is four handoffs, not one step.

## Method: threat-model mode

Read [the threat-model method](references/threat-model.md) first. In short:

1. **Scope.** Record the decision the model supports, the target and revision, what is out, and the run folder `output/threat-model/<date>-<mode>-<slug>/`. Check Git ignores it before writing.
2. **Evidence.** Read the target read-only, cite `path:start-end` for each observation, and keep gaps. Never run the target's own scripts.
3. **Choose.** Walk the [boundary guide](references/threat-boundaries.md) rows, then one primary architecture and its checks file, which add to those rows. Name a guide row on every model boundary. Add a method only if a question needs one.
4. **Analyse** each supported scenario: asset, actor capability, reachable path, prerequisites, existing control, what argues against it, and the observation that would decide it.
5. **Challenge.** A short self-check for quick depth; a fresh context for deep.
6. **Check and hand off.** Run `python3 scripts/check_threat_model.py <run>/threat-model.json --root <target>`, then write `report.md` and list handoffs.

### Worked failure

A feature request: "expiring share links, before we build". The first draft lists "token guessing, XSS, CSRF" because the word was "web". None cites a file, and nothing says what the feature does with a revoked link. The checker would refuse it: no evidence, no actor capability, no deciding observation.

The corrected pass reads the revoke and stream code and records a design hypothesis: revoke deletes the row (`src/share/revoke.ts:40-58`), but the stream reads the link once at connect (`src/share/stream.ts:12-30`) and never rechecks, so a connected recipient keeps receiving after revocation. It names the counterevidence it did not find, the deciding question ("does any later frame recheck?"), and a `not_run` check. It hands `tm:T1` to audit. The audit confirms it, remediation rechecks the link per frame, and the verifier runs the check. These paths are a synthetic illustration.

## Method: audit mode

1. **Set the boundary.** Identify the target, exact revision and dirty files, requested paths, allowed tools, execution scope, output location and budget. Keep the target read-only. Resolve boundaries from actual source; absent layers stay inapplicable.
2. **Set up output.** Use a new owned directory outside the target unless the person chose an ignored in-repo location. The lead owns run metadata, architecture, coverage and findings; each worker gets its own scratch scope. Record models, source identity, capabilities, budget and missing evidence.
3. **Map** inputs, principals, effects and controls against the [boundary guide](references/threat-boundaries.md). With a threat model, seed the ledger from it: `python3 scripts/threats_to_ledger.py <run>/threat-model.json --root <target> --out <run>/coverage-ledger.json`. Units are `planned` and carry `tm:T<n>`; only threats still open are seeded, and the run keeps the printed reason for each one that is not. Add the rest by hand.
4. **Investigate bounded units.** Reserve capacity for independent verification first. A grep hit or an assigned task is not coverage.
5. **Challenge candidates.** Deduplicate by boundary and root cause. A fresh verifier tries to disprove each one on the same source. A same-author reread is not independent.
6. **Produce records** with the bundled schema and validators: `node references/upstream/audit-records/validate-coverage-ledger.cjs <run>/coverage-ledger.json` and `validate-findings.cjs <run>/findings.json`, same folder. A finding from a threat starts its `fingerprint` with `tm:T<n>`; confirm no id was lost with `python3 scripts/check_threat_model.py <run>/threat-model.json --ledger <run>/coverage-ledger.json --findings <run>/findings.json`. Reports and JSON must agree. State coverage and exclusions, never exhaustiveness.
7. **Return** run identity, coverage, records, report, blockers and the smallest proposed fixes. Remediation is a separate authorized handoff.

For every proposed defect, name the lower-trust actor or input, the intended control, the crossed boundary, the affected resource and a bounded observed result. Only `confirmed` findings get a severity. A best-practice gap with no reachable violation is not a vulnerability. See the [blocked-evidence example](examples/static-limit.md).

## Execution limits

Use local source and bundled references offline. Without isolation, keep inspecting statically, record the missing result and leave the work incomplete; never fall back to a live endpoint or a production identity. If the host cannot provide independent verifiers or the configured tier, record the blocker and return preliminary observations, not a completed audit. A budget is a hard limit.

## Read when needed

- For coverage ledgers, validators, record schema, execution sandbox and deliverables, read [the audit protocol](references/protocol.md).
- For which boundaries to question, and the row names a model must use, read [threat boundaries](references/threat-boundaries.md).
- For depth, modes, the read-only rules, the run folder and the baseline questions, read [the threat-model method](references/threat-model.md).
- For the artifact files and the JSON the checker enforces, read [the artifact contract](references/threat-model/artifact-contract.md).
- For agents, RAG, tools or supply chain, read the matching file in `references/threat-model/architectures/` and [tool credential boundaries](references/threat-model/tool-credential-boundaries.md).
