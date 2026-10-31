# Illustrated statecharts

Use when a reader needs an explanatory statechart with a domain illustration,
not as a mandatory style for every lifecycle diagram. Architect owns behavior,
projection and evidence; [technical illustration](../../technical-illustration/SKILL.md)
owns drawing craft. Preserve the [statechart contract](statecharts.md).

Examples demonstrate techniques, not a closed menu of domains, styles or graph
shapes. Choose the illustration from the requested system: a spacecraft, medical
workflow, game, checkout or distributed service can need different objects and
composition. Do not force a new domain into the workshop sample or reduce its
behavior to fit one of four templates. Operational input budgets protect a local
renderer; they are not a limit on the method. For unsupported layout, keep the
semantic records and author the appropriate drawing with the same contract.

## One semantic chart, two presentations

Start with the editable model/chart or a real numbered trace. Name the evidence
level: design sketch, bounded checked model, or observed code replay. Keep the
plain chart and accessible transition table beside the illustrated view. The
artwork must consume the same state/event records; do not separately rewrite a
story to fit an attractive picture. A trace plate is one execution, not the
complete branching graph. Keep omitted branches and full reports reachable.

Choose a metaphor from the actual domain: a job ticket for work, a dated delivery
slip for a lease token, a shop window enclosing its open substates. Write what
each visual object means and where the analogy stops. Decorative workers, tools,
plants or textures belong outside semantic node/edge/label regions. Decorative
objects never imply an unmodeled actor, transition, guard or concurrency rule.

An observed acceptance/rejection is a transition outcome, not its enabling guard.
Keep the raw event and observed outcome distinct; display a guard only from the
actual model/source contract.

For a flat chart, preserve forks, back edges, start and terminal distinctions.
For parent states, contain children visibly and attach transitions to the actual
source/destination boundary. For concurrent regions, retain separate lanes and
cross-region conditions; proximity does not prove independence. For a failure
path, number each actual occurrence, including repeated visits to the same
label, and name the broken rule in text. A red arrow between two bad-path nodes
is not necessarily a counterexample edge: highlight exact edge IDs from the
trace, not membership of its endpoints alone. Preserve `mayBreak` versus definite
violations and per-rule identity.

## Layout and art contract

Use the existing renderer's measured layout for a general graph, or a deliberate
sequence layout for a numbered trace. Keep one geometry record per drawn state,
edge and label. Stable IDs connect each occurrence to its raw state/action record.
A debug overlay must draw those actual bounds/routes, not an approximate second
layout. Do not claim a full graph renderer from a hand-positioned example.

Measure or conservatively wrap text using the delivered font; keep full labels
in the text table if the drawing abbreviates them. Grow the card/canvas or reject
unsupported input instead of hiding a guard. Routes begin/end outside and near their declared node boundaries; the helper
uses a 32-unit endpoint budget rather than silently reversing an arrow. Arrowheads stop outside cards; edge
labels have clear paper underneath. Keep textures subtle, strokes deterministic,
text contrast legible, and failure distinctions visible without color. Provide an
SVG and an offline HTML/text fallback with no required animation or remote font.
Inspect both the intended review width and a narrow viewport. A large plate can
have an explicit scroll/zoom view plus the readable text table; shrinking a dense
poster to phone width alone does not make its labels readable.

## Draw an explicit chart record

The original [illustration helper](../scripts/illustrate-statechart.py) takes an
inert JSON record with explicit canvas geometry. It emits `chart.svg`,
`overlay.svg`, `chart.json`, `index.html` and a hash receipt into a new directory.
Node IDs, parent/region membership, event/guard labels, explicit routes and trace
occurrences are supplied by the artifact author. The helper does not parse
arbitrary Mermaid, choose layout or discover reachable transitions. Its `--help`
contains the accepted fields. Use the existing checked compiler when checker
results are required; retain its original graph/report next to the art.

```sh
python3 skills/architect/scripts/illustrate-statechart.py \
  --input path/to/authored-chart.json --out path/to/new-art-package
```

Author data and optional domain drawing from the consuming system's own model.
Use the existing technical-illustration geometry method for a composition beyond
the helper's declarative primitives; the method has no fixed theme menu. Rendering
budgets and schema validation are execution boundaries, not a ban on new art.

## Reproduce and review

Keep generator, semantic input, style/assets, output and input/source hashes with
the consuming repository's design/review records. Existing prototype review
policies own saved comments and design updates; do not add another persistence
system. Output paths must be new so earlier reviewed versions survive. A fresh
render does not refresh a prior model verdict or establish source correspondence.

Check semantic record coverage, text escaping, determinism and preservation.
Inspect actual pixels for clipped labels, arrow direction, misleading grouping,
contrast and decoration over evidence. Compare the illustrated and plain views.
Change the model/source first when meaning is wrong, then regenerate both views.
Keep checks specific: layout and illustration checks do not qualify formal safety,
accessibility across every reader, or universal host/model performance.

The [leased-job example](../examples/leased-job/guide.md#illustrated-replay-plate)
provides an original runnable trace illustration with exact replay states and a
layout overlay. It illustrates a linear counterexample. Its domain metaphor is optional; use
the same semantic and layout contract for other domains and graph structures.
Report exact executable support separately from the broader authoring method.

## Reviewed inspiration

[Kevin Ngo's statechart art](https://kevintngo.github.io/statechart-art/) combines
four boba-shop models, domain objects, deterministic drawing and visible layout
provenance. Reviewed source revision
[`7b7b918bcc069941854a2973b2a26f71091c6fab`](https://github.com/kevintngo/statechart-art/tree/7b7b918bcc069941854a2973b2a26f71091c6fab),
31 October 2026, MIT. This method and the workshop illustration are independently
authored; no drawing code, models, fonts or assets are imported. Our existing
pstack compiler and Anatomy support retain their own pins and notices.
