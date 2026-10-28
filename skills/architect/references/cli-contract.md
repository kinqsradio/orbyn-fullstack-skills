# Design and exercise a command interface

Use when designing a CLI or changing its observable behavior, including agent use.
Inspect existing parser, output compatibility and test harness before adding flags.
This is not a requirement to add a CLI to a visual product.

## Input and results

Document noninteractive flags for required inputs; optional wizard behavior must
not hang a headless caller. Fail missing/invalid input before effects with nonzero
status, a specific correction and a real current example. Top-level help locates
commands; subcommand help explains its own options/examples. Keep stdout results
separate from stderr diagnostics, with stable result IDs, status and a documented
machine format where needed. Async accepted/queued differs from completed; return
an operation identity and supported observation route. Document relevant stdin
formats and pipeline behavior rather than implicitly reading a terminal.

A preview/dry-run identifies exact target and effects actually skipped; inspect
file/network/ref effects rather than trusting its label. Confirmation bypass flags
do not grant authority. Preserve logical operation identity for supported retries;
unknown acceptance requires reconciliation before a new write. Follow existing
[effect identity](../../orbyn-backend-design/references/principles/make-operations-idempotent.md).

## Terminal interaction

Reuse the repository's current prompt harness, PTY, Expect or tmux support; do not
install another tool solely to match an example. Start a fresh owned PTY/session
and fixture where independence requires it. Wait for a known prompt/state within
a declared deadline, send one action, then inspect the new state. A sleep or elapsed
timeout is not readiness; do not blindly send the next command after a failed wait.
Retain the transcript and process/exit identity, redacting sensitive input.

Select only relevant arrows, Escape, narrow resize, EOF and Ctrl-C/signal cases.
Resize must actually reach the PTY, not merely crop a screenshot. Verify cancelled
work releases owned handles and effects do not complete late. A noninteractive
parser fix does not require a whole TUI matrix. Stop only owned sessions, never
an attached user's terminal. Use [artifact cleanup](../../orbyn-workflow/references/artifact-lifecycle.md).

For startup/heap/active-handle diagnosis, compare the same command, runtime,
environment and cold/warm fixture; repeat operations and inspect retained roots.
One heap snapshot is not a leak. A PTY fixture proves that fixture's terminal
behavior, not every target CLI or host platform.
