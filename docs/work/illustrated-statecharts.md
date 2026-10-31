# Domain-driven statechart artwork

The request is to improve the existing statechart capability with illustrative
art, using [Kevin Ngo’s statechart-art](https://kevintngo.github.io/statechart-art/)
as a reference. Examples demonstrate the method; they do not restrict supported
domains, styles or topology. Nesting, model defaults, compiler pins and formal
verification ownership remain unchanged.

## Reviewed mechanism and local decision

Source reviewed at `7b7b918bcc069941854a2973b2a26f71091c6fab`, 31 October 2026:
README, license, order and bug plate scripts, plus the public rendered page.
The source is MIT. Raw reviewed files and content hashes stay in ignored
`orbyn-references/`; this change imports no source, fonts, models or assets.

| Reference mechanism | Local decision |
| --- | --- |
| Domain objects replace generic boxes | Add original drawing craft under architect + technical-illustration, using the requested domain rather than a fixed boba/workshop template. |
| Plain layout is visible over finished art | Keep actual geometry records and a debug overlay, plus editable semantic data and a readable text table. |
| Four distinct structural examples | Preserve flat, parent and concurrent structures in the general method; demonstrate an unrelated nested/parallel domain as well as the leased-job trace. |
| Seeded pen/pencil drawing | Use deterministic original SVG textures/strokes and local fonts; no new Canvas/font/runtime dependency. |
| Bug illustration colors edges by endpoint path membership | Require exact edge/occurrence identity from a trace; two path nodes alone cannot establish that their connecting edge was taken. |
| Layout and artwork generated separately | Share one explicit geometry record between art and overlay; preserve full compiler Mermaid rather than introducing a second behavior parser. |

## Existing owners and boundaries

Architect owns states, guards, containment, projection and checker evidence.
Technical-illustration owns the domain metaphor, geometry, visual labels and
inspected artifact. The existing leased-job replay produces the exact initial
snapshot and observed transitions consumed by its illustration adapter. A generic
declarative SVG authoring path accepts explicit nodes/edges/groups and artwork
metadata; it does not infer semantics from arbitrary Mermaid or run TLC.
Existing compiler/Pele rendering is retained as the plain checked-model path.

One worker owns coupled renderer/example/tests; the lead owns guidance, evaluation,
provenance, integration and visual verification. Generated manifest changes are
serialized after integration. Work stays in one library feature worktree; no
consumer installation, provider/model call, external publication or target edit.

## Acceptance and verification scope

- Two unrelated domain artifacts: the actual stale-result replay and a nested,
  concurrent example with a branch, back edge and cross-region guard.
- Exact semantic records survive art/text generation: stable state/group/edge
  IDs, containment, raw events, guards, numbered trace occurrences and textual
  violation distinctions. Input claims alone are not checker receipts.
- Deterministic output, escaped labels, bounded validated inputs, no overwrite,
  explicit output ownership and no network/dependency acquisition.
- Actual browser inspection of illustration and overlay at review and narrow
  widths, with full labels accessible when the drawing is larger than the viewport.
- Focused helper/adapter/projection tests, a real leased-job model/check/replay
  run using existing trusted tools, evaluation structure and required library
  validation. No new hosted CI or model benchmark.

A successful drawing is visual evidence. A bounded TLC verdict and real-code
replay remain separately reported. The declarative renderer is not a general
Mermaid layout engine, does not prove independence of regions or code conformance,
and does not impose a fixed visual theme on future authoring.

## Observed local verification

The final local candidate passes library validation (36 skills, 324 Markdown
documents), host discovery/assets, manifest, model-registry and diff checks.
The reviewed full Python suite runs 235 tests: 225 pass and 10 optional cells skip.
A separate real-tool compiler run passes all 15 tests; projection checks pass
9/9 under the supported Node 23 runtime. The ordinary PATH Node 22.16 cannot
load the pinned TypeScript compiler; it was not substituted for the documented
supported tool. Library validation uses Python 3.13; PATH Python 3.10 lacks
required standard-library support. No installation or configuration change occurs.

The fresh leased-job demo checks the broken model (61 states/125 steps) and
corrected model (45 states/93 steps). Both actual counterexamples replay; fixed
rejection, cancellation and publication controls pass. The five-step published
failure supplies all six initial/transition snapshots for the artwork.
The separate spaceport drawing remains an unchecked design sketch.

Browser inspection covers final SVG artwork, exact record tables, the working
layout disclosure and loaded gallery images. At 390 CSS pixels the page remains
390 pixels wide and the 348-pixel figure scrolls its 760-pixel drawing. The
temporary DevTools viewport override was cleared. Desktop review width is 1280.
Final output and renderer hashes were read back and matched. This is not a
universal accessibility, live model or renderer-quality benchmark.

Local artifacts and reproducible command receipts are retained in ignored
`output/statechart-art/` in the feature worktree, including `HANDOFF.md`, final
packages, screenshot and `verification.json`. They are local review artifacts,
not public downloadable evidence. Only reusable source, synthetic examples and validation contracts enter the public
change; actual rendered packages, captures and command receipts remain local.


## Engineering workflow example

The additional `skills/architect/examples/illustrated-statechart/workflow.json`
overview draws the current task-to-closeout guidance as 11 nodes, 14 transitions
and four parent groups. It includes check/review recovery, verified commit/push,
PR/merge gates and distinct retained/retired dispositions. Full conditions for
abbreviated guards remain in edge details. This is policy illustration, not a
model-check result or live task-state observation. The generator is unchanged.
Its new package, IDs, source/output hashes and loaded browser image were checked;
all nine focused illustration tests and library validation pass. Local output
is `output/statechart-art/workflow-final/`, linked from the existing gallery.


## Pre-publication review corrections

The workflow illustration uses an owned checkout with isolation only when needed,
rather than mandating a new worktree for every edit. The commit transition retains
required checks, current evidence, diff review and existing task authority in its
full guard; it introduces no extra routine human approval checkpoint.

The renderer rejects routes whose endpoints do not sit outside and within 32
coordinates of their declared node boundaries, including reversed arrows. Raw input
bytes must match the typed chart record before a source hash can bind the output.
The replay adapter explicitly identifies supplied snapshots rather than claiming
that rendering establishes execution or checker provenance. Focused bad controls
cover these boundaries. Fresh `workflow-reviewed-v2/`, `spaceport-reviewed/` and
`checked-demo-reviewed/` packages retain the corrected source identities; earlier
packages and the existing gallery stay untouched as historical review evidence.
