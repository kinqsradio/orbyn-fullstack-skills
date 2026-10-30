# Compose a workspace around the task

Use for a substantial workspace redesign or when navigation, collections, editors
and context compete for attention. A small control fix keeps the existing shell.
These are adaptable design choices, not an accessibility standard or a prescribed
number of destinations. Preserve the consuming project's brand, saved views,
explicit panel preferences and platform conventions.

## Decide the default before decorating

Name the person's primary task, starting object and observable result. Inspect
realistic content and current routes before choosing the default view. Explain
which information changes the next decision and which can wait. Repeated metadata,
large completed-history groups and full authored briefs need not dominate active
work; keep the complete material reachable without rewriting it.

Keep a coherent shell across related routes: stable navigation, recognizable page
identity, search/create entry points where useful, and a clear return path. Primary
labels should be discoverable; a compact icon rail can be an explicit preference,
with accessible names and a usable way to learn destinations. Keep the category
recognizable when showing a custom companion name, respecting explicit product
preferences; do not invent a fixed menu count.
Search, asking a model and running an action have distinct scope and consequences;
a longer search query must not silently authorize an agent run.

Choose panel defaults deliberately. Notifications, libraries and assistant context
should earn their occupied width through the current task or a user's pinned
preference. A drawer or explicit context toggle often preserves more work space.
Measure the primary content after the actual shell and panels consume width;
collapse or switch secondary panes before squeezing reading, writing or actions.
A panel being technically inside the viewport does not make that composition useful.

## Reuse surface patterns, not identical pages

| Surface | Starting composition | Preserve / check |
| --- | --- | --- |
| Collection | Page identity, compact filter/action toolbar, aligned rows for comparable items; cards only where content benefits | Active/saved view, selection, next action, long names, empty/filter/read-error distinctions; history stays reachable |
| Detail | Object identity and parent/source link, current state, primary action, then relevant sections | Deep links, authored brief, full values, permissions and return to the originating collection |
| Editor | Writing/reading surface first, stable toolbar, optional source/context | Draft, cursor/selection, source identity, independent scroll; failure does not replace the draft |
| Review | Goal and factual outcome, artifact/source links, outstanding decision, relevant checks | Partial/unknown result, version-bound apply authority, retry/cancel/manual continuation; transcripts are optional detail |

Use alignment, spacing and type roles before wrapping each field in another card.
Keep title, decision-changing state and next action prominent; put secondary
metadata in consistent rows or sections. Reuse semantic canvas, navigation,
work-surface, overlay and selected roles from the existing token owner. Selection,
focus, hover and warning need distinguishable meanings, not one accent fill.
[Semantic colour](colour-palettes.md) owns actual contrast and token-role checks.

## Open context beside work without losing it

A contextual link identifies the actual object, source and scope; a related-object
map is different from an account integration. Open beside only when comparison or
reference reading serves the task. Reuse the current object when appropriate;
avoid spawning another duplicate pane at every click. Bound simultaneous panes
according to usable task space, not an arbitrary universal cap.

Keep object identity separate from placement. Moving, hiding or switching a pane
must preserve its draft, scroll, selection and Back destination. Hidden panes yield
focus and shortcuts; closing returns focus to a visible logical target. On narrow
layouts, show one working surface with explicit context/return controls rather
than shrinking the desktop split. Do not send every open pane to a model as implicit
context. [Async ownership](async-state.md) owns stale reads, permissions and saves;
[content outcomes](../../orbyn-content-design/references/outcomes-and-attention.md)
owns visible result language and attention grouping.

## Accept the task, not just the tokens

For a substantial composition change, retain one compact receipt in the existing
change note or PR. Use [the worked example](../examples/workspace-review.md).
No new tracker, giant screenshot matrix or separate approval ceremony is required.

- **Task and choice:** starting state, primary result, why the default composition
  supports it, and what competing chrome was collapsed or retained.
- **Comparable layout:** before/after on the changed route with comparable content,
  viewport and panel state. Identify source/build and loaded route. Inspect the
  actual rendered hierarchy and work space; use captures only when needed to
  convey the visual finding. Mark source-only, prototype and actual-app evidence
  separately; if before evidence is unavailable, say so rather than fabricate it.
- **Journey:** find the item, act, cancel and return, then relevant fail/recover
  paths. Retain drafts, focus/selection and source identity. Include partial or
  waiting outcomes when the changed flow can produce them.
- **Narrow case:** exercise the affected pane transition or constrained layout
  with representative content. Select relevant widths/themes/states under the
  existing [acceptance rules](design-rules.md#acceptance-for-a-changed-feature);
  unrelated screens and excluded native surfaces stay outside the check.
- **Verdict:** name confirmed problems, corrections, checks and unperformed scope.
  Build success, tokens, screenshots or containment alone do not establish visual
  quality, task success, accessibility conformance or measured usability benefit.

Small copy/control changes use the relevant narrow checks and existing evidence;
they do not inherit this whole receipt. Follow [redesign preservation](redesign-contract.md)
for changed contracts and [prototypes](prototypes.md) for the actual evidence surface.

## Reviewed inspiration and limits

Reviewed 30 October 2026 from pinned source/documentation: Macro contributors,
[Macro fb7ca4b](https://github.com/macro-inc/macro/tree/fb7ca4b7c4c10519413e592da81d5e04a44ce977),
including persistent shell, bounded adjacent content, contextual links and semantic
roles; its published task-list image was a composition reference in the upstream
review. Source mechanisms and published imagery do not establish deployed behavior,
accessibility or task performance. Open Duet contributors,
[Open Duet 881de25](https://github.com/Anil-matcha/open-duet/tree/881de25e941bb7c53380ffddb17c39d3d01ad06b),
informed result/recovery questions through source review, without rendered-product
qualification. No source code, assets, branded layout, runtime or upstream skill was
imported. This is independently authored guidance with synthetic examples. Retain
these update/credit pointers and use the [upstream review method](../../orbyn-upstream-review/SKILL.md)
before any later import, including its license and redistribution review. Existing
Hallmark and other adaptation notices remain in their owning references. Established
accessibility criteria remain separately identified in [research](research.md).
