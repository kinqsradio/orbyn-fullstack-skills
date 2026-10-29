# Optional checked statechart workflow

Select this path for a source-linked finite TLA+ check and a generated diagram,
not for an ordinary design sketch. The bundled compiler is unmodified pstack
runtime source at `1ba91fc25c0977741dd0e267849e6234b037ed0a` (plugin 0.15.36),
with exact [hashes and license](upstream/pstack-statechart/snapshot.json).
There is no bootstrap, active imported skill, network lookup or package install.
The independently authored adapter and view guard live under `../scripts/`.

## Prerequisites and doctor

Choose explicit trusted local paths for Node with native TypeScript support
(22.18+, 23.6+, or 24+), Java 11+, and **tla2tools 1.7.4**. Its required SHA-256 is
`936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`.
No Java, jar or renderer is bundled. Obtain prerequisites separately within the
user's setup scope if absent; otherwise report the missing check as blocked.
Do not execute the upstream bootstrap wrapper to make this command work.

Set `node_bin`, `java_bin` and `tlc_jar` to those actual paths, and `library` to
the outer library root. These names are example shell variables, not global
configuration. The same commands work from a nested consuming checkout because
source and output paths are explicit.

```sh
python3 "$library/skills/architect/scripts/check-statechart.py" doctor \
  --node "$node_bin" --java "$java_bin" --tlc "$tlc_jar"
```

Doctor reads/hashes the complete 26-file runtime closure, its notice, the local
ESM package boundary and the exact jar; it probes tool versions without writing
outputs or installing anything. It establishes readiness, not model correctness.
The pinned lifecycle uses POSIX shell/process-group signals: Windows is blocked.
macOS is locally qualified; Linux has the required execution primitives but
needs its own runtime and interruption qualification. Never edit a home/global
`package.json` to make TypeScript imports work.

## Run and retain the actual result

A view is a **trusted executable JavaScript module**, not inert input. Review it
and model/configuration before running. Choose a new task-owned output path
whose parent exists; neither output nor its sibling `.run` may already exist.

```sh
python3 "$library/skills/architect/scripts/check-statechart.py" check \
  "$model" --config "$config" --view "$trusted_view" --out "$new_output" \
  --node "$node_bin" --java "$java_bin" --tlc "$tlc_jar" --timeout 60
```

Omit `--view` for the compiler's detailed default. Files in `new_output.run/`
retain exact commands, tool/source/view hashes, stdout, stderr and a JSON receipt,
including preflight errors that produce no chart. Interrupted checks retain their
status and any observed surviving process IDs. Prior output is never overwritten.
SIGTERM/SIGINT or a deadline requests owned-child cleanup; exceptions after spawn
still settle the owned parent. A failed process observation cannot establish
complete descendant cleanup; keep that uncertainty in the receipt.

| Adapter exit | Interpretation |
| --- | --- |
| 0 | Compiler completed; read every requested rule and its bounds in report |
| 1 | At least one rule broken; other rules can still be not checked |
| 2 | Preflight, parse, projection, timeout or tool error; no successful verification implied |
| 143 | Cancelled; check incomplete |

Plain TLC has its own exit codes (for example 12 for the exercised invariant
violation). Compare actual property/termination messages, not numeric equality
with the adapter. SANY parse, TLC exploration, projection and rendering are
separate stages. A projection error can suppress compiler publication even after
checker work; use retained diagnostics or a separate plain-TLC run rather than
inventing a model verdict.

Read `report.md`, `chart.mmd` when present, `tlc.out` and any additional
`tlc-RULE.out`. Extra raw files are not guaranteed for every reported bug when
its path is already drawn. The [sample](../examples/leased-job/guide.md) obtains
an explicit single-property plain-TLC trace when needed. The compiler checks the
written configuration with one worker. After an initial failure, reruns have a
100,000-state cap: `Rules not checked` is not a pass. Above 500 states it can emit
only bug paths, or omit the chart on a passing model; graph omission does not
invalidate a completed model check. Do not silently shrink requested bounds.

VIEW/SYMMETRY representative states and state/action constraints need the
[projection interpretation](statecharts.md#projection-and-omission-guardrails).
An intended terminal stutter prevents a deadlock report but does not prove
liveness. Keep fairness and unmodeled environment behavior explicit.

## Guard a projection, then render it

The adapter adds a conservative view guard: for the same raw action and displayed
endpoints, mixed null/non-null step labels are rejected. Keep all instances or
refine the labels. Because null erases the intended label, this can refuse a view
whose safety needs a finer distinction. This is not a complete proof of hidden
edge semantics. Upstream separately checks reachability/bug paths, parallel-region
honesty and lasso fidelity; fallback or mixed `mayBreak` labels still need review.
Keep full qualified event IDs and per-rule identity in mappings and traces.

Use the existing [renderer adapter](../scripts/render-statechart.mjs) with an
explicit trusted installed Pele module when an inspected image is useful:

```sh
"$node_bin" "$library/skills/architect/scripts/render-statechart.mjs" \
  --input "$new_output/chart.mmd" --output "$new_svg" --pele "$pele_module"
```

Rendering never installs Pele, checks code or fills in an omitted chart. Missing
rendering can leave model checking complete but the visual result unverified.
Inspect the actual SVG at the intended width and retain Mermaid/text fallback.

## A complete runnable example

The [two-worker leased job](../examples/leased-job/guide.md) includes implementation,
model/configs, trusted view, source/action map, real counterexample replay and an
offline HTML/SVG preview generator. Its output is new and task-owned; it neither
modifies Orbyn nor copies shared skills into the consuming target.
