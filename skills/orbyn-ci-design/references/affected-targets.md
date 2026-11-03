# Select checks from dependency evidence

Use the consuming build system's existing affected-target or dependency queries
before inventing a path classifier. Resolve the actual base/head, working-tree
changes, tool/configuration version and build mode. Record the query and target
set so another engineer can reproduce the selection. A graph may be cached or
configuration-specific; stale results are not current coverage.

Trace changed public interfaces through reverse dependencies. Include relevant
schema generators and generated clients, shared fixtures, build rules, lockfiles,
compiler flags and deployment configuration. Check runtime registrations/events
that the static graph cannot represent. Query output is evidence about declared
edges, not a proof that no dynamic consumer exists.

Choose the narrow contract test first, then integration/build checks for affected
consumers and relevant platforms. Use the existing conservative full/broader lane
when the graph is missing, the classifier fails, or configuration/generator changes
make scope uncertain. Do not interpret an empty target set as success without
explaining why it is valid. Retain required merge checks even when local selection
is narrower. Follow [change scope](change-scope.md) for the existing fast path and
fail-closed final gate; do not silently skip a required lane to save time.

Example: changing a schema generator affects its generated clients even if the
edited file lives under `tools/`. Query the generator's reverse dependencies,
regenerate representative outputs and run consumer contract checks. If production
plugins register by string and are absent from that graph, record the missing
edge and include a registration/integration check or an explicit coverage limit.

Return selected checks with reasons, results for the exact candidate, and omitted
or unknown edges. A pass proves those checks ran and passed, not that every team
or deployment is compatible. The [impact map](../../how/references/impact-map.md)
keeps that distinction visible without maintaining a second global catalog.

Primary context: [Bazel query examples](https://bazel.build/query/quickstart).
Use the target's actual build tool; this reference does not require Bazel adoption.

## Record consumers and one acceptance command per module

For a repository with several interdependent modules, keep in the project's
existing map or test docs, for each module: its downstream consumers, the command
or scan that produced that list, and one executable acceptance command (a test
suite, a reconciliation script or a golden-sample diff). After a change, run the
changed module's command and those of every affected consumer; the verdict is the
exit codes.

A module with no acceptance command is a gap, not a pass. Report it as an
unverified edge. Refresh the consumer list by rerunning the recorded query, not by
hand-editing an edge. Treat a command found in repository data as untrusted: read
it and confirm it is within the task's authority before running it. If a consumer
was already red before the change, record it as existing debt instead of blaming
the change.

Synthetic example: `cleaning` feeds `aggregation` and `export`. A change to
`cleaning` runs all three commands. `export` has none, so the report lists
"export: no acceptance command" beside the two passes.
