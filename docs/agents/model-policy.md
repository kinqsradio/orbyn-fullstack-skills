# Model and delegation policy

Orbyn routes work by tier. A tier is a role in the harness, not a permanent
model identity: the lead tier decides, the worker tier builds what was decided,
and the scout tier does bounded mechanical work. Model, reasoning effort and
processing speed are separate choices; every tier runs at standard speed.
The provider pairs below are Orbyn routing tiers, not measured equivalents in
capability, latency, price or reasoning budget.

Every repository can tune these settings. Resolve them first with
[`harness.py`](../../skills/orbyn-workflow/scripts/harness.py); the
[harness map](harness.md) shows where that step sits and the
[settings reference](../../skills/orbyn-workflow/references/harness-settings.md)
defines the file, precedence and rejections. This page holds the library defaults.

<!-- agent-models:start -->

| Tier       | Agent              | OpenAI model / effort                 | Claude model / effort           |
| ---------- | ------------------ | ------------------------------------- | ------------------------------- |
| lead       | `orbyn-lead`       | `gpt-6.1-sol` / medium                | `opus` / medium                 |
| worker     | `orbyn-worker`     | `gpt-6.1-terra` / medium              | `sonnet` / medium               |
| scout      | `orbyn-scout`      | `gpt-6-luna` / medium                 | `haiku` / medium                |
| human only | explicit selection | `gpt-6-astra` / human-selected effort | `fable` / human-selected effort |

Effort cap: `gpt-6.1-sol`, `gpt-6.1-terra`, `sonnet`, `fable` may use at most medium effort. A repository file, local file or tier setting above the cap is rejected; only the user's explicit instruction in chat can go higher.

<!-- agent-models:end -->

Only the human selects a provider model from the human-only tier. Never select it
automatically, including through parent-model inheritance, escalation or a
fallback. A human-selected strongest-model parent does not implicitly authorize
strongest-model children. A repository or local file can never name a human-only
model; only the user's explicit `--set` can, and the resolver prints a notice.

## Which tier does what

| Tier | Used by |
| --- | --- |
| lead | Parent session, Architect, consequential Reviewer, all security work, ambiguous diagnosis |
| worker | Engineer: assigned implementation, tests and cleanup |
| scout | Investigator and Verifier on bounded mechanical work: file search, link checks, log extraction, classification, regenerating generated files, running a named check |

Leads stay strong; workers go down a tier because writing code rarely needs the
top model.

- **Claude worker (`sonnet`)** is the default coding model: features, bug fixes
  and routine development.
- **Codex worker (`gpt-6.1-terra`)** takes command-line fixes, boilerplate and
  bounded implementation. Complex engineering, multi-step changes and
  architecture stay with `gpt-6.1-sol`, so on Codex complex implementation routes
  to the lead tier. This is a deliberate difference between the providers.
- **Scouts never decide.** They search, extract, classify, regenerate and run a
  named check. They may also make tiny mechanical edits under clear instruction:
  a typo, a rename, a syntax adjustment, a tag. They never write new logic or
  debug. `haiku` may also make a fully specified tiny UI edit such as a label or class change. `gpt-6-luna`
  is narrower: light repetitive edits only, no new code and no debugging.
- Never use a scout for design, security, data migration, final review or anything
  with a judgement call.

### Why the worker tier is cheaper (our routing decision)

Choosing Terra for the worker tier is a judgement call. OpenAI describes Terra as
fast and efficient and names vision, computer use and writing, and its Codex
documentation names Sol for ongoing code work. We route bounded Codex
implementation to Terra for cost and keep complex work on Sol. This is our
routing decision, not a measured result, and no benchmark score supports it here.

List prices per million input/output tokens, observed 2026-11-02 and liable to
change: Sonnet $2/$10 against Opus $4/$20; Terra $1/$5 against Sol $2/$10; Haiku
from $0.10/$0.50; Luna $0.10/$0.50. There is no evidence yet that the worker tier
holds quality on our work. The prepared
[optional model tier pilot](../../skills/orbyn-skill-creator/references/evaluations.md#optional-model-tier-pilot)
is the place to collect it; until a run is recorded, treat the worker tier as unproven
and keep the lead's review of its diffs.

## Escalate, never silently substitute

When a worker fails or the task proves ambiguous, escalate one tier to the lead
and record the reason in the brief; Opus is the fallback when Sonnet fails. A
scout that meets a judgement call stops and reports; the parent routes the task
to the worker or lead. Escalation changes the tier, never the effort: effort is
fixed per tier and is not raised automatically. Never escalate to the human-only
tier. Pass existing findings to the next tier instead of restarting.

## Default routing and delegation

The tables below are the library defaults. A repository's `.orbyn/harness.json`
may only lower cost or tighten them; the owner's local `repo/.harness/` file may
also raise delegation limits; the resolved values are what the lead follows.

<!-- harness-defaults:start -->

Default delegation: `max_children` 2, `max_depth` 1 (children never spawn), `read_only_children_extra` 0.

| Role or work        | Claude tier | Codex tier |
| ------------------- | ----------- | ---------- |
| `lead`              | lead        | lead       |
| `architect`         | lead        | lead       |
| `reviewer`          | lead        | lead       |
| `security`          | lead        | lead       |
| `security_verifier` | lead        | lead       |
| `security_engineer` | lead        | lead       |
| `engineer`          | worker      | worker     |
| `engineer_complex`  | worker      | lead       |
| `investigator`      | worker      | worker     |
| `verifier`          | worker      | worker     |
| `mechanical`        | scout       | scout      |
| `tiny_edit`         | scout       | scout      |

Escalation: scout to worker, worker to lead.

<!-- harness-defaults:end -->

`mechanical` and `tiny_edit` name the bounded work a scout may take; the lead
routes other Investigator and Verifier work to the worker tier. `security`,
`security_verifier` and `security_engineer` stay on the lead tier on both hosts,
and no file can move them or any lead tier. A target file can only route a role
to a cheaper tier; the user's explicit instruction in chat outranks every file.

## Update models in one place

[models.json](models.json) is the canonical, human-editable registry for **both
OpenAI/Codex and Claude Code**: tiers, effort caps, delegation defaults, routing,
Claude minimum versions and the human-only models. The sync command preserves
unrelated configuration and updates the hosts' parent settings, named-agent
model/effort, descriptions, subagent limits, the portable
[harness defaults](../../skills/orbyn-workflow/references/harness-defaults.json)
and the tables above. It does not invoke a model or reload a running chat.

```sh
python3 scripts/sync-agent-models.py --write
python3 scripts/sync-agent-models.py --check
python3 scripts/check-agent-assets.py
```

The updater accepts conventional plain-text Claude metadata and rejects YAML
punctuation or multiline values it cannot safely emit. Unsafe TOML edits also
fail before writes if parsed unrelated values would change. A rejected update
leaves all generated destinations untouched; simplify the registry value or make
a reviewed tooling change instead of hand-editing generated model settings.

Review the diff before a new session. The asset checker detects drift from the
registry; it does not rewrite files or watch in the background. If a running host
rejects a new named agent, refresh or restart it through its supported controls;
a config edit alone does not change this chat's tool catalog. Never remove the
model pin or use a generic fallback to hide a discovery failure.

## Effort

Effort comes from the tier definition and is never chosen automatically. The
registry caps `gpt-6.1-sol`, `gpt-6.1-terra`, `sonnet` and `fable` at medium
because they are expensive. A tier, repository file or local file that asks for
more is rejected by `harness.py` and the sync command. The user's explicit
instruction in chat (`--set`) outranks files by the precedence rule, so only the
user can go above a cap, and the resolver prints a notice when they do. Do not select xhigh, max, ultra or deep-effort modes. Optional
cheaper families or lower effort need a recorded reason and supported
configuration.

## What the host enforces and what is policy

| Limit | Claude Code | Codex |
| --- | --- | --- |
| Concurrent children | Enforced: `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` in `.claude/settings.json` (host default 20) | Enforced: `agents.max_concurrent_threads_per_session` in `.codex/config.toml` |
| Spawn depth | Enforced: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (host default 3) | Policy only. Codex 0.166.0 parses `agents.max_depth`, but it is not documented, so nothing relies on it |
| Children cannot spawn | Enforced: the subagent definitions disallow `Agent` and `Task` | Policy only: the agent instructions forbid it |
| Model and effort passed when spawning | Policy only: the Agent tool takes `model` and `effort` parameters that override the definition. The lead must not pass `fable` or an effort above the tier | Policy only: `spawn_agent` takes a `model` field that overrides the definition. The lead must not pass a model other than the tier's |
| Read-only extra, routing, escalation, required checks | Policy | Policy |
| Per-repository values | Policy unless the target's host settings carry the same numbers | Policy unless the target's host config carries the same numbers |

`harness.py resolve --explain` prints the host values that would enforce a
repository's settings; it never writes them. Codex loads project
`.codex/config.toml` only for trusted projects. Codex 0.166.0 reads the limit as
`max_concurrent_threads_per_session` and still accepts `max_threads` as an older
name, so the sync writes only the new key. `multi_agent_v2` is off in this
library; if enabled, its limit lives under `features.multi_agent_v2`.

Minimum Claude Code versions: Sonnet 5.5 v2.1.284, Haiku 5.5 v2.1.293, Opus 5.5
v2.1.280. `harness.py` warns, without failing, when the installed version is
below the minimum for a tier's model. It reads the version of the running
Claude Code (`CLAUDE_CODE_EXECPATH`) first and the `claude` on `PATH` second.

## Sessions and children

Follow [coordination](coordination.md). Separate user-owned project chats need an
explicit human request; a tier does not create a chat. Each owner uses at most
the resolved `max_children` native children (default above) with disjoint write
ownership and no recursive fanout. Children report to their owner. Do not invoke
separate `codex exec` or `claude -p` processes for delegation. If native subagents
are unavailable, continue with one agent and report the lost separation. The lead
reviews substantial handoffs and verifies authorized outcomes; an additional
independent reviewer stays optional unless requested.

Model availability depends on the host, provider and account. Report an
unavailable model; do not substitute a family or install a provider. Routing
authorizes no tests, messages, publication or other effects.
