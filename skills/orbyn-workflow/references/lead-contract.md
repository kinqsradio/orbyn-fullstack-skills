# Lead, delegate, review and deliver

Use for substantial work, before dispatching a child or reviewing returned work.
A small clear edit or narrow explanation can proceed directly under the
[workflow](../SKILL.md).

## Lead contract

The owning lead grounds and scopes the outcome, chooses the design and delegates
substantial investigation and implementation as applicable. The lead stays
responsible for integration, review and verification. A child forbidden further
delegation completes its assigned task directly and returns the artifact to its
owner; it never waits for a nested worker.

Before dispatch, establish the requested end state, exclusions, current checkout
and candidate, owning data/contracts, failure behavior and authorized evidence.
For continuation, choose the minimum [task record](task-record.md) that preserves
the next action; use a [structured handoff](handoffs.md) only when validation helps.
Reconcile stale revisions before acting. Routine work can rely on its existing
diff, PR and CI without another log. Resolve blocking facts first. Use the selected
playbook to shape the work rather than repeating every workflow phase.

For multi-step implementation, write a short throughput checkpoint:

- Blocking first steps before dispatch.
- Independent workstreams and their owned paths.
- Shared mutable state to separate or serialize under one owner.
- Smallest safe decomposition, including why one worker is sufficient when coupled.

Mark an inapplicable dimension briefly instead of manufacturing parallel work.
For read-only investigation, one line naming the independent slices or why one
investigator is sufficient is enough. Revisit the checkpoint when a phase changes
ownership or dependencies.

## Answer key

For substantial work, write the [answer key](answer-key.md) before implementation:
the commands that prove success, the expected end state and the protected paths. The
worker's brief names the outcome, not the key; a separate verifier checks the
committed candidate from a clean copy. Protected files are restored to their base before the
checks run (adding tests is welcome), unless the key marks a path strict, where any change fails.
Decide unit tests with tdd's [rule](../../tdd/SKILL.md#do-we-need-a-unit-test-here)
and record the choice in one line (`Tests: none, docs only`).

## Delegate within the current session

Resolve the [harness](harness-settings.md) first; its limits and tiers are the
default for what follows.

Follow the [consumer host and coordination boundary](project-policy.md#delegation-and-host-configuration).
Use configured named roles and preserve the required model, effort and processing
mode. Where the host has no such model, follow [delegate on any host](#delegate-on-any-host).
Never silently substitute a model, launch a hidden inference process or install a
provider. Library model presets are optional; consumer-owned policy wins.

Give each child its role, outcome, source/candidate, owned files, allowed effects,
exclusions, relevant pointers and stopping condition. Reuse matching children;
tell writers they share the checkout and must preserve others' work. Start with
one child and stay within the resolved `max_children` and `max_depth` (a read-only
child may use `read_only_children_extra` more), without recursive delegation.
Choose each child's tier from the resolved routing and pass the resolved settings
in its brief. Split independent outputs
only; serialize shared generated files and fixtures. Children return evidence to
the lead, who owns integration and review.

## Delegate on any host

The harness names tiers for Claude and Codex, but other hosts (OpenCode, Gemini CLI,
Cursor and more) can run children too. On every host, take these steps in order:

1. **Decide once.** Pick the unit by what the work is, on any host:

   | The work | Use | On a host that |
   | --- | --- | --- |
   | A piece of the current task whose result you need before you finish | A subagent (child) | Can run children in this turn (Claude's agent tool, Codex `spawn_agent`, OpenCode's task tool) |
   | A task of its own that ends in its own branch or PR | A separate session | Can start sessions (linked or side sessions, cloud tasks), only in `parallel` mode or when the user asks |
   | Either, where the host has neither | Do it yourself, one task after another | Has neither |

   Delegate these by default: a read-only search across many files or folders (a
   scout), and an independent review of a substantial diff before its PR (a
   reviewer, since you cannot claim independent review of your own edits). Otherwise
   delegate a slice only when it does not block your next step. A small clear task
   needs none. State the choice in one line and move on.
2. **Pick the model.** Use the resolved tier where the host offers that model. Where
   the host cannot choose a model, or the tier's models are not on it, the child runs
   on the session's own model. That is allowed, because the name and announcement say
   so; it is a silent substitution only when nobody is told. Set a model parameter only
   to a resolved tier model or one the user named. With no effort control, write
   `Default` in the Effort field.
3. **Announce it.** In the same message as the spawn, tell the user the child's full
   name and task in one line. When it returns, say in one line what it found or
   changed. A child the user never hears about is a defect, even when its work is good.
4. **Background or foreground.** Run it in the background when you have other work,
   and in the foreground when its result is your next step. Never poll it
   ([wait without polling](waiting.md)).
5. **Limits.** `max_children`, `max_depth` and `read_only_children_extra` hold on every
   host. On a host other than Claude or Codex, run `harness.py resolve` with either
   `--host` value: its delegation limits, work mode and cleanup apply, and step 2
   picks the model.

For example, on a host running only `deepseek-v4.1-flash`:
`Orbyn Scout 1 - DeepSeek V4.1 Flash - Default - Map settings panel` is announced as
"Starting Orbyn Scout 1 on the session model to map the settings panel, read-only."

## Name the children you start

Name every subagent or session you start so its work can be traced at a glance,
including a session that owns one issue: `Orbyn Engineer 3 - Sonnet 5.5 - Medium -
Automations - #181`, not just the issue title. The pattern is for children only: the
main session, the one the user opened and talks to, keeps its own title. Never rename
it to this pattern.

```text
Orbyn [Role] [N] - [Model] - [Effort] - [Task] - [Evidence or ID]
```

| Field | Use |
| --- | --- |
| Role | Engineer, Research, Architect, Reviewer, Verifier, Security or Scout |
| N | Counts up per role in this session from 1: Orbyn Engineer 1, Orbyn Engineer 2 |
| Model | The model that actually runs, such as Sonnet 5.5 or Terra |
| Effort | The effort that actually runs, such as Medium |
| Task | A few words on the outcome |
| Evidence or ID | Optional: a PR, issue, finding, threat id or commit |

For example, `Orbyn Engineer 2 - Sonnet 5.5 - Medium - Fix icon fetch - PR 71`, or
`Orbyn Security 1 - Opus 5.5 - Medium - Verify ledger guard - T9`. A reused child keeps its
number, and a replacement takes the next one, so a number always means one child. Rename a child that
escalates, so the name never reports a model or effort it is not using. Where the host's name
field is short, keep Role and Task and open the brief with the full name. A name the
user chose wins. Names are labels: they grant nothing, and in public repositories they
carry no private names or secrets.

Start separate sessions only as step 1 of [delegate on any host](#delegate-on-any-host)
allows: in `parallel` mode, within `max_active`, or when the user asks. They follow the
same naming. Do not create sessions recursively or turn design comparison into a model
panel.

## Execution invariants

Complete the agreed outcome, including necessary caller migration and removal,
without silently expanding authority. Use a small reusable tool for proven
repetition when its cost and failure behavior justify it. Separate concurrent
writers' files, fixtures and resources before serializing what truly must be shared.
Match each completion claim to direct evidence for the requested artifact; retain
missing checks as limits. Read the conditional methods for
[outcomes](principles/outcome-oriented-execution.md),
[automation](principles/build-the-lever.md),
[shared state](principles/separate-before-serializing-shared-state.md) or
[proof](principles/prove-it-works.md) when needed.
For requested rollout or incident work, use the CI owner's
[health and recovery method](../../orbyn-ci-design/references/rollout-recovery.md).

### Loop guard

When the same step fails the same way twice in one task (the same command or edit,
the same error), do not try it a third time:

1. Change the approach once, and say why in one line.
2. If that fails too, stop and tell the user what failed, what you tried and what you
   need from them.

A different error, a passing step or new evidence is progress and resets the count.
A long command still producing output is not stuck. A child follows the same rule and
reports to its lead. Stopping the user's running work is the user's call, never yours.

## Review

For substantial work, the lead must inspect the actual returned artifacts and
diff against the intended contract, including affected callers, authority,
failure/recovery and unrelated changes. Treat a delegate's summary as evidence to
inspect. Route concrete fixes back to the same child and review the resulting
diff. The lead writes the final assessment.

## Verify

The lead performs verification proportional to the changed contract and inspects
its results. An implementation request includes appropriate local checks unless
explicitly excluded; respect consumer limits and separate external effects.
Documentation needs document/link checks rather than product builds. When runtime
or surface evidence is unavailable or excluded, report that limit explicitly.

Additional independent Verifier/Reviewer assignments are optional unless requested.
Requested independent qualification uses the same frozen candidate and at most
three full review rounds under [delivery](project-policy.md#verification-and-review).
The same cap holds for any review or fix loop: after the third unresolved round,
stop and hand the decision to the user with the open findings. With PR authority,
that hand-off is a draft PR, never a ready one; see
[opening a PR](../playbooks/opening-a-pr.md#when-three-rounds-do-not-resolve-it).

Never weaken lint, format, type or test configuration, and never delete or loosen
a test, to make a check pass. Fix the code. A change to existing configuration
needs its own stated reason and the user's approval.

## Deliver

Deliver only the requested scope. Report changed behavior/artifacts, actual
evidence, unresolved limits and local/committed/pushed/merged/deployed state.
Report the result without ceremonial principle citations.

For authorized delivery, verify the successful owned commit and its validated tree
before pushing. A failed stage/commit stops dependent push, PR and CI actions; do
not treat a later command's success as repairing that missing prerequisite. Use
the [commit and push gate](../playbooks/opening-a-pr.md#commit-and-push-gate) for
the execution and remote-ref checks. Preserve the patch when host metadata is
blocked. Start a PR, merge, publish, deployment, external message or monitor only
under explicit authority; delegation and playbooks grant none.

If the current task demonstrates a meaningful general skill gap, follow the
[optional contribution feedback](../../orbyn-skill-creator/references/contribution-feedback.md):
prepare a concrete proposal, then offer it once without blocking the user's task.
Keep company-only material local. Publication, self-edits, telemetry and cross-user
learning stay off unless separately authorized; exact existing contribution
authority still applies.
