# UI and UX

Read the [UI skill](../../skills/orbyn-ui-design/SKILL.md) for layout and interaction,
and the [content skill](../../skills/orbyn-content-design/SKILL.md) for visible copy.
Use existing shared components and tokens; inspect the current screen before
adding an override. Preserve drafts, selection, focus, permissions and run states.

## Consumer conventions

Find the target project's design and brand guides using the optional
[context map](../../skills/orbyn-setup/references/project-context.md). Read those
guides and current components before choosing palette, type scale, density,
navigation or motion. Keep product-specific rules there so shared skills can be
updated without replacing local decisions.

Use one clear action per outcome, preserve draft/focus/recovery behavior and adapt
to actual pane width. Accessible names, keyboard focus and reachable actions matter
independently of visual style. A document needs room to write; a settings surface
needs a clear route to the setting. Shared token changes alone do not establish
that every layout has been reviewed.

## Scoped visual evidence

When visual verification is authorized, use the project's supported preview
commands and platforms. Orbyn uses web and Expo web previews; other projects use
their actual equivalents. Record the actual URL, source revision,
viewport, zoom, theme and checked states; browser evidence does not establish
native integration behavior. Do not require native builds unless in scope.

Inspect changed flows and concrete risks, not a matrix of unchanged screens.
Independent inspection is optional unless requested; choose the session/subagent
arrangement from [coordination](coordination.md). Builds and DOM dimensions alone
do not establish usable visuals. Keep failed/blocked states and evidence limits.
A blocked browser origin is not permission to retry through another transport.
