# Model and delegation policy

Use multiple model tiers according to the actual assignment. Model routing and
reasoning effort and processing speed are separate choices. Use the explicit
model/effort assignments below, always at standard processing speed.
The provider pairs below are Orbyn routing tiers, not measured equivalence in
capability, latency, price or reasoning budget.

<!-- agent-models:start -->

| Agent / selection              | OpenAI model / effort                 | Claude model / effort           |
| ------------------------------ | ------------------------------------- | ------------------------------- |
| `orbyn-agent`                  | `gpt-6.1-sol` / medium                | `opus` / medium                 |
| `orbyn-light`                  | `gpt-6-luna` / high                   | `sonnet` / medium               |
| `orbyn-middle` (explicit only) | `gpt-6.1-terra` / medium              | Not configured                  |
| Explicit human selection only  | `gpt-6-astra` / human-selected effort | `fable` / human-selected effort |

<!-- agent-models:end -->

Only the human selects a provider model from the registry's human-only tier.
Never select that tier automatically, including through
parent-model inheritance or a fallback. A human-selected strongest-model parent
does not implicitly authorize strongest-model children. Keep routine children on
the standard or light definitions unless the human explicitly selects the optional
middle tier or requests otherwise.
Do not silently replace a model the human selected.

## Update models in one place

[models.json](models.json) is the canonical, human-editable model and effort
registry for **both OpenAI/Codex and Claude Code**, including human-only models
and standard-speed settings. The optional `orbyn-middle` entry is Codex-only;
its `selection: explicit` is required, it cannot be a parent default, and no Claude
equivalent is generated. Edit the appropriate provider entries there when
models change. The sync command preserves unrelated configuration and updates
the supported hosts' parent settings, named-agent model/effort, descriptions and the table
above. It does not invoke a model or reload a running chat.

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

Review the diff before a new session. Do not replace the entire config from an
old snippet or setup script. The asset checker detects drift from the registry;
it does not silently rewrite files or act as a background watcher. If a running
host rejects a new named agent, refresh/restart that host through its supported
user controls; a config edit alone does not change this chat's fixed tool catalog.
Never remove the model pin or use a generic fallback to conceal discovery failure.

## Route the assignment

Use `orbyn-agent` for cross-cutting plans, architecture and ownership decisions,
complex implementation, ambiguous diagnosis and consequential reviews. Use
`orbyn-light` for bounded source discovery, clear small edits, documentation,
routine authorized verification and focused evidence collection. Roles do not
have a single mandatory model: select by scope, ambiguity and consequences.
See [roles](roles.md) for role responsibilities and examples.

`orbyn-middle` pins `gpt-6.1-terra` / medium as an optional Codex middle tier for
an explicitly selected assignment or authorized comparison. Luna High and Sol
Medium remain the routing defaults; never select Terra through automatic fallback,
escalation or parent inheritance. Confirm the explicit human model/tier choice in
the brief, keep the assigned scope, and report an unavailable model or unsupported
standard processing rather than substituting or starting a trial. Registration
makes an option discoverable; explicit selection is a policy instruction, not a
claimed runtime permission gate or measured capability ranking. It changes no
Claude routing. For a prepared comparison, use the
[optional model pilot](../../skills/orbyn-skill-creator/references/evaluations.md#optional-model-tier-pilot).

The owner may route a task from `orbyn-light` to `orbyn-agent` when the bounded
brief proves insufficient; record the concrete reason and pass existing findings.
Do not automatically escalate beyond the standard tier. Use one suitable model
for each assignment; multiple available tiers do not require a panel, duplicate work or
extra sessions. Keep prompts scoped, pass file references instead of whole
transcripts and reuse a matching child.

Use the model and effort in the generated table and named definition, sourced
from the registry. The light and standard tiers are not measured equivalents;
effort labels are model-specific. A non-default effort assignment requires a
recorded reason and supported definition/configuration.
Do not select xhigh, max, ultra or automatic deep-effort modes automatically. A human's
explicit model/effort choice takes precedence. Optional cheaper families or low
effort require an explicit human choice; they are not implicit fallbacks.

## Sessions and children

Follow [coordination](coordination.md). Separate user-owned project chats require
an explicit human request. A model tier does not create a chat. Each owner may
use at most two native children with disjoint write ownership and no recursive
fanout. Children report to their owner. Do not invoke separate `codex exec` or
`claude -p` processes for delegation. If native subagents are unavailable, continue
with one agent and report the lost delegation separation. The lead must review
substantial handoffs and verify authorized outcomes; an additional independent
reviewer remains optional unless requested.

Model availability is subject to the current host, provider and account access.
Report an unavailable model; do not silently substitute a family or install a
provider. Model routing does not authorize tests, messages, publication or other
effects beyond the assignment.
