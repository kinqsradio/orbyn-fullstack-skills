# Evaluate a skill change

The [case suite](../evals/cases.json) contains routing requests, adjacent non-triggers
and artifact tasks. The [tool](../scripts/evaluate.py) validates cases, prepares
task inputs, grades recorded observations and compares matched runs. It does not
call a model, execute arbitrary artifacts, access accounts or infer a host's model.

## Three kinds of evidence

1. Static validation establishes that cases, skill references and rubrics are coherent.
2. Disposable fixture tests establish that tooling catches missing evidence,
   wrong routes, forbidden effects and malformed records. Fixtures are synthetic.
3. Recorded agent trials establish observations about a particular candidate,
   host/model and task. Human review remains necessary for prose, design and
   architecture quality. A transcript is evidence to inspect, not a trusted claim
   that its author performed every stated action.

Never present fixture scores as agent performance. A real run requires supported,
authorized host execution. Record the full host version, model, effort/processing
and relevant tool configuration in the `host` and `model` provenance strings.
Keep those strings equal for paired comparisons; use a fresh context and the same
fixtures, capabilities and task scope for each condition. Keep user/system policy
constant. Register only the intended skill selection; check that a baseline has
not inherited the candidate through global discovery or conversation history.

## Prepare and collect

From a library or pinned consumer checkout, select the committed revision:

First run one bounded readiness probe with the exact host binary and model settings
intended for the evaluation. Record unavailable authentication, unsupported runtime
or timeout as such. Do not silently change the model, install another runtime or
claim that an unavailable host passed. A different installed runtime needs its own
recorded version and a fresh probe.

Create a shared `protocol.json` object before collecting paired trials. Include
fixture hashes, task wrapper, skill selection, tool capabilities, timeout and
execution scope. Give both conditions the same file. `prepare` copies its exact
bytes and pins their SHA-256; `grade` rejects tampering and `compare` rejects a
missing or different protocol. Review the recorded commands against that protocol:
a matching checksum cannot establish that the runner followed it.

```sh
python3 skills/orbyn-skill-creator/scripts/evaluate.py validate
python3 skills/orbyn-skill-creator/scripts/evaluate.py prepare --output /tmp/skills-candidate --revision FULL_40_CHARACTER_COMMIT --host HOST_VERSION_AND_TOOL_CONFIG --model MODEL_EFFORT_AND_PROCESSING --condition candidate --trials 3 --protocol protocol.json
```

The output directory must be new. `tasks.json` contains requests without expected
routes or grading rubrics. `run.json` starts with every trial `not_run`. Give each
request to the authorized host, capture its visible transcript/tool events and
save resulting artifacts inside that run directory. Do not collect hidden reasoning.
Use `--split holdout` only after revising against the development cases; freeze the
candidate before looking at held-out results. The public split prevents accidental
reuse, not deliberate access to answers. Authors must not tune against it.

An observer fills each result from actual evidence:

- `status`: `completed` includes unsuccessful attempts; unfinished work stays `not_run`.
- `selected_skills`: canonical skills actually read; do not infer selection from prose.
- `actions`: observed categories, including `write`, `write_product`, `test`,
  `publish`, `deploy`, `merge`, `message` when applicable. `write_product` means
  modifying application source; writing the requested answer artifact is `write`.
- `transcript`: relative UTF-8 transcript filename; `artifacts`: relative UTF-8
  output filenames. Evidence must remain inside the run directory (2 MiB per file).
- `reviewer`: the person or supported reviewing agent that inspected the trial.
- `rubric`: for each criterion in the suite, record `status` (`pass`, `fail`,
  `unverified`) and an exact `evidence` excerpt for a pass/fail decision. Include
  enough transcript context to support a finding about an omission. A matching
  excerpt only establishes provenance, not the correctness of the review.
- `duration_ms` and `total_tokens`: observed integers, or `null` when unavailable.
  Never estimate missing usage as zero. Do not invent host identity or measurements.

```sh
python3 skills/orbyn-skill-creator/scripts/evaluate.py grade /tmp/skills-candidate/run.json
python3 skills/orbyn-skill-creator/scripts/evaluate.py compare --baseline /tmp/skills-baseline/run.json --candidate /tmp/skills-candidate/run.json
```

Grade returns exit 1 for failed or unverified trials and exit 2 for invalid evidence.
It records evidence hashes, missing trials and observed metrics. Routing and outcome
judgments stay separate: an outcome task can succeed without selecting the expected
skill. Comparison requires a complete matched case/trial set, suite hash and host/model
configuration and pinned protocol. Older records without a protocol can still be
graded individually, but cannot enter a paired comparison. Fixture runs cannot
enter a benchmark comparison. Review individual
failures and run variation; a small score change is not general improvement.

Label first-response routing trials separately from completed implementation. A
Markdown design cannot prove browser, native, provider or deployment behavior.
Keep timed-out attempts and earlier failures alongside any rerun; do not replace
them with a later success. If only one host is evaluated, other hosts remain
unverified even when they share the same skill files.

For Codex, consult the installed CLI's help and the official
[non-interactive execution guide](https://learn.chatgpt.com/docs/non-interactive-mode)
and [skill discovery guide](https://developers.openai.com/codex/skills). Isolate
global skills and previous context using supported per-run controls. Host behavior
and available flags vary by version; this evaluator does not launch a host for you.

## Suite evolution

When adding development cases, keep existing holdout criteria unchanged and record
the new suite hash. Prior reports remain tied to their recorded revision and suite
bytes; grade or reproduce them from that revision rather than rewriting their
results against an expanded suite. New cases require fresh observations before
claiming coverage or comparing scores.

## CI and contributions

Ordinary PR CI runs static case validation and fixture tests without model calls or
secrets. Run live trials explicitly on a reviewed revision using an available host;
retain their evidence outside the shared distribution unless it is synthetic or
reviewed for publication. Add only the public task, rubric and a concise result
summary to a contribution. Never give untrusted PR code a model key merely to grade it.

By default, commit the concise result report and a reproducible declarative
protocol with synthetic fixtures, exact revisions and grading criteria. Keep full
answers, visible tool captures, run records and debug traces in ignored local
output or explicitly approved CI artifacts. Preserve failed attempts there, and
retain their verdicts and limitations in the summary. Do not add per-run captures
to the template merely because they were useful during development. Checkpoint
and evidence retention belongs to the consuming project; setup must not create
log folders or export that project's records automatically.

Choose code-based checks for executable behavior, and calibrated human or model
review for subjective outcomes. Do not grade only output keywords, require a single
wording, or accept a task's own success assertion as proof. Extend helpers with an
actual failing input/output boundary when their behavior changes.

## Verify discovery isolation before scoring

A clean fixture and a disabled-feature flag do not establish the effective input.
Use the installed host's supported prompt-inventory preview when available to
check actual skill names, roots, descriptions, instruction ancestry and exposed
capabilities. Exclude global/system/plugin skills and previous context from both
conditions; check that a baseline has not inherited candidate methods. Preserve
the preflight receipt and do not score a contaminated trial as a matched run.

Disable discovery only through supported per-run controls. In the recorded desktop
host, folder-only skill overrides left extras visible; actual advertised
`SKILL.md` path overrides and resolved locations were needed, followed by another
inventory check. This is version-specific evidence, not a promise about every
host's setting syntax. Never edit global skills, user policy or installed caches
to force isolation. If the runner cannot establish it, report the limitation and
leave the comparison unverified.

Treat a missing fixture contract as an evaluation-input gap. Retain the original
rubric and observation as unverified where the criterion cannot be established;
do not penalize an answer for refusing an unsupported assumption. Correct a
development prompt or fixture in a new suite revision, freeze it before rerunning,
and report the follow-up separately. Do not silently regrade old observations,
combine different suites into a new full-suite score or weaken a criterion after
seeing a held-out answer. The callback-count assessment illustrates why a symptom
label alone is not a supplied expected-behavior contract.

This workflow is independently authored. Design references are
[Anthropic's skill creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md),
[agent evaluation guidance](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
and [SkillsBench](https://arxiv.org/abs/2602.12670v4). No evaluator code was imported.

## Consolidating a skill owner

For a bounded development question, `prepare --case <id>` can select an explicit
subset; repeat it for each case in the chosen `--split`. Pin the same subset,
rubrics, fixtures, tool configuration and trial count for both conditions before
observing output. Report the subset denominator, not the full suite count. The
helper rejects duplicates, unknown IDs and cases outside that split. No model
is invoked by preparation. A focused trial does not qualify unrun cases or hosts.

Keep observed historical trials tied to their original suite and revision. The
released 61-case suite before TypeScript consolidation is retained verbatim in
[the baseline archive](../evals/baselines/2026-10-24-55-skills.json). The active
suite migrates its two TypeScript selection identities to the language owner;
this is a new suite checksum, not a regrade of the old observations. New routing
and production-practice cases are development cases. Run fresh paired trials
before claiming a measured behavioral improvement from this candidate.

## Contribution workflow checks

The contribution milestone adds 13 development assessment cases covering stale
issue availability, overlap, target ownership, reproduction-only scope, runner
discovery, intermittent evidence, stale-head CI, pagination, feedback disagreement,
human gates, retry budgets, optional checks and separate external effects. Earlier
cases and holdouts retain their objects; the expanded suite has a new checksum.

`tests/test_contribution_workflow.py` exercises the actual managed copy and core/all
host installation with networking unavailable and no library root docs or tools.
It checks required support reachability, missing-asset rejection and preservation
of target policy/company guidance. Synthetic evaluator fixtures check that prepared
cases remain unverified, incomplete rubric evidence stays unverified and a recorded
forbidden message fails despite positive rubric assertions. These are packaging
and evaluator checks, not a live PR, framework test, agent score or host comparison.
Use fresh matched trials under the protocol above before claiming improved agent
behavior. Normal library CI already runs this test module through discovery.

## Paired handoff/readiness comparisons

For an authorized behavioral comparison of surface selection, delivery feasibility,
continuation readiness or PR waiting, freeze baseline/candidate skill revisions,
case definitions and identical host/model/effort/tool protocol. Use synthetic
inputs: requested surface plus known window/build/adapter facts; a local Git and
runner inventory plus saved-binding observation; delivery responses with a
transient, unknown or deterministic cause; and an event stream with pending/log
progress, terminal handles and new-head results. Keep response order and permitted
effects fixed so fixture changes cannot masquerade as guidance improvements.

Include successful and adjacent controls, such as component-only capture,
local-only fixes and valid reusable readiness/UI evidence. Score the chosen
surface/next action, evidence limits, preserved work and completion of the requested
wait, not verbosity or a guessed fixed number of polls. Capture material updates
and handle use; respect host-required communication and user steering. Preserve
failed/incomplete attempts and grade excerpts independently using the existing
recorded-run evaluator. Repeated matched trials are needed for reliability claims.
A source walkthrough or prepared protocol is not a run. No real account mutation,
provider call, consumer-app sweep or background service is implied; leave
unexecuted host behavior explicitly unverified.

## Optional comparative-research comparison

For an authorized behavioral trial, freeze three conditions: current guidance,
current guidance plus an explicit blanket GitHub-first research instruction, and
the conditional comparative-implementation candidate. Keep the same synthetic
tasks, source packets, permitted tool responses, host/model/version/effort, budget
and effects in fresh contexts; record the exact added blanket instruction. Include
all three `comparative-research-*` development cases: consequential uncertainty,
sufficient offline local precedent and a mismatched/licensing-sensitive source.
Supply exact local/spec/source revisions, implementation/caller/failure-test
excerpts and source rights so inaccessible live repositories do not confound the
comparison. Keep unavailable evidence unavailable in every condition.

Use the existing recorded-run evaluator and an independent reviewer. Score
correctness, missed assumptions, justified dependency/disposition and scope, plus
observed time/tool cost; citation counts or query counts alone do not establish
quality. Capture failed/incomplete attempts and stop behavior as well as success.
Do not modify holdouts after seeing outcomes or infer reliability from one run.
This protocol and its cases are unexecuted preparation, not a live comparison or
permission for external calls/installations.

## Optional model tier pilot

The optional library audit artifact at
`docs/evaluations/2026-10-27-optional-model-pilot.json`
(not part of a skills-only export) pins three self-contained case definitions,
source revision, shared entrypoint
packet and wrapper hashes, arms, repeats/order and budgets. It remains `not_run`
and not collection-ready until the exact supported host and effective settings
are verified and frozen. This is an artifact/reasoning comparison only, not a
coding, PR defect-detection or UI trial. Coding routing would need a later
independently replayed code task before any promotion.

Preparation only: compare `gpt-6-luna` / high, explicitly selected
`gpt-6.1-terra` / medium and `gpt-6.1-sol` / medium on the same supported Codex
host at standard processing. This is not a quality/cost ranking or authority to
invoke models. No pilot has been run. Model registration does not establish
account access, supported effort, effective processing or loaded-host discovery.
At collection, verify the intended host/version and each exact model/effort/tier
through supported host capabilities and current official documentation. If any
setting is unavailable, mark that arm blocked/unverified; do not silently replace
a model, upgrade/install tools, enable accelerated processing or start a paid call.

Use three existing synthetic development outcome tasks: `approval-contract`,
`retry-effect` and `narrow-feature-slice`. Pin the unchanged case suite SHA256
`2683c34e494b3854b768c15b7522a3ca507316645cc170aac6d417821e8eb65e`
and those exact case definitions. If the suite later changes, deliberately freeze
a new shared suite before collection; never tune old holdouts. Before any trial,
freeze the same committed skill revision, wrapper bytes, task/source fixture
hashes, permitted tools/effects, timeout/token budgets and acceptance criteria in
one `protocol.json` using the existing collection method. These tasks require
source-packet answers, not a real account or production service; keep external
effects disabled. Keep expected routes and rubrics hidden from the task context. The tool-free
pilot measures artifact outcomes; supplied entrypoints are not evidence of
automatic skill discovery or complete reference coverage.

Prepare separate run folders with `prepare --case approval-contract --case
retry-effect --case narrow-feature-slice --trials 3 --protocol protocol.json`,
supplying the pinned `--revision`, identical `--host`, exact arm-specific `--model`
(including effort and standard processing), `--condition candidate` and a new
`--output` for each arm. Use fresh contexts and the same pinned entrypoint context with no tools;
rotate arm order across matched repeats. All records initially remain `not_run`.
Three repeats per task/arm are a small pilot, not a reliability benchmark.

An independent reviewer grades actual artifacts and visible tool evidence against
the same acceptance criteria: correct contract, authority/failure handling,
material omissions and authorized scope. Use the existing `grade` for each run.
The existing `compare` requires identical model provenance and is unsuitable for
this cross-model pilot: do not spoof model identity or relax its gate. Instead
prepare a manually reviewed descriptive table of per-task/arm acceptances,
failures, incomplete/blocked attempts, observed latency and usage. Retain every
attempt, including failed/time-out runs and any separately authorized retries.

Report total observed model cost divided by accepted results and total elapsed
work time divided by accepted results, including all failed/retry attempts in
the respective numerators. Record model token/cache usage and the dated applicable
pricing/account basis only when actually available; subscription usage is not
proof of marginal dollar cost. Include reviewer time separately, or apply an
explicit consistent inclusion rule across arms. Missing cost/time stays unknown,
not zero. With no accepted results, per-accepted-result ratios are undefined.
Report the small sample and task differences; no broad speed/quality guarantee or
automatic routing/default change follows. Any later policy change needs its own
review and authority. Keep raw captures under ignored output as usual.
