# Orbyn UX rules

Apply these to the changed flow within the agreed task scope. They cover
behavior and information architecture as well as appearance. Research sources
and the distinction between external guidance and local choices are in
[research](research.md).

## Task and navigation

- Define a concrete outcome: change a preference, connect a provider, write a
  document, review a proposal, or schedule work. Avoid designing a page around
  everything the implementation can do.
- Map entry → action → feedback → result, plus cancel, failure, and return. Keep
  names and locations stable across clients; adapt presentation to the platform.
- Give frequent tasks a direct, visible path. Menus hold rare management actions;
  primary actions must not require guessing an icon or reading a tutorial.
- Preserve the current document/chat, draft, selected category, and relevant
  scroll position when opening and closing Settings or temporary panels.
- Search must lead to the actual setting, reveal its containing section, and
  leave a clear route back. Empty results offer a useful next step.
- Reduce duplicate actions and unnecessary steps. Keep steps that protect an
  informed decision, a destructive action, or a meaningful review boundary.

## Bind an action to its invocation target

For a shared action exposed through toolbar, shortcut or context menu, resolve the
object IDs, supported selection, originating pane and operation identity when it
is invoked. Use that entrypoint's actual target semantics, not an assumed global
active object. Reuse existing action/hooks and the [shared control contract](design-rules.md#shared-control-behavior-across-supported-renderings);
no command registry or new action framework is required.

Synthetic example: a context menu opens on task A while another pane has task B
active. “Archive task” targets A. If focus moves to B while the request awaits,
neither the write arguments nor the eventual result may silently retarget B.
Keep the receipt associated with A; update A's owned state or retain its status
when no longer visible. Apply a visible update only to the matching current
object/request generation. Do not discard a confirmed effect merely because its
original view unmounted, or put its success/error under a replacement object.

Exercise equivalent supported toolbar, shortcut and context-menu paths using
explicit targets. A shortcut may legitimately use the focused pane while a menu
uses its clicked object; agreement means consistent action/authority for the same
resolved target, not forcing all entrypoints to use the global selection. For
unsupported multi-selection, disable with a discoverable reason or reject explicitly;
never silently operate on only the first item. If selection changes after a menu
opens, retain/revalidate its original target or invalidate the menu under the actual
product contract, rather than silently taking a new selection at execution time.

Check the inactive-target case, a focus/pane change during await, denied/stale target
and a legitimate current action. UI preconditions and enabled controls are not
permission: current model/service authority and freshness still govern the effect.
[Async ownership](async-state.md) owns replacement/unmount fencing and cleanup;
[tool/backend effects](../../orbyn-ai-application/references/tool-effects.md) owns
authorization and unknown committed outcomes. These are proposed target checks,
not evidence that a product's actions have already passed them.

## Copy and progressive disclosure

- Show the label, current value/state, and relevant action. Add one short helper
  sentence only if it answers a likely question or prevents a mistake.
- Optional explanations belong in a specifically named disclosure, such as
  "How connections work". A help link is separate from the field's hint text.
- Essential consent, sharing scope, consequences, and recovery instructions stay
  near their action. Do not hide them simply to meet a copy or density target.
- Remove repeated benefit statements, welcome essays, and lists of example apps
  from routine settings. Empty states need a short fact and a next action.
- Use product distinctions consistently: ChatGPT provider connections supply
  inference; Connected agents/MCP grant access to Orbyn. Background and Overnight
  are separate work surfaces. Avoid a shared ambiguous "Connect AI" action.

## Focused editors and modal ownership

- The active editor owns keyboard focus and restores its connected opener on close.
  Tab cycles through visible controls; Escape closes only the top layer.
- Floating selectors/date pickers must declare their editor owner. Their focus and
  Escape handling remain local; never trap a picker back into its parent form.
- Pending saves prevent duplicate submission and accidental dismissal. Keep drafts
  mounted behind optional sections; reveal invalid hidden fields before focusing them.
- Use `useModalFocus` for custom web editor overlays where appropriate. Native
  dialogs require compatible portal placement; do not substitute them blindly.
- Links, chat handoffs and other-pane navigation can also leave an unsaved editor.
  Apply its departure guard before handing over; a confirmed write can hand off
  its saved receipt without presenting another creation action.


## Forms, state, and recovery

- Prefer safe defaults and suitable input types; keep labels visible. Validate
  actionable field errors next to the field and preserve entered values.
- Distinguish invalid input from unavailable service, revoked access, missing
  permission, or provider outage. Explain the relevant next action briefly;
  do not ask a person to edit a correct field to solve a server problem.
- Bind related-resource state to its current document/project identity. On a
  content change, previous results must not appear under the new owner while
  effects or reads settle; distinguish loading/failure from confirmed emptiness.
- Show pending feedback when an action begins, prevent accidental duplicate
  submission, and make the saved/result state observable. A toast alone must not
  conceal a persistent failure or replace the current connection/run status.
- Approval reviews keep recipients, dates and destructive consequences visible.
  Long authored text can use a named disclosure with complete before/after values;
  bound scrolling must remain keyboard reachable. Freeze approval options while
  their write is pending, and retain a confirmed receipt before opening its result.
- A retry retains work and cannot silently change the provider, recipient, model,
  or authority. If the consequence changes, require the appropriate fresh choice.
- Cancel, Back, Close, Undo, and disconnect must have predictable effects. Preserve
  unsaved-change guards and explain irreversible consequences before commitment.
- On mobile, use familiar back navigation, sheets, safe areas, keyboard types,
  and reachable actions. Native input/keyboard checks remain separate from browser
  emulation; parity means equivalent outcomes, not identical screen composition.

## AI experience

- Let people edit or dismiss suggestions and continue manually when AI is wrong
  or unavailable. Existing work must remain accessible after a provider failure.
- Show useful provenance and the actual reason for waiting. Keep uncertain or
  unavailable plan/usage information distinct from a verified zero value.
- Preserve approval, review, cancellation, and ownership boundaries as specified
  in the agreed task requirements. Convenience must not turn a suggestion into an authorized write.
- Keep contextual suggestions in a stable location; do not rearrange primary
  navigation or change settings based on inferred preferences without a choice.

## Acceptance beyond screenshots

For the changed feature, record an outcome, not just an opened screen:

| Check               | Evidence to record                                                             |
| ------------------- | ------------------------------------------------------------------------------ |
| Find and complete   | Starting point, actions, observable result, confusing or duplicate steps       |
| Cancel and return   | Draft/selection retained, correct destination, restored focus where applicable |
| Fail and recover    | Specific error, reachable next action, no work loss or duplicate side effects  |
| Narrow and enlarged | Actual viewport/scale, usable task space, keyboard/overlays, no trapped action |
| Equivalent clients  | Same supported task and authority on web/desktop/mobile; explicit native gaps  |

When independent interaction review is requested, give the assigned inspector a
bounded brief and report destination under the repository coordination policy.
Use plain task goals for exploratory review rather than giving away every click;
give exact steps for a known defect's recheck. Agent walkthroughs are expert QA,
not evidence from representative human participants. Where user testing is done,
record completion, errors, assistance, and time without claiming a universal
usability score. Do not collect new analytics or personal data implicitly.


## Add rows and confirmed receipts

- Before saving a form, account for text still in an Add row (links, invitees,
  alerts, tags). Add it explicitly or explain which unfinished entry to add or
  clear. Never silently leave typed data out of the saved artifact.
- Bind creation/apply receipts to the account and exact proposal or object. Keep
  the receipt before opening its destination or refreshing a list. A failed
  follow-up must say the item was saved and offer the follow-up action; it must
  not invite another creation as if the first write failed.
- A counted preview needs a visible route to all of its content. Label a plain
  text disclosure as text; do not imply it proves rich-format or attachment
  rendering. Sharing destinations must be identifiable before commitment.
