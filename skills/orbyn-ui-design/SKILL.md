---
name: orbyn-ui-design
description: "Design, implement, or review product UI and UX across web, desktop, and mobile: task flows, concise copy, responsive layouts, overlays, and AI interactions. Use for visible product flows; not backend-only work."
---

# Orbyn UI and UX Design

Make the target product's task flow easy to scan and operate at real window sizes.
Use the agreed palette and shared components. Compact default text must remain
readable and grow with user accessibility settings.

This skill owns changes to the product UI itself. For social announcement graphics,
product screenshot compositions and feed mockups, use
[social-preview](../social-preview/SKILL.md), with
[social-content](../social-content/SKILL.md) for the post; a promotional mockup is
not an implemented screen.

## Read before designing

- Read the consuming project's instructions and the agreed task scope; preserve
  scope and stage order.
- For product copy and information hierarchy, read
  [orbyn-content-design](../orbyn-content-design/SKILL.md); keep detailed content
  rules there.
- Read [design rules](references/design-rules.md) for typography, layout, copy,
  AI behavior, and the visual acceptance matrix.
- Read [UX rules](references/ux-rules.md) when changing navigation, task steps,
  forms, onboarding, feedback, recovery, or explanatory content.
- Read [research](references/research.md) when choosing or revising a rule. It
  distinguishes accessibility requirements, research guidance, and Orbyn choices.
- Inspect the owning screen and shared controls before adding a local override.
  Resolve the theme/token and component owners from the consuming project's stack
  guide and manifests, and use the paths it already has. Never create paths to fit
  this skill. The [Orbyn example](references/research.md#orbyn-example-token-and-component-owners)
  shows one such mapping.

## Resolve product direction

Read the consuming checkout's design/brand pointers in its optional
[project context](../orbyn-setup/references/project-context.md), then inspect the
actual token and component owners. Preserve its agreed palette, type scale, density,
navigation and motion policy, and keep existing product tokens over a foreign host's
theme or tool APIs. This library supplies no universal blue accent, modal layout or
pixel scale. When a guide is absent, use the existing interface and the user's
brief; record unsettled choices before a broad redesign. Audit-only requests produce
findings without product edits. Keep a small polish to its stated scope.

## Design and implement

1. State the person's main task, starting state, and observable success. Map the
   steps, cancellation, failure, and return path before arranging controls.
2. Use existing text roles, spacing, and controls. Reduce competing headings,
   repeated actions, and explanatory copy before changing font sizes.
3. Adapt to the actual content width: collapse secondary panels, stack forms,
   or use a drawer. Keep every action reachable without squeezing the main task.
4. Preserve data and authority: drafts, selections, permissions, approvals,
   consent, and backend run states must survive visual changes.
5. Cover the supported surfaces affected by the requested change, using their
   platform-appropriate navigation and controls. Apply parity only where the
   product contract requires it; record agreed platform limitations.

Evaluate the complete task from the person's starting state through success,
cancellation and recovery. Resolve trade-offs around that outcome, preserving
accessibility and authority. Use the [experience method](references/principles/experience-first.md)
when a local visual improvement could make the end-to-end task harder.

## Review and deliver

Follow the consuming project's visual-review policy and the changed surface. Read
[visual review](references/visual-review.md) before capturing UI, briefing an
inspector or handing a preview to a person.

- Check the cases relevant to the named risk, then stop. Review density,
  discoverability and task completion as well as containment.
- Fix reproduced problems, request a targeted recheck, and retain failed attempts
  and unverified states.
- If browser permission or export is rejected, report the blocked action and use an
  allowed handoff. Never bypass it through another browser, port, transport or
  indirect export.
- When presenting new or changed UI for human design review, offer or reuse the
  live feedback method in [review packages](references/review-packages.md).
- For a requested prototype or preview, deliver the actual app route/story or a
  self-contained HTML artifact, with a verified link and the states to try. Small
  visual work stays small.

## Read when the task needs it

- Interactive sketch to resolve a design question: [prototyping](references/prototypes.md).
- Unknown platform or accessibility requirements: `orbyn-research`.
- New visual direction, a requested redesign or a design-quality audit:
  [visual direction](references/visual-direction.md).
- Changing an existing UI: [redesign contract](references/redesign-contract.md).
- Substantial workspace composition, collections, editors or review surfaces:
  [workspace composition](references/workspace-composition.md).
- Colour direction, semantic light/dark roles or contrast review:
  [reference palettes and semantic colour](references/colour-palettes.md).
- Validation with people: [user evidence](../orbyn-research/references/user-evidence.md).
- Model-powered behavior: [AI application engineering](../orbyn-ai-application/SKILL.md)
  and [AI experience](references/ux-rules.md#ai-experience).
- Assistant conversation/composer surfaces: [assistant-chat UI](references/assistant-chat.md).
- Fetch/save/search or subscription changes:
  [asynchronous state and recovery](references/async-state.md).
- Stateful flows: [behavior preview](references/behavior-preview.md). Hand lifecycle
  statecharts to `architect` and critical property checks or drift to `tdd`.
- Ordinary transitions/gestures: [motion](references/motion.md) and measured
  [motion performance](references/animation-performance.md).
- Code-driven UI motion and an editable preview:
  [motion composition and inspector](examples/spatial-review/motion/README.md).
- Browser touch/keyboard/viewport: [mobile web](references/mobile-web.md).
- Real schema/data extremes: [stress fixtures](references/stress-fixtures.md).
- Demonstrated Expo/RN screens: [native UI](references/mobile/native-ui.md),
  [navigation](references/mobile/navigation.md),
  [data/lifecycle](references/mobile/data-and-lifecycle.md) or
  [UI-runtime motion](references/mobile/motion.md), only as relevant.
- Positive page identity, fresh structure after navigation, or supplied Figma
  node/assets-to-primitives mapping: [design intake](references/design-intake.md).
- Bidirectional, translated or live-locale interfaces:
  [localization and RTL](references/localization-rtl.md).
- A worked example: [recovering a failed save](examples/failed-save.md) applies a
  consuming project's style and draft/conflict contract without claiming an
  unperformed visual check.
