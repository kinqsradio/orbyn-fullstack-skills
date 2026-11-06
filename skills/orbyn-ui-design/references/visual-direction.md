# Choose and carry a visual direction

Use for a new screen/site, a requested redesign, or a visual-quality review.
For a small fix, preserve the existing direction and inspect only its affected
states. This method is adapted from Hallmark; see the pinned
[source record](hallmark-source.md) and [MIT notice](hallmark-LICENSE.txt).
It is maintained as part of Orbyn UI design and needs no upstream installation.

## Start with the actual job and material

Identify the audience, primary task, surface and requested depth: audit, polish,
restyle, or redesign. Audit produces findings; polish fixes local defects;
restyle changes visual tokens while retaining composition; redesign can change
composition within the user's scope. Do not expand a button fix into a new site.

Inspect existing design guidance, component/token owners and real content before
asking questions. Use supplied answers and reasonable stated assumptions for
reversible choices; ask only when an unresolved decision materially changes the
outcome. Brand values come from project files or authorized primary sources,
never a remembered hex value or an inferred logo. Existing brand and accessibility
requirements constrain the direction even when a fashionable alternative differs.

Inventory usable material: product views, words, images and verified facts. Mark
missing proof explicitly. Do not invent customers, quotes, prices, availability,
usage counts or successful transactions. Synthetic prototype data must be labelled.
Use a real product view when available and authorized; a fabricated browser frame
or screenshot cannot establish implemented functionality. Check each external
asset's own license and required attribution; a repository's MIT license does not
automatically cover linked photography, fonts, marks or third-party artwork.

## Make the composition specific

For a consequential new direction, sketch two or three genuinely different
options briefly, then choose using the person's task, content and brand. A routine
screen in an established app normally needs one consistent extension, not a theme
competition. Record a short rationale with the prototype or existing design note:

- Task and primary action; facts and material available or missing.
- Chosen idea and why this content benefits from it.
- Type roles, color roles, spacing/density, grid and motion behavior.
- Existing contracts to preserve and the view/state that will test the choice.

For a service page, the primary action may be booking an available appointment;
for an operations screen, it may be resolving one failed job without losing its
queue context. Let those jobs determine the order and forms of content. Do not
force app screens into a marketing hero, three feature cards and a signup footer.
Nor should a table become cards when scanning and comparison require aligned rows.

Use one salient idea grounded in the subject: for example, an editable route map
for a route planner, or clear availability and booking controls for a workshop.
Ask whether substituting another product's name would leave every design decision
unchanged. If so, strengthen the content and hierarchy rather than adding ornament.
Novelty is useful only when it improves comprehension, identity or task completion.

For a supplied colour reference or an unbranded palette decision, use the
[semantic-colour method](colour-palettes.md) to separate confirmed labels from
role proposals, unknowns and actual contrast evidence. Keep existing target tokens
unless their change is in scope; a swatch collection is not a complete UI theme.

## Turn the direction into a coherent system

Reuse the project's tokens and components. If none exist, define a small set of
semantic color, typography and spacing roles; do not create competing global
token files. Carry the same roles across routes. Vary composition with content,
not the brand palette on each page. Choose readable line lengths and a clear
type hierarchy; preserve the project's dense or spacious task requirements.

Give groups an explicit relationship through alignment, spacing, type or a
surface. Remove nested boxes, redundant labels and competing actions where they
obscure that relationship. Gradients, serif headings, uppercase labels and cards
are design choices, not universal defects: assess their purpose and readability.
Do not impose fixed section counts, word budgets or a favorite font on every app.

Inspect representative real content at narrow and wide sizes, including long
labels. Fix the overflow's owner; hiding page overflow can conceal unreachable
controls. Use flexible grid/flex tracks and deliberate table scrolling where
needed. Respect reduced motion and preserve essential content without decorative
animation. Avoid broad transitions and layout-shifting state feedback. Keep
focus, errors and progress immediately understandable.

Render one representative slice early when it can settle the direction cheaply:
the primary task area and an important failure/empty state, or the opening of a
marketing page. Inspect it before multiplying the pattern across screens. Use the
[prototype method](prototypes.md) for a usable HTML/app/native preview and its
storage/lifetime; no mandatory hero review or separate agent is implied.

For consequential concept comparisons, keep the same task/material and explain how
each concept changes hierarchy, typography and interaction. Render the primary
path and relevant failure state with fonts ready at the intended viewport; record
critique → revision → targeted recheck. These are selective Orbyn review choices,
not a fixed three-concept ritual, Apple-font prescription or universal card ban.
Submitted feedback and durable design decisions use [review packages](review-packages.md).
Reviewed inspiration: [Tobi's design-process article](https://x.com/tobiadonadon_/status/2106430529113301163),
read in the source research on 30 October 2026. No underlying skill implementation,
license or claimed results were verified; no article/skill text or assets imported.
Existing Hallmark adaptation notices remain applicable.

## Typefaces and loading

Choose type for the content, not from a favourite list. Shortlist two or three faces
in the class the idea calls for and judge them on the real headline set on the page,
by shape and colour; a name, reputation or subject association is not a reason. A
face every first answer reaches for (generic UI sans, default serif) is fine when the
project already uses it or the user asked; otherwise state why it fits. Confirm the
licence before using a non-free face; a font file keeps its own licence.

- One display and one body face, or one family; an extra face carries one role, such
  as a wordmark. A wordmark set in the plain body weight reads as un-branded unless
  the body voice is the brand.
- Load only the weights used, with `font-display: swap`, preconnect to the host, and a
  metric-matched fallback (`size-adjust` and the ascent/descent/line-gap overrides) so
  the swap does not reflow the fold. Prefer one variable font to several statics.
- Set `font-synthesis: none` and load the real italic or bold a heading uses.
- Inspect the page with fonts ready, as in the concept comparison below.

## Check a page composition

For a marketing or content page, scroll one screen at a time: each screen needs one
idea at a size that carries it. A screen holding only a heading and a line wants a
bigger visual, a statement, or a merge with its neighbour.

- Fix the container width and gutters once; align section edges to that grid.
- Section heads clearly outrank item titles, and body text stays at a readable size.
  An undersized heading is a common reason a page looks unfinished.
- Space follows mass: a large gap frames a large section and leaves a hole under a
  small one. Fix an empty-looking page with a bigger visual or fuller section, not a
  smaller gap.
- Do not repeat one skeleton (head then block) in more than two neighbours; alternate
  dense sections with quiet ones; end on what the visitor came to do.
- Narrow widths stack in reading order; visuals keep aspect ratio; only a named rail
  or table scrolls sideways.
- Squint with the words blurred: each section still has a shape.

## Check an app screen

A working screen is judged on familiarity, not on marketing composition.

- Borrow a theme's palette, faces and radius, not its layout. Use the accent for the
  primary action and the current selection; a second neutral carries panels.
- Keep the project's shell. Add a sidebar only for many destinations, and prefer
  inline editing or disclosure before a modal.
- Density is a design choice: tables before cards for comparison, control heights
  consistent with a comfortable hit target.
- Every region that loads data shows loading, empty, error and full states; draw the
  states the logic has and list the rest for the owner.
- Filters, tabs and pagination live in the URL; a destructive action is undone or
  confirmed. Motion marks state change, not decoration.
- A single component needs every interactive state (default, hover, focus-visible,
  active, disabled, loading, error, success) rendered in a labelled preview.
- A framework page renders through its dev server; say when the render check did not run.

## Separate defects from taste

Review in this order and name the evidence for each finding:

| Finding | Treatment |
| --- | --- |
| Broken task, inaccessible action, lost data, misleading claim or permission violation | Resolve within scope or report as an explicit acceptance blocker |
| Weak hierarchy, repeated composition, excessive chrome or inappropriate density | Explain the task/content harm and propose a concrete adjustment; project intent may justify the current choice |
| Optional craft detail such as spacing rhythm or decoration | Improve proportionally; do not hold delivery for an endless aesthetic sweep |

Use the existing [design rules](design-rules.md) for accessibility and acceptance.
A linter or screenshot inventory cannot judge task usability or brand fit. Match
claims to inspected pixels, exercised interactions and actual backend effects.
An independent reviewer, when requested and supported, gets the source identity,
brief, preserved contracts and captures/routes; distinguish its findings from
the builder's own review. Return the chosen direction, working preview, evidence,
open findings and missing material without claiming user acceptance.
