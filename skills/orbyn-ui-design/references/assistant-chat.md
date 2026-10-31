# Assistant chat surfaces

Use when building or revising an assistant conversation, composer or message-part
renderer. Start with the consuming product's components and existing/planned
semantic colours, typography and interaction patterns. Do not adopt a reference
library's theme, branding, cloud service, provider or runtime by implication.
For a normal comments list or save form use the existing UI methods instead.

## Resolve the actual runtime boundary

Trace the current thread → selected message branch → ordered content parts →
renderer and composer → supported runtime action. Name the owner of canonical
messages, branch selection, run state, attachments and persisted history before
adding components. Keep focus, expanded details, scroll intent and unsubmitted
composer drafts local where appropriate; do not maintain a second message store
that continually reconciles with the runtime. External stores and local runtimes
need their own supported adapter contract, not an assumed interchangeable API.

Ask the actual runtime which actions are supported. Show edit, retry, branch,
cancel and attachment controls only with their real semantics and current
availability. An edit may create a branch; retry may regenerate an answer or
reconcile an existing operation. Do not treat either as an unrestricted repeat
of tool effects. A visible stop control requests cancellation; it does not prove
rollback or completion. Use [streaming interactions](../../orbyn-ai-application/references/streaming-interactions.md)
for leases, partial output, terminal witnesses, history and supported pending
resume; [tool effects](../../orbyn-ai-application/references/tool-effects.md)
retains authority and receipt ownership.

## Build a stable message projection

Use runtime-issued message and part identities rather than array positions or
rendered text for component keys. Separate human-readable text, attachments,
source citations, tool state and unsupported parts. Register trusted renderers
and validate the supported part/version and required props before rendering.
Unknown parts need a visible non-executable fallback that does not erase the
rest of the answer. Do not turn streamed component names, HTML or URLs into
executable code, arbitrary resource loads or handlers.

When the product needs tool status, an approval, a diff, an artifact or citations,
inspect the selected version's relevant component catalog and connect that part
to its actual data/permission owner. Compose the smallest useful subset; do not
copy a catalog wholesale or make a generic chat shell mandatory for every app.

Treat model text and imported history as untrusted content. Use the consuming
renderer’s sanitization and allowed-link/media policy. A known tool renderer may
show a proposal/result without granting authority to execute it. Collapsed debug
panels must not expose hidden reasoning, private arguments or credentials.
Keep history passive; render status from supported current state rather than
inferring success from displayed text or an idle connection.

## Preserve the composer across asynchronous work

Keep drafts scoped to their account/thread; define whether switching threads
preserves or deliberately discards them. Fence late acknowledgements and
attachment callbacks after scope changes. Snapshot a submission, fence duplicate
submits, and clear only the acknowledged snapshot. Newer typing must survive an
older acknowledgement; a known failed send retains the draft and attachments.
An unknown send result needs reconciliation, not an automatic second send.

Distinguish local file selection, upload, ready attachment and submitted message.
Do not clear files merely because text was queued. Check the actual accepted
size/type/count and accessible removal/error paths at the attachment owner;
a file extension or a preview thumbnail is not a validation boundary.
For Enter-to-send, preserve multiline input, Shift+Enter and IME composition.
Keep a labelled submit button and native form semantics where applicable.

## Respect reading and focus intent

Follow new content while the person is at the end. When they scroll up, preserve
their reading position and offer a labelled jump-to-latest control. Preserve the
visible anchor when older history is prepended or message heights change; use
the actual virtualization/measurement owner. An unconditional scroll-to-bottom
on every token destroys reading intent. Keyboard selection/focus must not jump
with each delta, renderer update or thread switch.

Group accessible message content with meaningful author/role labels, readable
order and distinct pending/error states. Announce useful status changes without
re-announcing the whole transcript on every token. Label icon actions, preserve
keyboard reachability and focus visibility, and test the changed keyboard/screen
reader behavior in the consuming product. A DOM attribute or contrast result is
not full assistive-technology qualification.

## Compose a readable conversation

Choose a readable content column for the task and available space, using the
product's typography, spacing, radius, density and layout tokens as well as colour.
Distinguish author roles and content parts through a clear type/spacing hierarchy.
Keep secondary message actions reachable by keyboard and touch without controls
jumping on every token. Let the composer and attachment area grow without hiding
the transcript or its latest controls, including with the mobile keyboard open.
Distinguish new conversation, history loading, running, stopped and error states;
a blank transcript or an idle connection cannot explain all of them. Add an
optional conversation rail only when it fits the product's navigation and narrow
layout. These are composition decisions, not a fixed width or copied theme.

## Map the product's tokens and verify useful states

Map page/panel, body/muted text, action/action label, focus, borders and status
roles to the target design system. Keep ownership/origin explicit for planned
roles. Use [semantic colour](colour-palettes.md) for actual contextual contrast,
theme and non-colour cues; do not replace target tokens with the reference demo.
Keep narrow-width composer/actions operable with zoom and dynamic text.

The original [assistant-chat teaching fixture](../examples/assistant-chat/README.md)
exercises draft acknowledgements, duplicate-send fencing, part fallback and scroll
intent without an SDK/provider. Its browser view accepts a deliberately limited
semantic-token input; illustrative defaults are not approved target colours.

Choose adverse and legitimate controls for the actual change: typing during send,
send failure, IME, late account/thread acknowledgement, unsupported part, reading
older content during updates, jump-to-latest, unavailable runtime actions and
current-theme focus/error cues. Report reducer/helper, browser, assistive-tech,
SDK and actual application evidence separately. Do not claim a fixture qualifies
durable history, a real upload, production authentication or an upstream runtime.

## Conditional assistant-ui adoption recipe

When a consuming React product actually chooses assistant-ui, verify its current
installed or selected release tuple, React peer requirements and adapter APIs.
The reviewed source package versions are not proof of the current published
release or compatibility with that product. Keep the existing store/runtime as
the canonical owner and select one supported adapter; do not introduce a second
message database just to render the primitives.

Connect the selected runtime provider and the minimum thread/message/composer
primitives through the product's component owners. Map semantic roles and slots
to its existing/planned tokens and accessible controls. Wire only supported
history, attachment, branch and action adapters; verify their pending, read-only,
error, cancellation and callback-lifetime behavior. Test the changed ownership
boundary and actual rendered flow at the product's supported widths/themes.
For non-React products use their platform-native equivalent rather than adding
React merely to reuse a reference. The original fixture is a teaching aid, not a
mandatory runtime replacement. Normal implementation authority may cover scoped
reviewed dependencies; this library task itself installs none. CLI initialization,
Cloud/provider services and unrelated settings do not follow from this recipe.

When edits/cancellation replace an input, restore focus only to the correct
current thread/composer and only if focus was lost within that owned interaction.
Do not steal focus from another control or conversation. Honor read-only state
in keyboard shortcuts, pasted files and action handlers, not only button styling.
Choose mobile/touch Enter behavior with the actual platform's conventions.
Viewport identity follows the actual product thread key and delivery generation,
including A→B→A navigation; a repeated route/name cannot revive stale callbacks.

## Pinned research and attribution

Independently authored guidance informed by
[assistant-ui at ff654d8](https://github.com/assistant-ui/assistant-ui/tree/ff654d8156680b839774296ef644b57ab1078425)
(Agentbase AI, MIT). Selected runtime architecture, composer, viewport, typed-part,
external-store, attachment and branch sources were reviewed; no upstream code,
styles, assets, policy text or runtime are bundled. Its source manifests identify
React package 0.15.32 and core 0.3.32; no published release or consumer compatibility
claim follows. Upstream tests were read as evidence of intended mechanisms, not
executed. This offline method and original fixture do not require the links.
