# Make a UI decision previewable

Use for a requested prototype, mockup or human preview, or when a bounded
interaction experiment resolves a real design uncertainty. State the person's
task, target surface, relevant states and decision to make. A requested preview
ends with an accessible artifact and opening instructions, not only a description
or source code block. Preserve the consuming product's tokens and vocabulary.

When the open question is visual direction, use the
[direction method](visual-direction.md) to choose content, hierarchy and a
representative slice before extending it. A polished mockup still needs an
explicit path into the real component and backend contract.

Choose rigor from the decision: visual exploration for layout/content, interactive
behavior for task completion/recovery, and critical-property verification only
when the risk warrants it or it is requested. Use
[behavior preview](behavior-preview.md) to connect state/rule IDs, deterministic
scenarios, source and checks. Use [statecharts](../../architect/references/statecharts.md)
when a lifecycle or concurrent actors need an explanation. A simple visual change
does not require a formal model.

## Make the first view useful

Start with a readable primary task, its current state and one clear next action.
Choose the amount of context for the decision: a task flow benefits from a small
number of meaningful stages; a comparison may need aligned rows. Do not expose a
whole catalog, dependency graph or reviewer matrix as the default product view
when the person needs to complete one task. Keep deeper context reachable through
named details, a focused view or a separate reference. Essential consequences,
permissions and recovery controls stay visible beside the action.

Carry the chosen type, spacing and color roles across the preview using the
target's existing design direction. A liked example can inform a scoped new
direction, but does not establish a universal palette, card layout or stage count.
Separate product controls from optional scenario controls. Check the opening view
at its actual size: fitting every node or avoiding overflow is insufficient if
the person must zoom to read ordinary content or cannot identify the next action.

The [focus-session example](../examples/focus-session.md) provides a portable
interactive slice, recovery scenario and implementation handoff. Its synthetic
style and in-memory effects are explicitly limited to the example.

## Choose the evidence surface before building

Use the request and known target to identify what the human needs to inspect:
a component fixture, behavior in a native container, or the actual application/
extension with its relevant real adapters. “On the app” or “in the extension”
selects that actual surface; do not silently substitute a standalone fixture or
ask the human to choose again when the intent is already clear. If required access,
runner or adapters are unavailable, state the blocker before investing in the
wrong harness. Continue only the useful authorized slice, explicitly labelled.

Before UI actions/capture, identify the actual loaded candidate, window/route,
container and relevant adapter/data path using available source/build/runtime
evidence. A native window containing mock controls proves container rendering,
not integration with the application's extension APIs, storage or backend. A
fixture may test real components and still miss host lifecycle/adapter behavior.
Use synthetic data through the intended adapters when appropriate; actual-app
intent does not authorize production data, account access or deployment. Reuse
prior evidence when candidate, surface, adapters and changed contract still match;
do not launch another app just to produce a fresh screenshot.

## Choose the smallest useful surface

| Context | Deliverable |
| --- | --- |
| Component appearance or isolated state | Existing story/fixture using actual components; simulated adapters remain labelled |
| Native container behavior | Existing native preview/emulator/device route; identify host and mocked versus real adapters |
| Actual application/extension flow | The intended app/window/build with the relevant real adapter path; a fixture in a native shell is insufficient |
| Early web interaction with no app harness | Self-contained HTML/CSS/JS with local assets and synthetic data; no framework installation is required |
| Native-specific interaction | Existing native preview/emulator/device path; a web approximation may explore layout but must be labelled and cannot prove native input/navigation |
| Explanatory diagram or comparison | Host-supported inline visual or standalone artifact; do not call it the implemented product |

Check the repository first; do not default every product to React or React Native.
Do not invent a framework route, host embedding API or preview URL. A plain HTML
file can open directly if self-contained. Modules, fetch or routing may require
an existing local server; use the project's supported runner, or a narrowly scoped
loopback static server for a standalone artifact. The agent starts and verifies
it when available and authorized rather than assigning routine setup to the human.
Do not publish, expose the server on all interfaces or access real accounts merely
to make a preview available. If a browser/tool is blocked, retain the file and
report the precise unverified interaction; do not bypass the restriction.

## Make the interaction honest

Build the relevant path through initial, loading, empty, populated, error, retry
and success states; include only states material to the question. Use visible demo
controls or fixtures for deterministic failure/latency and reset. Label synthetic
data and simulated persistence/API actions. A disabled decorative button is not a
working interaction. Never imply a mock saved real data, granted permission or
sent a message. Keep production secrets, analytics and remote CDN dependencies out
of a standalone preview unless specifically required and authorized.

Preserve drafts, target identity, cancellation and focus. Use semantic buttons,
labels, status/error announcements and visible keyboard focus. Check narrow panes
and enlarged text with realistic long content. A modal must manage focus and Escape;
use a simpler inline state when a modal adds no useful decision. Reuse
[async-state guidance](async-state.md) for request identity and unknown save outcomes.

## Human handoff and storage

Use the project's artifact convention; otherwise keep disposable files under
ignored `output/<task>/preview/` and captures under `output/<task>/evidence/`.
Follow [artifact lifecycle](../../orbyn-workflow/references/artifact-lifecycle.md)
for retention, servers and cleanup. Do not place a one-off mockup inside the public
skill catalog, the app's production routes or an expiring temp directory without
an explicit reason. Accepted examples/components have their normal tracked owner.

Return a clickable actual file or verified local route, the startup/lifetime state,
what to try (for example edit → fail → retry → reset), and what is simulated.
Use the host's supported open/preview tool when available. A file-opening tool may
show source instead of rendered HTML; inspect the result before calling it a visual
preview. If no renderer is available, say “artifact created; rendering unverified”
and give the artifact and exact existing launch entrypoint. Do not manufacture a
screenshot or claim a user has reviewed the result.

For a stateful review, provide a compact package: actual preview, editable chart
and rendered chart when useful, scenario/expected-result table, simulation labels,
source/model identity and unresolved decisions. State rendering, exercised
interaction, bounded model result and real-code integration separately. Keep the
package together through workspace moves; a local URL is only a live entrypoint,
not the preserved artifact. Do not require extra records for a small visual edit.

## Inspect and promote deliberately

Open the rendered artifact when authorized. Exercise the changed success and
recovery path, keyboard navigation and relevant narrow layout. Record artifact or
source identity, viewport, actions and observations; a screenshot alone cannot
prove draft retention or an API effect. Automated checks complement interaction
inspection; neither proves complete accessibility or representative-user usability.
Keep agent walkthroughs separate from research with actual participants.

If implementation is requested, transfer the selected flow into the real frontend
and connect it to backend/domain contracts. Specify data/error/permission states,
remove demo-only actions, test the real integration and inspect the resulting UI.
Do not ship a second mock app or mark the feature complete because its HTML demo
looks correct. Retire the prototype only after its review purpose and evidence
retention are satisfied; keep the human's pending preview available.

Primary background, reviewed 25 October 2026:
[GOV.UK prototyping](https://design-system.service.gov.uk/get-started/prototyping/),
[MDN local testing](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Tools_and_setup/set_up_a_local_testing_server),
and [W3C preliminary accessibility checks](https://www.w3.org/WAI/test-evaluate/preliminary/).
This independently written method imports no framework, assets or visual identity.

Use [technical illustration](../../technical-illustration/SKILL.md) when the output
is a model-driven explanatory mechanism with coherent geometry/readouts and
inspected SVG/React/print or conditional GPU paths. Ordinary app previews stay here.
