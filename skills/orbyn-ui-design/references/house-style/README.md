# Orbyn house style

A quiet, monochrome product interface: colour comes from status and content, not
decoration. Three themes, one token set. Adapted from the author's own design system.

## When to use it

- A new application with no design system of its own: start here instead of an
  invented palette.
- A project with its own design system keeps it. Never replace existing tokens with
  these.

## How to apply

1. Load `tokens.css` (generated from `tokens.json`; regenerate with
   `scripts/house_style_css.py`, never edit by hand). Set `data-theme="light"`,
   `"dark"` or `"dim"` on the root element; light is also the default.
2. Map the tokens to the project's styling and refer to them by name. Never
   hard-code a colour. With Tailwind, extend the theme with colour variables, for
   example RGB channels (`--th-text-body: 0 0 0` with `rgb(var(--th-text-body) / <alpha-value>)`)
   converted from the `rgba()` values; plain CSS can use `var(--th-text-body)` directly.
3. Load the fonts from Google Fonts: Geist (400, 500) and JetBrains Mono (400), both
   SIL OFL. No font files are bundled.
4. Take icons from the project's own icon set. Brand and provider logos keep their
   own colours.

## Content fundamentals

- Sentence case, plain and direct: "Deploy", "Add server", "Deployed 3 minutes ago".
  No exclamation marks, no emoji.
- Name the object, not the feature: "api-server", not "your service".
- Statuses are single words: Live, Building, Failed, Paused.
- Empty and error states say what happened and offer the next action
  ("Repository not found" with an Import repository button).
- Amber means the person must act. Work that is progressing (queued, building,
  migrating) is info blue.

## Visual foundations

- **Three themes.** Light, Dark (a pure black page) and Dim (neutral `#101010`
  with lime accents). Every colour is a `--th-*` or `--st-*` token that switches
  with `data-theme`. The shadcn-style names (`background`, `foreground`, `primary`,
  `muted`, `border`, `ring`) are aliases of them.
- **Monochrome ink.** Text is black or white at stepped opacities: `th-text-heading`,
  `title`, `strong`, `body`, `secondary`, `muted`, then `hint` and `ghost`. Muted is
  the lowest step for readable text; hint and ghost are for disabled or
  non-essential text. Strokes and overlays use the `th-on-*` scale (4 to 95%), tinted
  fills use `th-sf-*` (1 to 8%).
- **Inverting primary button.** `th-btn-bg` is near-black on Light and white on Dark
  and Dim. The gradient accent button (`th-btn-accent-*`: violet to ink to blue on
  Light, amber to orange to rose on Dark, flat lime on Dim) is opt-in, for the one
  control that deserves emphasis.
- **Borderless cards.** `th-card-bg` fill, no border at rest (`th-card-bd` is
  transparent), no shadow. Borders (`th-bd-default`) belong to inputs, menus, choice
  rows and dividers.
- **Radius.** 5px checkbox, 8px small buttons, chips and choice rows, 12px buttons,
  inputs and alerts, 16px cards, menus and modals, 20px banners, 24px drawer, full
  for pills, badges and switches.
- **Control height.** Buttons 32, 40 or 48px (36px for icon buttons); inputs and
  select triggers 44px.
- **Type.** Geist at 400 and 500, 14px as the UI default; headings medium or
  semibold, never bold. JetBrains Mono for commands, hosts, IPs and logs. The full
  scale is in `tokens.json`.
- **Status.** Use one set together: `st-*-fg` text on `st-*-bg` with a `st-*-bd`
  border, and `st-*-solid` for dots and bars. Always add a label or icon, so colour is
  never the only signal.
- **Depth.** Only floating layers (menus, selects, tooltips) cast `th-dropdown-shadow`.
  Modals and drawers sit on `th-overlay` with a backdrop blur. Focus is a 2px ring
  offset 2px from the background.
- **Motion.** 150ms for colour changes, 200 to 300ms for menus, modals and drawers.
  Respect reduced motion.

## Limits

- Hand-resolved values: the Light and Dark accent and primary-hover colours were
  resolved from `color-mix()` over the Tailwind v4 palette.
- Not included: component code, previews, icons, a logo and marketing components.
- Adapted from the author's own Openship system, renamed Orbyn. Gellix was replaced by
  Geist and JetBrains Mono for licensing.
