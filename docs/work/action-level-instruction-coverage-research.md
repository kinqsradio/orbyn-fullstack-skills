# Action-level instruction coverage in nested agent workspaces

Status: research proposal; experiments and runtime enforcement are not implemented
by this document. Date: 2026-10-26.

## Purpose and minimality

Keep the nested repository method as the everyday product: open the outer library,
select a target/worktree, read applicable guidance, search within the selected
scope, and work. Evaluate this method without making the research harness a
required runtime dependency.

One canonical outer skill library contains ignored, independently versioned target
repositories and their sibling worktrees. Targets retain their own instructions,
skills and history. Shared skills are never installed, copied or synchronized
into targets. No daemon, vector index, mandatory hook framework, additional memory
store or per-target configuration is required by this proposal.

```text
orbyn-engineering/
  AGENTS.md
  skills/                       canonical shared skills
  .agents/skills/               existing discovery links
  .claude/skills/               existing discovery links
  repo/                         ignored by outer Git
    shop/                       independent target repository
    shop-wt/fix-checkout/       exact selected worktree
    another-project/           separate target
```

Memory follows logical target scope through its existing owner. This proposal does
not relocate private records into the public library or initialize memory. Shared
project memory is not automatically valid for every worktree. Branch-dependent
facts need current evidence from the selected checkout.

## Existing owners and related documents

- [Nested workspace contract](../../skills/orbyn-setup/references/repository-workspaces.md)
  owns target layout, instruction ownership and discovery limitations.
- [Nested-only workspace decision](nested-only-workspaces.md) records the layout decision.
- [Installation](../installation.md) and [workspace ownership](../synchronization.md)
  own onboarding and public/private boundaries.
- [Local engineering memory](../../skills/reflect/references/memory.md) owns current
  opt-in capture, project bindings, retrieval and private storage.
- [Memory design](learning-memory-design.md) supplies memory rationale and lifecycle
  design; current implementation claims must be checked against its owning guide.
- [Investigation](../../skills/how/SKILL.md) owns bounded source search.
- [Skill maintenance](../../skills/orbyn-skill-creator/SKILL.md) owns coordinated
  routing, evaluation and generated discovery updates.

Improve these owners rather than create a competing coverage skill or store.
Practical guidance upgrades can implement scoped procedural behavior. The stronger
coverage claims below require separate observations and experiments.

## Research question and exact candidate novelty claim

Can a minimal filesystem-based method reliably supply instructions applicable to
each coding action while limiting code and memory retrieval to the selected
workspace and avoiding duplicated skill installations?

> We propose and evaluate a scope-aware method for nested agent workspaces that
> derives the instructions applicable to a concrete coding action, connects those
> instructions to the model request producing the action, and identifies when
> changes to instruction scope, contents or worktree identity invalidate that
> coverage, without installing shared skills into target repositories.

This is a candidate contribution, not established novelty. Nesting, scoped search,
hashes, dependency invalidation, action gates and provenance are existing ideas.
The potential contribution is repository-specific evidence derivation and its
evaluation across workspace and agent-context transitions. If an existing method
already provides the complete contract, report an integration or benchmark
contribution rather than inventing a broader originality claim.

Hypotheses:

- H1: explicit target selection and action-specific resolution reduce missing
  instructions compared with native loading alone.
- H2: choosing code and memory scope before retrieval reduces sibling-target and
  sibling-worktree contamination.
- H3: refreshing affected context preserves coverage at lower read/context cost
  than full applicable-instruction reload before every proposal. Drop this
  optimization if the simpler baseline is equally effective at acceptable cost.

## Closest methods and remaining distinction

This table records the preceding source review, not reproduced experiments.
Publication/specification maturity varies; source descriptions do not establish
support in an installed host.

| Method | Existing capability | Distinction to investigate |
| --- | --- | --- |
| [AgentSpec, ICSE 2026](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf) | Triggers, predicates and runtime enforcement | Derive trustworthy repository instruction and request-lineage inputs; do not claim a new generic gate |
| [Agent-C](https://adharshkamath.github.io/papers/agentc.pdf) | Temporal constraints over agent actions | Supply applicability, delivery and invalidation events; temporal prerequisites themselves are prior work |
| [Agent Hooks](https://github.com/responsibleai/agent-hooks/blob/a90e56e91a6ef226c15eb84842efa411423e85c7/spec/AGENT-HOOKS-0.1.md) | Model/tool interception and context ordering under a cooperating host | Repository-specific profile and required linkage; complete mediation is not promised |
| [True Memory Fragments reflex](https://github.com/kyle641320/true-memory-fragments/blob/16ca0b72a3a268d966fbf9daca00bb9894b8c143/integrations/reflex/README.md) | Source freshness, covered pre-tool checks and localized refresh | Instruction applicability and originating-request inclusion, rather than index freshness alone |
| [PCAA](https://arxiv.org/html/2606.04104v1) and [CAVA](https://arxiv.org/html/2607.13716v1) | Action admission, fingerprints, contextual bindings and receipts | Evidence derivation, not a new per-action receipt format |
| [ACLE-MCP](https://arxiv.org/html/2609.02690v1) and [Proof of Execution](https://arxiv.org/html/2607.05397v1) | Fresh scoped authority and execution/replay contracts | Applicable instruction discovery and request linkage remain separate inputs |
| [Rel(AI)Build](https://arxiv.org/html/2606.26924v1) | Definition hashes, locks, audit records and workflow phases | Action-specific coverage rather than general workflow reproducibility |
| [SLSA provenance](https://slsa.dev/spec/v1.2/build-provenance) | Artifact provenance and build inputs | Recording evidence does not itself enforce instruction delivery |

## Task context and search contract

Maintain task-local facts: outer library, actual target Git root, exact worktree,
selected search roots, authorized memory scope (or none), and requested outcome.
These facts can remain in the conversation; no new manifest or registry is required.
Resolve paths and Git identities rather than equating names or remote URLs.

Choose permitted roots before searching; apply relevance filters inside them.
Never search all private projects first and filter returned results afterward.

| Selector | Default boundary |
| --- | --- |
| Outer library | Relevant library paths, excluding nested targets and private memory |
| Individual codebase | Its selected checkout, not a union of all worktrees |
| Individual worktree | That exact checkout, excluding sibling checkouts |
| Package/module | Selected subtree; widen deliberately when dependencies require it |
| Multiple targets | Explicit authorized set with target identity retained on results |
| Memory | Select the authorized store and applicability before retrieval |

Instruction lookup and implementation search are different scopes. A search within
`payments/` still needs applicable root/ancestor guidance. Instruction discovery
explicitly probes required hidden/ignored locations instead of relying on ordinary
content-search defaults. A nested Git root is not proof that a host stops ancestor
instruction discovery there; use the declared host/user policy and observed evidence.

Use ordinary explicit `rg` paths and filters before considering a helper. Account
for symlinks and nested independent repositories so they do not silently widen
scope. No-match results describe the searched area, not the whole codebase. Widen
within already authorized scope when justified; this is not a new approval ritual.
Memory is evidence, not permission or a source of higher-priority instructions.

## Coverage contract

Initial supported actions are explicit file edits/patches with known paths.
Unknown-effect shell commands are outside complete action-coverage claims. Search
operations are evaluated separately against the retrieval boundary above.

For action `a`, let `T` be the selected target/worktree, `R(a,T)` the required
instruction set under a versioned scope/precedence policy, `Q(a)` the originating
model request, and `t` the instant immediately before execution.

| Obligation | Requirement |
| --- | --- |
| Target | Actual action paths belong to the selected authorized target scope |
| Applicability | R includes required outer, target, applicable nested guidance and explicitly mandatory references, with conflicts resolved by declared authority |
| Delivery | Selected contents of R occur in Q with the intended instructional role; matching text quoted as data is insufficient |
| Freshness | At t, relevant contents, scope-selection conditions and target identity match the proposal evidence |
| Lineage | The executing action is the action linked to Q; material changes require another check |

Required means selected by explicit rules, not every potentially useful skill or
every hyperlink. Current user scope and higher-priority host instructions still
govern; the resolver does not invent an authority order from filesystem nesting.

Outcomes are **satisfied**, **violated**, and **unknown**. Missing observations or
unsupported actions produce unknown, never satisfied. A procedural method can
attempt the contract without proving all its obligations.

Distinguish evidence levels: tool-returned file content, observed inclusion in the
submitted model request, and enforced admission on intercepted execution paths.
Neither a file read nor a host hook declaration proves the next level. Request
inclusion does not prove comprehension, obedience or provider-internal handling.

If required guidance was missing or changed after generation, deliver the current
guidance and request a new proposal. A later read cannot qualify the old proposal.
If the concrete path is first known after generation, resolve against that proposal
and repeat with missing guidance; bound retries and report unresolved coverage.

Track newly created/removed instruction files and precedence changes as well as
hashes of known files. An unrelated commit need not invalidate coverage; uncommitted
relevant edits can. Child agents need their own delivery evidence. Compaction can
remove required contents even if an earlier transcript recorded a read.

Concurrent writes create a check-to-execution race. Only a supported synchronization
or snapshot boundary can strengthen the guarantee at execution. Procedural checks
must report this limitation. One action that changes instructions may invalidate
later queued actions from the same model response.

## Baselines and ablations

Keep tasks, initial contents, instructions and model settings comparable.

| ID | Condition | Purpose |
| --- | --- | --- |
| B0 | Existing nesting, native discovery and ordinary search | Current baseline |
| B1 | Explicit target selection and instruction reads once at task start | Small procedural improvement |
| B2 | Re-resolve and fully reload applicable instructions before every edit proposal | Strong simple conservative baseline |
| B3 | Freshness checks on already-known instruction files | Isolate discovery and request-linkage value beyond hashes |
| P | Scoped retrieval, action-specific applicability, request linkage and relevant invalidation | Complete proposed method |

B2 must discover new applicable files, not merely reload an old list. Compare P
without retrieval scoping and P without request linkage as separate ablations.
The five-arm pilot below excludes these ablations; add them in a separately scoped
follow-up. Compare an existing policy engine using the same derived evidence in
deterministic tests; equivalent decisions indicate evidence derivation, not gate
novelty. Measurement instrumentation must not silently repair a baseline's behavior.

## Evaluation cases

Hand-author expected instruction sets, search roots and verdicts independently of
the proposed resolver. Each case has a valid control and a broken trace: 32 initial
deterministic traces. Unsupported observations may correctly produce unknown.

| ID | Scenario | Required result |
| --- | --- | --- |
| C01 | Unchanged outer and target guidance | Satisfied with complete evidence |
| C02 | Action enters a directory with nested guidance | Include before a qualifying proposal |
| C03 | New nested instruction after generation | Invalidate despite matching old hashes |
| C04 | Applicable instruction edited without commit | Invalidate |
| C05 | Applicable instruction/override removed | Recompute and regenerate if selected contents change |
| C06 | Unrelated source or subtree guidance changes | Preserve coverage if applicability is unchanged |
| C07 | Identical paths/symbols in two targets | Retrieve and act only in selected scope |
| C08 | Same path differs between worktrees | Use selected worktree contents |
| C09 | Package-only search with root guidance | Narrow code search while preserving governing instructions |
| C10 | Relevant dependency lies outside initial narrow search | Widen deliberately; avoid false absence claims |
| C11 | Symlink/nested repository escapes selected roots | Exclude or explicitly expand authorized scope |
| C12 | Relevant-looking memory belongs to another project | Exclude before results reach agent |
| C13 | Project memory describes another branch | Verify against selected checkout before consequential use |
| C14 | Compaction or child handoff loses instructions | No coverage inherited merely from a prior read |
| C15 | Missing instruction read after proposal generation | Old proposal remains uncovered; regenerate |
| C16 | Relevant change between admission and execution | Detect/block under supporting harness, otherwise disclose unknown race |

## Experimental protocol and measures

Run deterministic evaluation first. A later, separately authorized exploratory
agent pilot uses six held-out tasks across three fixture repositories: two each
emphasizing discovery, retrieval/worktree isolation, and context invalidation.
Five conditions B0-B3/P times six tasks times two repetitions gives **60 runs**.
Use one fixed host/model configuration, restored fixtures and fresh sessions;
randomize condition order and retain failures/timeouts. Keep development fixtures
separate. This pilot estimates feasibility and variance, not general superiority.

Record exact fixture, library, host and model versions/settings; instruction bytes
or accessible immutable references; relevant dirty-file contents; request/action
linkage; observed transitions; expected and actual verdicts; task outputs; and cost.
Hashes alone do not reconstruct inputs. Keep real captures private/ignored under
explicit retention scope; publish only reviewed synthetic evidence when authorized.

Measure incorrect coverage acceptances, unnecessary invalidations, out-of-scope
retrieval, missed applicable instructions, task outcomes, reads, context volume,
model calls, time and verifier replay agreement. Report denominators and unknowns.
Compare paired tasks; actions within one task are not independent experiments.
Use pilot variance to size a later held-out study. Cross-host claims need replication.

Distinguish evidence reconstruction, deterministic verifier replay, and model
reruns. Reconstructed requests do not guarantee identical model output.

## Decision rules and delivery sequence

1. Freeze the contract, fixture oracle and baseline definitions. Resolve evidence
   availability per host before claiming request or execution coverage.
2. Upgrade existing procedural guidance minimally and validate routing/links.
   This does not implement or prove the research harness.
3. If authorized later, build the disposable deterministic evaluation and inspect
   false acceptances, unnecessary invalidations and unsupported cases.
4. Run the separately authorized pilot only after the deterministic contract is
   credible; report results before expanding scope.

Any false satisfied result in a supported deterministic case blocks a correctness
claim. Keep unknowns visible. Prefer B1 if it performs equally well. Prefer B2 over
incremental machinery if its cost is acceptable. Without request visibility,
report read/discovery evidence only. Runtime gates are a later option justified by
measured failures, not a required repository dependency.

Deliver a specification, reproducible synthetic evaluation package and empirical
report. Possible outcomes are engineering integration, a repository-specific
method, or a benchmark contribution. Do not promise a new invention or productivity
gain before comparative evidence exists.

Skill implementation and research verification are separate responsibilities.
Orbyn Skills Builder 2 owns the authorized procedural skill upgrade; Orbyn Engineer
Product Research owns this proposal and verifies the changed contracts, actual diff,
validation evidence and minimality. Static validation is not a live-agent trial.
No runtime harness, model experiments, publication or memory capture follows solely
from saving this proposal or upgrading its procedural guidance.
