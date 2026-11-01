---
name: orbyn-ci-design
description: "Design or repair CI, select affected checks, analyze bulk failures, verify release evidence and plan rollout or incident recovery. Keep artifact readiness and deployed health distinct; no implicit deployment authority."
---

# CI that checks the artifact it will promote

Read the consuming project's commands and contribution model before changing a
workflow. Use [orbyn-workflow](../orbyn-workflow/SKILL.md) for the broader change
and [security remediation](../orbyn-security-remediation/SKILL.md) only for
existing findings.

## Method

1. **Identify the run:** event, candidate revision, untrusted inputs, required evidence, credential scope and any external effect. Separate ordinary fork-PR validation from trusted maintainer publication or deployment. Inspect current primary platform documentation when a workflow depends on versioned action or token behavior.
2. **Use the smallest useful lanes.** Document changes need metadata/link checks; executable helpers need meaningful behavior checks; application changes need the affected contract's checks. Keep fixtures disposable and preserve source/runtime separation. Do not invoke a paid model or live provider merely to validate skill frontmatter. Report live skill selection and model behavior separately.
3. **Designate checks before expensive runs.** For small changes and selective execution, follow [proportional verification](references/change-scope.md): name the feature worktree's checks, exclusions and widening triggers, and use [stage-specific gates](references/change-scope.md#designate-gates-for-the-feature-worktree) rather than a whole-repository suite on every iteration.
4. **Lock down trust boundaries** using the rules below.
5. **Validate** workflow syntax and the actual helper behavior, then inspect the remote run for the exact candidate when available. Name branch-protection, secret or host settings that remain unapplied.
6. **Deliver** the workflow, commands and evidence.

For example, a skills consumer can verify its local file hashes against a public pin without a cross-repository write credential. A separate reviewed contribution exports only the managed skill paths; the private application's Git history and configuration never become part of that export.

## Scope and gates

Add CI automation or CD only when the change calls for it; a worktree or task alone is no reason. Cosmetic local work can finish with relevant local checks, without hosted CI/CD. Published changes keep their required merge status: use a known docs/skills fast path, broader checks for uncertain/runtime changes and a final gate that cannot hide classifier or selected job failures. Deployment is separate from green CI and must respect scope and existing authority. Decide the appropriate checks yourself, without adding a new skill or asking the human to invoke one.

## Trust boundaries

**Fork contributions:** use unprivileged PR execution, read-only tokens, no secrets and no persisted checkout credentials. Never execute a contributor's code in a privileged target-PR or follow-up job. Pin actions to reviewed immutable revisions and let dependency-update PRs propose changes. Treat issue text, branch names, artifacts and downloaded manifests as data rather than shell code.

**Cross-repository content:** prefer an allowlisted manifest and explicit upstream revision. Fail on drift, path escapes and overwriting local edits. CI may prepare a reviewable PR under a maintainer trigger; it must never silently make private content public or turn a successful check into permission to merge.

## Evidence claims

Artifact readiness, deployed health and recovery completion are separate evidence claims. Diagnose a failed pipeline before calling it a code defect. Unknown/failed required gates block readiness. Offline JSON/digests do not authenticate a provider or grant deployment authority. The agent completes authorized collection and analysis without making the human invoke each helper.

## Read when needed

- A requested verification inventory or stale recipes: the [consumer-owned verification map](references/verification-map.md). Derive it from current source and existing commands; keep attempted and last-confirmed revisions separate.
- Many failed suites, instances or shards: the [bulk method](references/bulk-failures.md) and its disk-backed offline analyzer. Collect the complete expected matrix and all attempts before diagnosing. Keep missing/invalid newest reports as blockers; never truncate the inventory to a readable top list or erase a fail/pass retry. Group shared symptoms as hypotheses, then use `how`/`tdd` for confirmed causes and meaningful corrections.
- Release evidence: [release verification](references/release-verification.md) binds required stage evidence to the actual candidate, artifact bytes, configuration, current run and freshness.
- Cross-package selection: [affected targets](references/affected-targets.md), with the existing build graph, generator/runtime edges and conservative fallback.
- An authorized rollout plan or incident recovery: [health-driven rollout](references/rollout-recovery.md).
- Changed AI behavior: [application evaluations](../orbyn-ai-application/references/evaluations.md) select affected task-quality evidence alongside deterministic contract gates. Do not turn every PR into a paid model sweep or treat static skill-case validation as application quality. Existing live-call, data and deployment authority applies.
- Demonstrated Expo/EAS or native-only EAS delivery: [build/upgrade](references/mobile/build-and-upgrade.md), [distribution/App Clip](references/mobile/distribution.md), [OTA and health](references/mobile/updates-and-health.md) or [workflows/hosting](references/mobile/workflows-and-hosting.md). Keep native artifact, activation, store/service and health evidence distinct.
