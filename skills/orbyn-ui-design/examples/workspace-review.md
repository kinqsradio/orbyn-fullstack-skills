# Synthetic collection-to-review redesign

This is a worked policy example, not a shipped screen or an executed UI test.
A person needs to find a failed export, correct its destination and return to the
queue without losing the filter. Existing brand, permissions and custom view stay.

**Before:** the queue has a full summary card per export, nested metadata cards,
a permanently open notification pane and a detail drawer that clears the filter.
The header fits, but little useful queue remains beside both panels.

**Chosen composition:** persistent labeled navigation; collection toolbar and
aligned export rows showing name, outcome and next action. Open detail beside the
queue only when there is useful space. Context/notifications open deliberately,
respecting a pinned user choice. Full summaries remain in detail. At narrow pane
width, switch to detail with a clear Back destination; preserve filter, scroll,
selection and unsaved destination. Existing semantic roles carry both layouts.

**Acceptance plan / receipt shape:**

| Journey | Expected observation | Evidence needed, not claimed here |
| --- | --- | --- |
| Find | Active filter and recognizable failed export with distinct source identity | Before/after actual queue on comparable fixture/viewport; inspect hierarchy |
| Act | Open export, change destination under existing authority | Exercised route/control; actual effect receipt if integration is in scope |
| Cancel/return | Cancel edit returns to the same filtered row and scroll without applying it | Navigation, draft policy and focus check |
| Fail/recover | Save failure keeps draft; retry reconciles unknown write before another submission | Failure fixture/test plus actual UI recovery when authorized |
| Partial/waiting | Retained artifact and missing step visible, relevant source/review reachable | Result fixture tied to domain state; no run-ended success substitute |
| Narrow | Context becomes a switched view; Back restores queue and focus | Relevant constrained layout and keyboard journey, not a full-product matrix |

Record candidate/build, route, content/viewport/panel comparability, actual checks
and limits in the existing change note. A before-state source description alone
cannot substantiate a visible before/after improvement. This example requires no
new screenshot tracker, telemetry, model calls or consumer edits. A future test
must report missing rendered/native/backend evidence rather than mark this plan
as passed. For a tiny icon-label fix, inspect that control and reuse relevant
existing evidence instead of repeating this entire scenario.
