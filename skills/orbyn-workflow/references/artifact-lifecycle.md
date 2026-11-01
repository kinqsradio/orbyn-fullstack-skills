# Own artifacts and development resources through cleanup

Use when work creates previews, captures, test data or running services. Prefer the
consuming project's existing locations and retention policy. A small edit needs
no extra folders. Create a task directory only when an artifact is needed.

## Choose storage deliberately

| Artifact | Default when the project has no convention | Keep until |
| --- | --- | --- |
| Product source, reusable tests and accepted examples | Existing source/test owners; tracked when intended for delivery | Normal product lifecycle |
| Disposable interactive prototype | Ignored `output/<task>/preview/`, with local assets and a short opening/reset note | Human review ends, or the selected interaction is transferred and the artifact is intentionally retired |
| Screenshots, test captures, profiles and trial receipts | Ignored `output/<task>/evidence/` or approved CI artifacts; retain candidate/state identity | Required review/reproduction and project retention are satisfied |
| Decision or sanitized result summary | Existing design/task document; tracked only when appropriate | Owning decision's useful lifetime |
| Accepted behavioral model, property/config and maintenance instructions | Target's existing tracked verification/test/design owner | Covered behavior remains supported; update correspondence after code changes |
| Disposable database, queue, volume or environment | Unique task-owned namespace/path outside production | Data/recovery and teardown authority are explicitly resolved; volumes are not ordinary rebuild caches |
| Regenerable task cache/build output | Existing package/build policy with owned namespace and reproducible inputs | Its task purpose ends and no active/shared consumer needs it |
| Credentials and private local configuration | Existing permitted secret/configuration owner, outside public output | Owner policy and explicit scope; never treat as cache or copy automatically |
| Downloaded research | Ignored `orbyn-references/` under upstream-review policy | Its research/retention purpose ends |

Verify ignore/export behavior before writing sensitive or raw material. Do not
force-add output, copy secrets into examples, install global dependencies or create
one log per routine change. Files under a temporary OS directory may disappear;
move a requested handoff to a durable project-approved location before promising it.

An explicit durable-prototype/review request keeps approved source/assets/settings
and review records in the consuming repository's existing design owner, using
[review packages](../../orbyn-ui-design/references/review-packages.md). Browser
storage/downloads alone are not that save. Keep raw/private captures ignored and
respect export policy; durability does not grant publication or deletion authority.

## Retention and growth decisions

At a meaningful task boundary, use the same [closeout record](../../orbyn-worktree/references/task-closeout.md),
not another registry. For retained material identify purpose, owner, exact path or
handle, size when useful, reconstruction/reopen method and reason/review event.
Age or a successful rerun makes an item reviewable, not safe to delete. No fixed
auto-delete TTL or scheduled janitor is a library default.

- **Raw evidence:** keep candidate/input identity and diagnostically useful failed
  attempts through required review/reproduction and project retention. Before
  retiring redundant large captures, preserve the selected receipts and state
  which raw files become unavailable. A summary cannot pretend deleted evidence
  remains replayable; a passing rerun alone does not erase an earlier failure.
- **Preview review hold:** keep the usable artifact/assets and supported entrypoint
  until review/release. Then propose preserving the selected reopenable package
  and retiring superseded versions/servers under actual authority. A review hold
  needs a reason/trigger, not permanent hosting or automatic expiry.
- **Regenerable cache:** record pinned inputs/lockfile, supported reconstruction
  command and any unique diagnostics before proposing eviction. Point package managers, virtual environments and
  model downloads at a shared cache outside the task tree where the tool supports
  it, so a worktree stays small. Reuse supported package caches; shared mutable `node_modules`, build outputs or fixture state
  need demonstrated resolver/cache isolation before cross-worktree reuse. A folder
  named cache may contain valuable output; classification follows contents/owner.
- **Credentials, configuration and volume data:** preserve their actual security,
  access and recovery contract. They are not disposable dependencies. A local
  source commit or fresh clone cannot recover their contents automatically.

Choose retention and storage budget from the user's/project's workload and policy.
When idle task resources are eligible for release, act only within cleanup scope
and verify the real result. Holds with unknown ownership name the next resolution
check. Do not touch existing artifacts during a read-only inventory or dry run.

## Record the resources actually started

For a server/worker, retain the session or process identity, command/cwd, bound
address/port, task owner and stopping method. Bind local previews to loopback by
default and serve only their dedicated directory, not the repository or home.
A port number alone does not prove process ownership. If a port is occupied, use
another available owned port; never kill the listener to make room.

Worktrees isolate source, not database names, queues, containers or caches. Use
unique task resource names and fixture data; preserve shared dependency caches and
user-managed services. Keep credentials outside output and public artifacts.

## Close out by state, not elapsed time

- While implementation/review is active, retain the checkout, artifacts and
  reproducible inputs. Do not delete failed receipts when a rerun passes.
- At a human preview handoff, keep the artifact and say whether its server is
  running. Keep an owned server only while it is needed for that handoff; a local
  URL is not permanent hosting. If stopping it, provide the retained artifact and
  exact restart entrypoint. Do not promise future uptime or schedule cleanup
  without a requested automation.
- When the task's checks finish, stop owned background work no longer needed,
  inspect termination and preserve relevant diagnostics. Remove only known
  disposable task data within cleanup authority. Shared or unknown resources stay.
- Before worktree removal, preserve needed ignored artifacts/configuration and
  verify the destination can be reopened. Follow
  [worktree cleanup](../../orbyn-worktree/SKILL.md#preserve-before-cleanup) for Git
  state, active ownership, archive/remove and recovery. A clean status or merged
  PR does not prove the tree has no valuable output. Uncommitted/unpushed work or
  pending human review keeps the tree active unless deliberately preserved and
  released within scope.

Prefer graceful session/process termination and the environment's normal teardown.
For containers, identify the exact task project and distinguish stopping services
from deleting volumes. Never use a global prune, broad kill, forced clean or
volume deletion as routine cleanup. Inspect remaining resources after teardown;
report retained/removed/running state and why, not “cleaned” without evidence.

For a stateful prototype, preserve the preview, editable chart, model/config,
scenario notes and evidence identities as one review package when moving them.
Reopen retained links after relocation; copying HTML alone may omit local assets
or a required server. Record expired/deleted raw evidence as unavailable rather
than implying an old summary still has replayable receipts. Retain approved
durable models/tests under their tracked owner separately from disposable exports.

Example: a reviewed patch is merged, but its ignored prototype is the only copy
and a teammate uses the same database. Preserve/reopen the prototype outside the
retiring tree, release only the task's own preview process, leave the shared database,
and then perform eligible Git cleanup. No merge-triggered deletion of all resources.

Primary background: [Git worktrees](https://git-scm.com/docs/git-worktree) and
[Docker Compose teardown](https://docs.docker.com/reference/cli/docker/compose/down/).
Use the installed tool's semantics; this policy grants no new destructive authority.
