# Create or update DESIGN.md

Use when asked to document a product's design language for people and coding
agents. The file records the system that governs the product, not every value in
the code. Edit only the design document: no product source, dependencies or
config.

## Where it lives

Find the target's existing design document and its exact filename case first (see
[project context](../../orbyn-setup/references/project-context.md)); use
`DESIGN.md`/`design.md` only when none exists. One file per product. If a
repository holds several deployable products and the request does not name one,
ask before writing. Public-URL mode produces a draft in the workspace, labelled
reconstructed.

## Pick the mode

- **Repository** (preferred, whenever source exists): source can establish values,
  token names, component owners and documented rationale.
- **Public URL, no source**: needs a rendered browser. Inspect DOM, computed styles
  and loaded stylesheets at desktop and mobile widths, on the page plus up to three
  same-origin templates. It can establish observable patterns and computed values
  only, never token names, ownership or intent. Without rendered inspection, ask
  for screenshots or source; never build the file from copy or markup alone.

## Collect evidence

Record per candidate: role, value, source, scope, recurrence.

Repository order: existing design document and guidance, tokens/themes/globals,
shared primitives and variants, representative routes, local styles. A source
counts only if the product imports, inherits or renders it; skip proposals,
migrations, examples, generated output and legacy code.

URL mode: keep a ledger of page, viewport, element role, computed value and the
matching loaded declaration. Keep a value when the computed value matches a
loaded declaration, or the same value recurs for the same role across samples.
Otherwise omit it. Use a custom-property name only if its declaration and use are
both visible; invent no aliases.

## What belongs

- Exact values for named shared tokens and roles, in the frontmatter.
- Intent and application rules the sources support, in prose.
- Product character only from stated intent or a design reference. In URL mode
  state observable purpose and presentation only.
- A "don't" only when a governing source states the prohibition.

## What does not

- Utility classes, repeated literals or component values turned into scales.
- One page's styling presented as a product rule.
- Invented personality, audience or emotional rationale.
- Citations, audit notes, rejected candidates or open questions; report those
  in chat.
- Token inventories, component config or source syntax in prose.
- Advice that changes nothing ("be polished").

## Shape

- Frontmatter: `version`, `name`, `description`; add `colors`, `typography`,
  `rounded`, `spacing`, `components` only when a governing source defines that
  system. References look like `{colors.primary}`.
- Token groups are mappings. Typography entries are named scales holding
  `fontFamily`, `fontSize`, `lineHeight`; never `sans: Inter`. One source radius
  variable becomes `rounded.base`; derive no steps.
- Prose starts with an Overview, then only the sections that have evidence, in
  this order: Colors, Themes, Typography, Layout, Elevation and Depth, Shapes,
  Components, Do's and Don'ts. Alternate-theme values go in a Themes table if the
  format cannot express modes.
- Update, do not overwrite: keep accepted decisions unless the user or current
  governing evidence replaces them.

Pick the token naming that fits the project's export target (Tailwind 4, Tailwind
3 or neutral design tokens).

## Validate

Run the format's linter and one export for the chosen target (the reference tool
is `npx @google/design.md lint` and `... export --format <target>`), then check:

- Every populated frontmatter category appears in the export; a missing category
  is a failure even with exit 0.
- When updating, diff against the previous file and restore any accepted
  decision that disappeared.
- Create no export files.
- Do not show the draft before it passes. If a limit of the exporter drops
  supported information, keep the information and report the limit.

Report: mode, product or URL, file written, sources used, what was omitted and
why, lint and export results.
