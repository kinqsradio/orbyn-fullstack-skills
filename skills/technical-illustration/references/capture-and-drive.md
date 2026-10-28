# Capture and drive a permitted local figure

Use only a trusted, authorized artifact and existing browser executable. The
maintained scripts use native CDP WebSocket support under Node and a fresh owned
Chrome profile. They do not download a browser, widen sandbox/file-access policy
or change global settings. A denied browser is a blocker, not permission to bypass
it. Supplied JS/actions can execute code; inspect them before a run.

## Select inputs and effects

Resolve the exact built page/candidate, viewport/DPR, theme, reduced-motion setting,
fonts, expected readout and selected figure. Choose an output directory outside
Git or owned by the consumer. Set CHROME_PATH to an existing permitted executable
when discovery is ambiguous. Record actual Node/Chrome/OS versions and command.
Run `node scripts/capture.mjs --help` or `node scripts/drive.mjs --help` from the
bundled support root to inspect exact maintained options before use.

A minimal drive action list can wait for a semantic predicate, send a native key,
read actual state and save a selected screenshot. Use an actions JSON file for
expressions rather than fragile shell quoting. Validate all actions, selectors,
finite dimensions and output ownership before browser effects. Missing required
selectors must fail; selecting body as a silent fallback cannot qualify that part.

## Distinguish time and input

The `slow` action changes RAF/performance sampling, not wall timers. Use `until`
for actual semantic readiness and retain timeout/errors. The driver sends CDP
keyboard/pointer input; a page eval that dispatches an event is a different surface.
Capture after the relevant mount/layout/phase, not merely after a fixed sleep.
Recompute bounds for moving targets and each timed screenshot; stale crops can
hide the part being checked. Scope the readout to the selected figure.

Console errors/warnings, runtime exceptions, rejected async evaluation, navigation
failure and load timeout are failures in the maintained capture/drive contract.
A screenshot may have been written before failure: retain it as failed evidence,
not a qualified artifact. Record command exit and actual image/readout, not just
"saved" output. The process closes only its owned Chrome, waits for termination
and then removes its profile. If termination is unknown, retain the profile/blocker.

## Inspect and hand off

Use clean rest/active/reversal frames, theme/reduced-motion and a planted bad
readout/missing-selector/console-error control. Open the actual screenshots and
check labels, contrast, clipping, geometry and readout correspondence. A successful
capture is not proof of full geometry, browser accessibility, real GPU or all
platforms. Retain first failures, exact inputs and limitations. The Node helpers
operate locally; they do not publish, access private accounts or authorize a
browser tool that the host otherwise forbids.
