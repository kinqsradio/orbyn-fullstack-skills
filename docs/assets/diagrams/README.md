# README diagrams

Each diagram has an editable Mermaid source (`.mmd`) and a checked-in SVG used by
the [main README](../../../README.md). These are conceptual explanations of the
existing engineering, workspace and contribution policies; rendering them does
not establish product behavior or verification results.

| Diagram | Source | README image |
| --- | --- | --- |
| Connected engineering workflow | [Mermaid](connected-workflow.mmd) | [SVG](connected-workflow.svg) |
| Nested workspace ownership | [Mermaid](nested-workspace.mmd) | [SVG](nested-workspace.svg) |
| Local lessons and reviewed improvements | [Mermaid](reviewed-learning.mmd) | [SVG](reviewed-learning.svg) |

## Editing and rendering

Edit the Mermaid source first, then regenerate and inspect its SVG. Keep the
source, image, README alt text and explanation aligned. The SVGs have a white
background and use generic sans-serif text, so viewing the README requires no
special fonts or diagram renderer. No font files or renderer runtime are bundled.

These SVGs were rendered with [Pele](https://github.com/obsidianmd/pele) 1.10.0 by
kepano / Obsidian, using the library's existing
[renderer adapter](../../../skills/architect/scripts/render-statechart.mjs).
From the library root, supply your own trusted, already installed Pele module
and write to a new review file:

```sh
node skills/architect/scripts/render-statechart.mjs \
  --input docs/assets/diagrams/connected-workflow.mmd \
  --output path/to/new-review.svg \
  --pele path/to/installed/pele/dist/pele.js
```

After rendering, retain the SVG's descriptive title and description and its white
background rectangle when replacing the checked-in image. Inspect every label,
arrow and grouping at a normal README width, including light and dark page
backgrounds. Use the [diagram guidance](../../../skills/architect/references/statecharts.md#produce-a-chart-people-can-read)
for readable exports. Mermaid-compatible renderers can lay out the same graph
differently; review the actual export rather than assuming source validity proves
readability.
