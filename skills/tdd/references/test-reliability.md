# Reliable time, isolation and runner evidence

Use this method when a test's timing, readiness, cleanup, module identity or runner
coverage could hide the behavior being checked. Keep the project's actual test
framework and installed API versions; no Bun/Effect/Playwright mandate follows.

## Define the observation before running

Name the production module/candidate, actual effect and assertion, environment,
clock owner, isolated state and selected runner leg. First make a discriminating
bad control fail for the intended contract, then verify the legitimate case.
A failed setup, zero selected cases, a copied story or a skipped shard cannot
establish a production regression. Preserve first attempts as well as retries.

## Own time and asynchronous work

Record the actual tool-launched executable, not just the parent's PATH. A login
shell can choose a different interpreter. Do not compare timestamps from clocks
without a verified shared domain: older macOS Python monotonic clocks can have
per-process origins. For dependency order prefer a source-bound causal witness,
such as a cooperating locked journal ordinal plus actual tool completion events.
Wall-clock time can jump; diagnostic timestamps alone do not prove causality.

Pass the owning virtual clock and cancellation signal into the code doing the
work, including callbacks, workers and child processes where supported. Register
the waiter before advancing the clock. A frame budget controls rendering steps,
not wall timers, network readiness or the implementation's other clock. State
which live I/O remains uncontrolled; do not label that mixed boundary fully virtual.

Poll with an elapsed deadline and the complete semantic predicate. Include the
last observed state on failure. A timeout rejects an observation; it may leave
the body running. Cancel, await/join termination and close owned connections
before removing fixture files. Keep an uncooperative worker's resource and blocker
visible rather than delete its state while it can still write.

Example: a delayed writer should check the injected abort signal before commit.
The timeout test aborts and joins it, then removes the directory and checks no late
file appears. The negative control omits signal propagation and must demonstrate
its late write. A longer sleep that occasionally masks it is not the correction.

## Isolate each attempt

Create mutable seed/builders per attempt and register mocks/routes before
navigation or action. Join previous work before the next attempt. Identify module
registries, import caches, process globals, mock lifetime and build output paths;
a separate test file or port alone does not isolate these. Do not reuse a cache
or output whose identity omits changed helpers, candidate or dependencies.

A cold dependency optimizer may reload a browser and erase in-memory seeds. Test
cold/warm paths and establish fixtures at the actual lifecycle boundary. Confirm
stories import the production module rather than a copied stand-in. Distinguish
an intentional source snapshot from the module the consuming application runs.

## Wait for meaning and drive the right input

Visibility, quiet frames and an HTTP response are partial signals. Establish
connection/event delivery, seeded content, final mount/focus, loaded font and
portal/transition geometry needed by the next action. Use native keyboard/pointer
input where the contract requires it; record terminal keyboard protocol, focus,
click history and platform. Synthetic DOM events are a different evidence surface.

Use strict mocked API routes: unexpected calls fail with the request identity;
mocked server events must actually connect before assertions. Service-worker
interception is not a deployed backend run. A race reachable by an ordinary user
needs a product guard where appropriate, not only a test sleep or retry. Respect
project rules against restarting an existing server or changing shared build state.

## Prove the affected runner leg ran

Read the real task/project/test-file/shard matching and discover the intended case.
Retain exact command, source, selected counts, skip/fail/error status and relevant
artifacts for each attempt. Check changed helpers are registered as cache inputs.
An aggregate green CI result does not prove an omitted leg ran. A forced single
worker can hide concurrency; an accidental project/shard filter can silently omit
cases. State both changes rather than call them equivalent coverage.

Test Windows path/signal/PTY contracts on their actual surface or report them open;
do not replace a semantic assertion with a timing-based platform skip. Preserve
first-failure traces, screenshots and timeout bodies when a retry passes.

## Measure completed work

Predeclare correctness, work/error counts, input/harness identity and noise/budget.
Use diverse inputs independent of the known timing vector. Empty/error paths and
a hardcoded timing-vector return must fail the correctness gate even if fast.
Count process launches/operations when that is the cost contract; wall-time noise
alone is not a stable bound. Keep code correctness, fixture validity, browser
surface and observed agent use separate. A controlled test is not production proof.

For agent/UI event streams, select relevant controls from the [streaming interaction method](../../orbyn-ai-application/references/streaming-interactions.md#worked-example-and-verification). Exercise the actual selected decoder/reducer/effect boundary and healthy recovery; a handwritten fixture is not SDK, transport or durable-service conformance.
