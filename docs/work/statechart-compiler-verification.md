# Optional statechart compiler and leased-job qualification

Local candidate based on library `668194758568d3ac9fb7144826ad68b36e70dc2c`.
This report describes scoped source, checker, executable replay and render evidence;
it is not a claim of general agent superiority or production correctness.

## What changed

Existing architect/TDD guidance now makes mixed violations, hidden arrows,
parallel guards, temporal lasso fidelity, terminal/deadlock and VIEW/SYMMETRY/
constraint interpretation explicit. The optional compiler is a licensed offline
source bundle, not a new skill or default dependency. All 36 canonical skills,
nested ownership, model defaults and historical adaptation pins remain intact.
Six development cases were appended; all 366 earlier case objects, including
holdouts, are unchanged (372 total).

The bundle contains exactly 26 unmodified TypeScript runtime files plus the
original MIT notice from cursor/plugins `1ba91fc25c0977741dd0e267849e6234b037ed0a`,
pstack 0.15.36. The three reviewed upstream skill subtrees are identical to the
previous 519d36aa source review; no active upstream SKILL.md, shell bootstrap,
test corpus, Java/TLC or renderer is imported. Snapshot source paths and hashes
are checked by the existing offline source validator. Orbyn authors the Python
adapter, view guard, local ESM boundary, sample and tests separately.

The adapter verifies all runtime bytes, module boundary and the supported TLC jar
before launch; requires explicit tool paths; blocks Windows; uses fresh output
plus a sibling command/log receipt directory; and retains timeout/cancel/error
status. Exceptions after spawn still settle the owned parent. Unavailable process
inspection does not establish complete descendant cleanup. Doctor is read-only;
there is no implicit acquisition, package install, global configuration or target
sync.

## Reproduce

Follow the [compiler guide](../../skills/architect/references/statechart-compiler.md)
and [sample guide](../../skills/architect/examples/leased-job/guide.md). Explicit
trusted local prerequisites were Node 23.11.0, Java 22.0.2 and tla2tools 1.7.4,
SHA-256 `936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`
(TLC's own banner identifies Version 2.19). Observed host: macOS 26.2 arm64;
the Java process reports x86_64. No other OS/runtime cell is qualified here.
The existing trusted renderer was Pele 1.9.0, entry SHA-256
`7c40a25eeaf4370fb56c03d9d8f6780051c9c39b6c6ca36d53239075117097f5`.
Rendering source was not bundled or installed. Headless installed Chrome with
Playwright supplied browser layout observations; no native application claim.

Example command shape, with actual trusted paths and a new output:

```sh
python3 skills/architect/examples/leased-job/demo.py \
  --node "$node_bin" --java "$java_bin" --tlc "$tlc_jar" \
  --pele "$pele_module" --out "$new_demo_output"
```

The reusable script retains commands, source/tool/output identities, errors,
reports, diagrams and replay results. Full local development/qualification output
is ignored at `output/statechart-integration/` in the owned worktree; it is not a
public downloadable artifact. Independent review output is retained separately
in the primary checkout's ignored `orbyn-references/statechart-integration-review/`.
These folders are evidence retention locations, not cold-checkout dependencies.

## Four separate results

| Surface | Observed result | Limit |
| --- | --- | --- |
| Model | Broken: 61 states/125 steps, FreshResult four-step failure and PublishedFresh five-step failure. Fixed: 45 states/93 steps, all six requested rules hold including NoDeadlock and conditional EventuallyTerminal. | One job, two workers, epochs 0..2, finite serialized boundary; weak fairness of Progress and bounded expiry, not production scheduling. |
| Projection | Final fixed view emits 21 display states/32 arrows, broken 25/38; same-label omissions (23/31) are reported. Three concurrent regions retain cross-region guards. Separate correlated-fork fixture falls back; bad loop projection and hidden bug path are rejected. | Earlier coarse sample view fell back; final view does not. Do not transfer one view's disposition to another. |
| Source correspondence | Independent BFS through actual public methods matches the model's reachable states and all nonstuttering abstract transitions: fixed 45/70, broken 61/94. Action-to-method map and source digests retained. | Reachability comparison omits fairness/properties; separate TLC runs check those. This is bounded serialized sample correspondence, not a theorem about arbitrary JavaScript or distributed databases. |
| Replay | Both real TLC traces replay through public methods. Broken code visibly commits/publishes stale epoch 1 at epoch 2. Fixed code rejects it, consumes only the old delivery, preserves worker 2's lease and no result/publication, then commits/publishes epoch 2 once. Precommit and late-cancel controls pass. | In-memory one-job ledger; no external publishing, database crash durability or unbounded retry qualification. |

Independent plain TLC completed the fixed model with 45 states (exit 0) and
reported the broken FreshResult invariant (exit 12). The adapter uses exit 1 for
its violation report: numeric equality is not the comparison. The demo obtains
PublishedFresh's raw trace using a separately recorded single-property plain-TLC
run, because the compiler need not emit an extra raw file for every drawn bug.

The final HTML/SVG preview is generated locally under `demo-final/`. Its HTML
and all three SVGs are byte-identical to the browser-inspected `demo-v4/` outputs
(presentation hashes compared after regeneration). Its primary
view is a focused actual five-step failure path, with the complete checked
Mermaid/SVG graphs, reports and replay observations available alongside it.
Full graphs retain their 4046-pixel natural width in a horizontal scroll region;
full-size SVG links are provided. Browser checks passed at 1280px and 390px with
no page errors or mobile root overflow. Top, failure-path, readable full-graph
portion and mobile captures were inspected. No dark-theme, every graph position,
print or assistive-technology qualification is claimed.

## Negative controls, partial checks and failures retained

- The pinned compiler alone accepted the synthetic partial-hidden-arrow case.
  The added Orbyn guard conservatively rejects mixed null/non-null visibility
  for one raw action plus displayed endpoints. Fully visible, fully hidden and
  refined-endpoint controls pass. This is deliberately narrower than a general
  proof of projection/hidden-edge semantics; no upstream file was rewritten.
- Mixed safe/violating labels retain `mayBreak` and rule identity; cross-region
  guards survive; invariant and temporal rule keys with equal names stay distinct.
  Qualified temporal actions retain `C!Up`/`C!Back`. Temporal lasso and invariant
  outcomes are tested separately.
- Intended terminal stutter is distinguished from an actual deadlock. Disabled
  deadlock detection is not reported as a pass. VIEW, SYMMETRY and constraint
  behavior/disclosure are exercised without claiming unconstrained completeness.
- Independent 502-state safe fixture completes with Safe/NoDeadlock holding and
  no chart (500-state display budget). Independent 100005-state fixture reports
  BreakEarly's one-step failure, then keeps Safe/NoDeadlock **not checked** when
  the 100000-state rerun cap is reached. An exit 1 is not full verification.
- Missing tools, unsupported Windows, unknown jar identity, changed runtime byte,
  existing output sentinel, malformed model, projection error, real deadline and
  SIGTERM controls are covered. Observed owned processes settle for the real
  interruption fixtures. A mocked process-observation denial tests the exception
  cleanup contract only; it is not independent real-process qualification.
- Cold copy beneath a CommonJS ancestor works using the local architect ESM
  package boundary, without editing home/global metadata or installing packages.

Earlier development attempts remain retained: a first TLC help probe incorrectly
expected exit 0/usage spelling; an initial correlated-region test used a valid
synchronous step that did not require fallback; two interruption fixtures used an
unsettled promise without a live timer and therefore exited rather than blocking.
These fixture/probe errors were corrected rather than labeled successful checks.
The first demo guessed an absent additional trace filename, and the second
plain-TLC trace attempt failed cross-directory configuration resolution. Both
failures remain; the corrected command colocates an identical model copy and its
selected config in owned output. No earlier run was overwritten.

## Integration and usability evidence

Local required checks pass: 192 Python tests under Python 3.11.5 with all
Java/TLC opt-ins enabled (59.538 seconds),
9 pure Node projection/identity tests, library/source/license/link/manifest
validation, host/catalog discovery and `git diff --check`. Ordinary Python CI
without explicit trusted tool variables runs adapter/packaging contracts and
reports nine engine integration tests skipped; those are not automatic live
qualification. Independent review additionally ran the pinned upstream
chart/pipeline tests: 60 passed, zero skipped, not the whole upstream corpus.

One fresh-context candidate-only cold-use observation routed from root guidance
through architect/statecharts to the documented compiler. With explicit trusted
Node/Java/TLC paths it reproduced both variants and both replays. The all-in-one
preview first failed for missing `--pele`; no renderer path was fabricated or
installed. An assisted follow-up supplied the existing trusted module and the
full documented demo then completed. Rendering assistance is separate from
unassisted discovery and from the independent browser inspection above. All
initial failures and scoped before/after hashes are retained. Only the sample
guide changed between those observations; executable/model/compiler bytes did
not during the trial. A subsequent conservative-guard input-validation correction
rejects a malformed nonfunction step export instead of silently substituting it;
the added Node negative control and regenerated full demo pass. The cold trial
therefore describes the earlier guard bytes, not an exact final-candidate trial.
Effective inherited model/effort are unknown and were not changed. This is
one usability observation, not a model ranking, paired performance benchmark or
statistical reliability estimate.

At the author handoff the candidate was local and uncommitted; delivery state is
reported separately from these qualification results. Independent review of the
frozen 55-file candidate passed all 192 tests with zero skips under Python 3.13.3
in 62.755 seconds, all nine Node tests, and the library/discovery/source checks.
No publication, merge, Orbyn edit, global setup, REA upgrade or deletion of other
work is included in these qualification results.
