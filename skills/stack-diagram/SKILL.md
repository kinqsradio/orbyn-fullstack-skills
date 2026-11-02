---
name: stack-diagram
description: "Turn a described stack into an architecture diagram as self-contained HTML, PNG or TSX, with grouped nodes and three edge kinds. Use architect for system design and state or lifecycle diagrams, technical-illustration for model-driven figures and motion, product-illustration for faux product UI."
---

# Stack diagram

Use this when someone describes a stack, a service topology or an infrastructure layout and wants a picture of how the parts connect. The result is an engineering-style drawing: icons on tiles, labelled group boxes, orthogonal arrows.

One built HTML file is the source of truth. PNG and TSX derive from it. Keep job files in a git-ignored working folder, for example `output/<job>/`.


This draws what exists and how it connects. A diagram of how one thing changes over
time, with states, transitions and guards, is a statechart: use
[architect](../architect/references/statecharts.md), which checks it against the real
behaviour. A deployment shown here and a lifecycle shown there are often both useful. A diagram inside a film is redrawn in film code under the [code-only rule](../technical-illustration/references/code-only.md), using only logos the user supplied.
## Method

### 1. Settle the content

From the user's list, decide:

- **Nodes.** One per technology: a name and a short lowercase role such as `http server`.
- **Groups.** Draw a box around things that share a runtime, vendor or repository. Nest one level at most. Write labels in the brand's own casing.
- **Edges**, in three kinds:
  - accent solid (`e`): the primary request or data flow, ideally one continuous path
  - neutral solid (`n`): secondary internal connections
  - neutral dashed (`n dash`): dev-time and deploy-time relationships such as CI, hooks and IaC

From a flat list, infer groups and flows. Ask only when a tool is ambiguous enough that the diagram would be wrong either way.

### 2. Get the icons

Fetch logos only when the user asked for them and the network is available. Otherwise take pictograms and say so.

```bash
python3 scripts/fetch_icons.py <job>/icons client:generic/user api:generic/server
python3 scripts/fetch_icons.py <job>/icons --allow-network hono~server "betterauth:better-auth"
```

Logos are fetched per job, sanitised, stored in the ignored folder and embedded in that job's output. `build.py` and `render_png.py` refuse a folder Git would commit unless the user asked for `--allow-tracked`. Nothing branded goes into a repository or into this skill, and the script refuses a folder Git would commit.

- **Never recolour a logo.** People notice at once. A white logo goes on a dark tile (`tile dark`).
- **Official marks only.** simple-icons is not a source, because its glyphs are monochrome redraws.
- **On a miss or offline,** the node gets a neutral pictogram from `assets/generic`, the run prints `FALLBACK`, and the footer counts it. Tell the user which nodes lack logos.

### 3. Plan the coordinates

Read [geometry](references/geometry.md) before placing anything. The rule behind the rest: a node is its tile plus the text below it, so vertical arrows run from box bottom to tile top.

- Horizontal edge: tile side to tile side at `topY+30`.
- Vertical edge: from `topY_upper+100` to `topY_lower-4`, never from the tile bottom through the label.
- Elbow edge: the vertical segment in a corridor free of node boxes, the horizontal in the clear band between rows. Crossing an edge is fine; crossing a node box is not.

### 4. Build the HTML

Copy `assets/template.html` into the job folder. Replace the sample groups, edges and nodes, and fill `%%TITLE%%`, `%%KICKER%%`, `%%LEDE%%` and `%%FOOT%%`. Leave `%%CREDITS%%` for the build. Set `lang` on `<html>` to the label language. Keep colours and fonts behind the CSS tokens.

```bash
python3 scripts/build.py <job>/draft.html <job>/icons <job>/diagram.html
```

The build embeds icons as data URIs, sanitises every SVG again and writes the footer credit. It fails on an unresolved token or anything that would load at view time. For a dark default, set `data-theme="dark"` on `<html>`. To show a deploy to a platform that is a group, point the arrow at the most representative node inside it and label the edge.

### 5. Render and look

```bash
python3 scripts/render_png.py <job>/diagram.html <job>/diagram.png --scale 2
```

This writes light and dark PNGs using an existing Chrome, with the title, legend and credit included. Pass `--selector .canvas` for the bare drawing. Set `CHROME_PATH` if discovery fails; the script installs nothing. Open both images and read them. A successful exit proves nothing about layout. Check:

- No arrow crosses label text, and no arrowhead lands in text.
- Edge labels are readable and clear of group borders.
- Every icon is visible, including group-label icons in the dark render.
- Group labels sit top-left, clear of nodes and edges, with matching left and right padding.
- Nothing sticks out of its group or clips at the canvas edge.

Fix and render again until clean.

**Worked failure.** An API node has its tile top at 120 and a database below it at 350. The first draft draws `M487 180 V344`, from the tile bottom. The render shows the line running through the name and role. Change the start to the box bottom, 120+100+6: `M487 226 V344`. Then list every vertical segment and ask which node boxes it passes between its two ends. The answer must be none.

### 6. Deliver

- **HTML** is the default: the built file, self-contained and offline.
- **PNG** always comes from `render_png.py`. Never draw a separate image with another library, because the HTML is the single source of truth. Deliver both themes unless the user asked for one.
- **TSX:** convert the built HTML per [TSX output](references/tsx.md).

Build the HTML once and derive the rest. Keep the footer credit. It names the sources this diagram uses and states that logos remain the trademarks of their owners. Report any fallbacks.

## Boundaries

- This skill draws a system someone has described. To decide what the system should be, use [architect](../architect/SKILL.md) first.
- Output that embeds logos stays out of the repository unless the user decides otherwise.
- System fonts vary by host, so the HTML can reflow on another machine. The PNG is the fixed record.

## Read when needed

- For coordinates, spacing, edge classes and a worked layout, read [geometry](references/geometry.md).
- For spec forms, missed logos, fetch limits and placing marks, read [icons](references/icons.md).
- For a stack on AWS, read [AWS diagrams](references/aws.md).
- For a React component, read [TSX output](references/tsx.md).
