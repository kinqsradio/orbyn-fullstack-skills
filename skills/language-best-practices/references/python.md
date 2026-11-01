# Python: contracts to preserve

## Resolve the target

Inspect pyproject.toml or packaging metadata, lockfile, interpreter floor and the actual sync/async entry point. Preserve the configured environment manager.

## Apply at the affected boundary

- Own files and connections with `with`/`async with`, and close async resources before their event loop ends. Move blocking I/O out of coroutines with an async client or `asyncio.to_thread`.
- Keep a reference to every `create_task` result: the event loop holds tasks weakly, so an unreferenced task can be collected mid-run. Prefer `asyncio.TaskGroup` (3.11+ only), which holds, awaits and raises for its children.
- Propagate asyncio cancellation after cleanup. Do not swallow `CancelledError` or `BaseException` to make a job look successful.
- Catch the narrowest exception that you can act on, and keep the cause: `raise SyncError(invoice_id) from err`.
- Type hints and dataclasses do not validate external values. Parse at the boundary.
- Distinguish bytes from text. Pass `encoding="utf-8"` explicitly: Python uses UTF-8 by default only from 3.15, and earlier versions follow the locale.
- Use aware timestamps: `datetime.now(UTC)` (3.11+). `datetime.utcnow()` is deprecated and returns a naive value.

## Worked failure and correction

A default argument is built once, so every call shares it:

```python
# Wrong: pending persists across calls.
def enqueue(item, pending=[]):
    pending.append(item)
    return pending

def enqueue(item, pending=None):
    pending = [] if pending is None else pending
    pending.append(item)
    return pending
```

In a dataclass, use `field(default_factory=list)`. The fix gives per-call or
per-instance ownership; it does not make concurrent mutation safe or turn parsed
strings into authorized task identifiers.

## Traps to check

- Closures bind names, not values: `[lambda: i for i in ids]` all see the last `i`. Bind with `functools.partial` or a default argument.
- Pass `subprocess.run` an argument list; avoid `shell=True` with any input. Never `pickle.load` or `yaml.load` untrusted data; use JSON or `yaml.safe_load`.
- Keep imports free of network and setup effects, and preserve package boundaries instead of patching `sys.path`. The application owns log handlers.
- Register cleanup during partial setup.
- Use explicit validation for external input: `assert` disappears under `-O`, so required checks and side effects must not depend on it. Assertions remain appropriate for tests and debug invariants.

## Evidence to report

Use the configured type checker and formatter, then authorized focused tests for malformed input, cleanup or cancellation. Do not claim a type checker validates runtime input.

## Primary references

Reviewed 24 October 2026: [Python 3.13 asyncio](https://docs.python.org/3.13/library/asyncio-task.html), [Python 3.13 dataclasses](https://docs.python.org/3.13/library/dataclasses.html), [logging ownership](https://docs.python.org/3/library/logging.html).

Focused semantics reviewed 30 October 2026: [assert optimization](https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement).

Reviewed 1 November 2026: [create_task references and TaskGroup](https://docs.python.org/3/library/asyncio-task.html), [datetime.utcnow deprecation](https://docs.python.org/3/library/datetime.html), [Python 3.15 UTF-8 default](https://docs.python.org/3.15/whatsnew/3.15.html), [supported branches](https://devguide.python.org/versions/) (3.15 released 9 October 2026; 3.10 is end-of-life).
