# Accessibility audit

Use for a focused accessibility review or fix of controls, forms, dialogs and
hover-only or hidden content. Targets and thresholds are in the
[WCAG 2.2 checklist](design-rules.md#wcag-22-checklist); focus ownership and
modal rules are in [UX rules](ux-rules.md#focused-editors-and-modal-ownership) and
[design rules](design-rules.md#layout-panels-and-overlays). This page adds the
order of work. Report each finding as the exact snippet, the failure in one
sentence and a small fix.

## Boundaries first

- Minimal, targeted changes. Do not refactor unrelated code or rewrite the screen.
- Native HTML before ARIA. No `role` or `aria-*` where `button`, `a`, `input`,
  `label`, `ul` or `dialog` already carries the meaning.
- No UI library migration. Fix within the stack; for a complex widget (menu,
  dialog, combobox) prefer the project's accessible primitive over new custom
  behavior.

## Order of work

Fix earlier items first.

1. **Accessible names (critical).** Every control, input, select and textarea has
   a name. Icon-only buttons get `aria-label` or `aria-labelledby`; decorative
   icons get `aria-hidden`. No "click here" links.
2. **Keyboard (critical).** No `div`/`span` buttons without full keyboard support;
   use the native element. Everything is reachable by Tab, focus is visible, no
   `tabindex` above 0, Escape closes overlays.
3. **Focus and dialogs (critical).** Move focus in on open, contain it while open,
   return it to the trigger on close, and do not scroll the page unexpectedly.
4. **Semantics (high).** Lists use `ul`/`ol` with `li`, no skipped heading levels,
   `th` for table headers. A role that is used has its required attributes.
5. **Forms and errors (high).** Link errors and helper text with
   `aria-describedby`, set `aria-invalid` on invalid fields, announce required
   fields, and explain why a submit is disabled.
6. **Announcements (medium-high).** Critical errors use a live region; loading
   uses `aria-busy` or status text; a toast is never the only carrier of critical
   information; expanders use `aria-expanded` and `aria-controls`.
7. **Contrast and states (medium).** Enough contrast for text and icons. Hover-only
   behavior has a keyboard equivalent. Disabled state does not rely on colour
   alone. Never remove an outline without a visible replacement.
8. **Media and motion (low-medium).** Meaningful or empty `alt`, captions for
   speech, no autoplay with sound, and reduced motion honored for non-essential
   movement ([motion](motion.md)).

## Common fixes

```html
<!-- icon-only button -->
<button aria-label="Close"><svg aria-hidden="true">...</svg></button>
<!-- clickable div -> native button -->
<button type="button" onclick="save()">Save</button>
<!-- error linked to its field -->
<input id="email" aria-invalid="true" aria-describedby="email-err">
<span id="email-err">Enter an address like name@example.com</span>
```
