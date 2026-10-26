# Final behavior-skills review and focused reruns

26 October 2026. Local qualification of the uncommitted behavior-prototype change.
No commit, staging, push, PR, merge or deployment. Catalog: 34 skills.

## Independent source review and correction

A native reviewer independently examined the frozen 36-file change, its complete
402-file source packet, ownership/routing, executable renderer, distribution,
provenance and relevant checks. First-round verdict: no concrete correctness
defect. An optional test-coverage finding identified that renderer rejection-only
tests could miss an adapter which rejected every valid input.

Added two tests in `tests/test_statechart_renderer.py`: successful SVG output plus
attributable, explicitly unverified receipt; oversized SVG-result rejection with
no output. No skill method or runtime helper changed during this review task.
The reviewer approved the revised packet and independently demonstrated that
unconditional rejection and removal of the actual result-size guard each fail
the corresponding new test. All six renderer tests passed, and a fresh real-Pele
render succeeded. The independent source verdict does not by itself attest the
subsequent live-agent outcomes or visual quality.

| Identity | SHA-256 |
| --- | --- |
| Base commit | `6a872049f92e46bc1c0f8f55143500429739d507` |
| First review packet | `ab79217fc2ebf4e7f5c7c5b321b7d02e781012a6da636dbdfd78c81ff6fee6d3` |
| Approved final implementation packet | `ab0c15cfce72e263c86358e232f936c572d71913b59a7daa4117a39bfbcdc815` |
| Baseline methods, 280 files | `df2883e7b82011ff2f7a1d363bc62e1448e7baa0e68ce1921f29c001902aa6e0` |
| Final candidate methods, 292 files | `81b1d023aedf81b1b998f86e31dd73f5b83a67d912612d4237ba94bdde865959` |

The complete per-file methods inventory and unchanged tasks/fixtures/rubrics are
in the [final protocol](2026-10-26-behavior-final-review-protocol.json). Inventory
hashes use compact sorted JSON with separators `(',', ':')`. The final protocol
and this qualification report are additional evidence metadata outside the
402-file implementation packet. The packet's source bytes stayed frozen during
collection. No fabricated candidate Git revision is used.

## Fresh paired experiment

Four existing development cases, one baseline and one candidate call each,
with alternating condition order: eight scored calls, plus one unscored host
readiness call in this task. These are fresh runs against the exact final methods,
separate from the [earlier 16-call study](2026-10-26-behavior-prototypes.md).
The baseline is the existing 34-skill base commit, not the historical 54-skill set.
No new heldout or statistical-comparison claim follows from reusing development
cases. Outcome grading is by the implementing lead against the frozen criteria;
source review is independent.

Host: Codex CLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`, medium reasoning,
`service_tier=default`, fast modes disabled, workspace-write sandbox, five-minute
budget per call, at most two concurrent calls. Effective provider scheduling is
unverified. The user explicitly permitted priority processing for the native
independent reviewer only; the trial configuration stayed standard/default.
Existing user settings and the parent environment were not changed or repurposed.

Every condition has its own synthetic Git root, method copy and relative local
skill-discovery links. Per-call inventory inspection checks the 34 intended
skills and that their resolved advertised roots belong to that fixture. Evaluation
material is absent from the subject's method snapshot. The matching wrapper
restricts effects to the fixture and supplied installed tools; no installs,
downloads, accounts, external browsing, delegation, product repair, commits or
publication are authorized. Visible events, outputs, tool failures, answers,
termination, usage and duration are retained; reasoning items are excluded.

All eight calls completed within budget, each with the intended 34-skill
inventory. All original method files and supplied product inputs remained
byte-identical, excluding only verification artifacts explicitly authorized for
the drift task. Advertised discovery roots resolved inside each own fixture.
Outcome checks are distinct from which methods an agent actually read.

| Focused case | Baseline | Final candidate | Evidence inspected |
| --- | --- | --- | --- |
| Uncertain save preview | Core outcome confirmed; agent browser/HTTP blocked | Core outcome confirmed; agent browser/HTTP blocked | Actual inline-script/service-handler tests, real controller HTTP/browser checks, retry and reset fences, honest reopen instructions |
| Host interleaving and statechart | Violation and actual-code replay confirmed | Violation and actual-code replay confirmed | `observe_idle → admit → park`, source/model correspondence, model logs, Mermaid/SVG and separately rendered previews |
| New-writer verification drift | Updated model and reproduced bug | Updated model and reproduced bug | Old model pass, new admin writer, unchanged property, updated failure, actual entrypoint replay and preserved product sources |
| Checker output isolation | Safe → broken → safe confirmed in DFID | Safe → broken → safe confirmed in DFID | Separate logs/state outputs; original BFS failures retained; actual completion versus invariant violation distinguished |

Both conditions usually achieved the core outcome. The candidate's isolation
trial additionally retained shallow DFID attempts and explicitly rejected their
exit-0 results as incomplete because no completion message appeared. This is a
useful observed behavior, not a general superiority claim.

## Additional controller qualification

Controller checks run separately from the sandboxed trial agents and cannot turn
a blocked agent browser/checker invocation into an agent success claim.

Both generated previews passed real Chrome `156.0.8078.47` interactions against
the unchanged local Node HTTP fixture: one effect for normal save; draft retained
and outcome unknown after a lost response; same-key retry adds no duplicate
effect; reconciliation adds no write; reset prevents a late response from
changing the newer draft/status even when transport cancellation is deliberately
ignored. Each condition produced four logical effects from seven POST calls,
including browser transport retries. Both fit the tested 360px viewport and
supported field-to-control Tab navigation. Screenshots were actually inspected;
this is a bounded visual/keyboard check, not a usability or accessibility audit.
All servers and browser processes created for these controller checks were stopped.

Both host diagrams were rendered in Chrome and visually inspected at 1100px.
The candidate used the new Pele adapter; baseline explicitly authored SVG by hand.
Both show the prohibited state in text. Diagram rendering is separate from model
verification. Normal breadth-first TLC independently confirmed the host invariant
violations in both conditions; direct imports of unchanged Python public methods
reproduced `observe_idle → admit → park`.

For drift, both original models completed safely under normal breadth-first
TLC; both updated models violated `Protected`. Direct imports confirmed
`admit → maintenance_park` parks a busy host. For output isolation, normal breadth-first controller runs independently
confirmed Safe success, Broken violation and repeated Safe success for both
conditions, with a distinct state directory and log for every invocation.

## Checks, failures and limits

The full unit suite passed **157 tests**, including six renderer tests. Library
checks pass for 34 skills, provenance/licenses, links, generated host discovery,
presets and 295 distributed assets. The 194 evaluation definitions validate; their
suite identity is `645a60924336c39077acb04a33cb0c02d42d36a9006870decff5277fcd66eacd`.
These checks establish library structure and helper behavior, separately from
live-agent outcomes.

Trial browser launch and loopback listeners were blocked by the subject sandbox.
Default TLC breadth-first checks likewise failed on RMI listener initialization;
those failures are retained and excluded from property-success claims. Reports
identify supported DFID results and their limits separately. Baseline host work
also retained a failed nonexistent-module import and incomplete auxiliary search
attempts before reaching its documented result. The initial save harness timing
failure was corrected in the harness and preserved. An initial controller shell
invocation used the wrong output-directory base and failed before running TLC;
the subsequent absolute-path controller runs are separately retained. These
attempts were not discarded or silently counted as successful checks.

These are four small synthetic pairs on one configured model/host with one call
per condition. No candidate-only critical regression was observed in the checked
outcomes; that is not a statistically established improvement, enterprise-scale
qualification, unbounded proof, production concurrency test or human acceptance.
Finite serialized-command models do not establish deployed database isolation,
writer retirement, external process behavior or production scheduling. Screen
reader behavior, native devices and participant usability remain unchecked.

Raw evidence is retained locally in ignored `output/behavior-final-review/`;
fixtures are in ignored `repo/behavior-final-trials/round-2/`. The independent
reviewer reports are under `output/behavior-final-review/reviewer-probes/`.
These are local review artifacts, not publicly downloadable evidence. Preserve
while human review/reproduction is pending; report intentional retirement later.
The earlier human-preview resource has separate ownership and was preserved.
Unrelated work and `.freebuff/` were excluded. All changes remain uncommitted.
