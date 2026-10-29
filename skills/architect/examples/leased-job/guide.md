# Two workers, one stale result

This runnable synthetic service demonstrates why a lease expiry is not a fence.
It is an executable implementation with a separate TLA+ model, not a claim that
TLA+ automatically proves JavaScript or a production distributed database.

## Run

Use the [optional compiler prerequisites and doctor](../../references/statechart-compiler.md).
Set `library`, `node_bin`, `java_bin`, `tlc_jar` and `pele_module` to actual trusted
paths. Choose a new ignored output with an existing parent. No download, global
setup, target modification or package install occurs.

```sh
python3 "$library/skills/architect/examples/leased-job/demo.py" \
  --node "$node_bin" --java "$java_bin" --tlc "$tlc_jar" \
  --pele "$pele_module" --out "$new_demo_output"
```

Open `new_demo_output/index.html`. The command checks both variants, reads each
property result, obtains both actual counterexample traces, replays public
methods, renders three SVGs and writes command/source/output receipts. It exits
2 with logs retained when a dependency, check, replay or render fails. Output
must be new: keep failed attempts and rerun with another name. Rendering is not
layout inspection; inspect the resulting page before presenting it as qualified.

The compiler can put all reported paths into one chart without saving a raw file
for every invariant. The demo therefore runs plain TLC with only PublishedFresh
in a separate colocated model/config directory to obtain its five-step trace.
It does not guess a nonexistent `tlc-PublishedFresh.out` path. Plain TLC's expected
invariant exit is 12; the compiler adapter uses 1 for its violation report.

## The numbered failure

1. Worker 1 claims the job at epoch 1 and retains that delivery token.
2. Its lease expires; expiry makes the job available but cannot retract the token.
3. Worker 2 claims at epoch 2. Worker 1 still holds epoch 1.
4. The broken completion path accepts worker 1's old payload, committing result
   epoch 1 into a job whose current generation is 2 (**FreshResult fails**).
5. Publish stores that stale result (**PublishedFresh fails**).

The fixed method consumes and rejects the stale delivery while preserving worker
2's lease and the absence of a result/publication. Worker 2 can then complete;
cancellation is too late to undo that committed result, and repeated publish
calls produce only one ledger entry. Cancellation before commit instead prevents
both completion and publication. These observations are asserted by
[replay.mjs](replay.mjs), including all decoded states in the broken trace.

## Source and model correspondence

Inspect [job.mjs](job.mjs), [LeasedJob.tla](LeasedJob.tla),
[broken.cfg](broken.cfg), [fixed.cfg](fixed.cfg) and [view.mjs](view.mjs) together.

Every method is one serialized boundary in this example. A production check,
await and write separated across transactions cannot be collapsed into it.
The model's `Broken` constant and implementation's explicit `brokenCompletion`
option select the actual missing completion fence; both variants execute the
same public methods and differ at that guard. No production code is patched.

| Stable event/rule | TLA+ owner | Executable owner / observation |
| --- | --- | --- |
| Worker.Claim(worker) | Claim, Claim1/Claim2 | job.mjs `claim(worker)` admits only ready work, increments generation and records its delivery token |
| Lease.Expire | Expire | `expire()` clears current ownership; it leaves already issued tokens intact |
| Worker.Complete(worker) | Complete, Complete1/Complete2 | `complete(worker)` consumes its slot; fixed guard checks phase, owner and generation before committing payload |
| Client.CancelBeforeCommit | Cancel | `cancel()` accepts ready/leased only, leaving no result |
| Client.CancelAfterCommit | LateCancel | `cancelAfterCommit()` records the late request; durable result is preserved; view names it explicitly |
| Publisher.Publish | Publish | first `publish()` appends one job-key result; repeated calls abstract to terminal stutter |
| Terminal | Terminal | `terminal()` observes cancelled or published; not a new external effect |
| FreshResult | FreshResult | committed payload generation equals current job generation |
| PublishedFresh | PublishedFresh | published payload belongs to the current committed generation |
| CancelledHasNoResult | CancelledHasNoResult | precommit cancellation leaves no result or publish effect |
| TypeOK / NoDeadlock | type domain / implicit TLC check | finite sample states and explicit terminal stutter; no JavaScript type or production deadlock proof |
| EventuallyTerminal | temporal property with WF(Progress) | conditional progress assumption, not an unconditional real scheduler guarantee |

TLC reports the parameterized operator `Claim`/`Complete` rather than necessarily
its aliases. Replay retains that raw identity and resolves worker identity from
the concrete owner or changed token slot. The view uses that evidence for its
worker labels; it does not join events solely by a human-readable short label.

## Bounds and honest projection

One job, two worker slots, generations 0..2, one result, a 0..1 publication count
and one late-cancel observation. The real synthetic implementation shares the
max-two-generation bound: expiry is enabled only before generation 2. Rejected
completions consume their pending slot. Time, database transactions, crashes,
network delivery, multiple job keys, durable idempotency across restarts and
unbounded retries are excluded. This is not production distributed-lock proof.

Weak fairness of `Progress` assumes an enabled completion/cancellation/publish
step eventually occurs. The bound prevents endlessly expiring leases. Under
those assumptions TLC actually checks EventuallyTerminal; intentional terminal
stuttering alone would not establish it.

The view proposes three concurrent regions (job and two delivery slots). Their
coupling can require parent-state fallback when regions would invent possible
combinations. Read the report's actual disposition. Do not manually replace a
rejected projection with a falsely independent region chart. The HTML foregrounds
a focused failure path derived from the real trace, while retaining both complete
generated model projections and reports. Late cancellation is a visible state
label, not an omitted same-label step.

## Verify or change it

Run the opted-in adapter tests with the same explicit tool paths:

```sh
ORBYN_STATECHART_NODE="$node_bin" ORBYN_STATECHART_JAVA="$java_bin" \
ORBYN_STATECHART_TLC="$tlc_jar" \
  python3 -m unittest discover -s "$library/tests" -p test_statechart_compiler.py -v
"$node_bin" --disable-warning=ExperimentalWarning --test \
  "$library/tests/statechart-projection.test.mjs"
```

Without those explicit variables ordinary Python CI checks adapter contracts but
reports Java/TLC integration tests skipped, not passed. All model/config/view,
implementation and replay hashes are retained in the demo receipt. After any
boundary/guard change, update the map and rerun both variants and replays; an old
passing model says nothing about a changed implementation. This sample is
Orbyn-authored; the optional compiler preserves its separate pinned MIT notices.
