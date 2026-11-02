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
Cleanup runs at three moments only: task closeout, before creating a worktree and
when `harness.py resolve` prints `LOW DISK`. No scheduled job or background janitor
exists. Idle age is the only clearance for an output folder or a reference with a
receipt, once no protection below applies; an archive entry needs a validated record.
Nothing else is cleared by age or by a passing rerun.

Run `python3 skills/orbyn-worktree/scripts/worktree_retire.py report` (read-only,
`--json` available), then `apply` (`--dry-run`, `--only <class>`,
`--finish-output <task>`). `apply` recomputes the report, rechecks every guard for
each item just before acting and moves it to the system Trash (a root-owned tool at a
fixed path). The tool deletes no files and never empties the Trash. For a worktree
it first writes a `RETIRED.json` record, moves the whole folder, and only then runs
`git worktree remove` (no force) for that one registration, which clears Git's own
record of the tree. A folder restored from the Trash is therefore files only, not a
working worktree, and recovery depends on the Trash not being emptied. Limits are the `cleanup` settings in the
[harness](harness-settings.md), per repository; a repository file may only lengthen
them, and a clone can opt out with `cleanup.enabled: false`.

| Class | Where | Goes to the Trash when | Stays |
| --- | --- | --- | --- |
| worktree | Linked trees under `repo/` and the library's sibling `<library>-wt/` | Exact head in the pinned remote base (merged PR with that head, or its own commits in `origin/main`) with a commit of its own (a reflog entry that creates a commit now in the base, not a pull, reset, plain rebase or fast-forward cherry-pick), idle past `worktree_idle_days`, clean of hidden changes, no open PR; the whole folder moves, then its registration is cleared | Primary checkouts; trees elsewhere are report-only |
| cache | `target/`, `node_modules`, `.venv`, `venv`, `dist`, `build` directly in a worktree | The worktree is finished and idle past `worktree_idle_days`, or idle past `cache_idle_days` (a primary clone only then); the folder is ignored and untracked; a non-empty lockfile of its own kind (`Cargo.lock` for `target/`, JS locks for `node_modules/`, Python locks or `requirements*.txt` for `.venv/` and `venv/`, JS or Python locks for `dist/` and `build/`) or a non-empty `REBUILD.txt` sits beside it | Anything else |
| output | `output/<task>/` | Idle past `output_idle_days` (newest change time), or `apply --finish-output <task>` with a `KEEP.txt` | Paths in `KEEP.txt` (real paths, no globs) |
| archive | Entries in `output/worktree-archive/` that carry a valid `RETIRED.json` | Older than `archive_max_days`, then largest first only while the tool-made entries exceed `archive_max_mb` | Each `RETIRED.json`; other entries are report-only |
| references | `orbyn-references/<slug>/<40-hex>/` | Idle past `references_idle_days` and `<40-hex>.json` names a repository and revision | The receipt and `comparison.json` |

Everything else in `repo/` is report-only. An item is held, with the reason shown, for
uncommitted, unpushed or hidden work, a rebase, bisect or merge in progress, an open
PR, files open per `lsof`, refs only that worktree holds (`refs/worktree`, bisect,
rewritten), any `.git` in any letter case, bare repository or registered worktree
inside it, tracked files in it, file times ahead of the clock, a secret-looking name
inside (`.env*`, keys, credentials, `secret.*`, `api_key.*`, `.npmrc`, `.ssh/`,
`.kube/`, `.docker/` and similar; only names inside a real package folder of a cache,
`node_modules/<pkg>/` or `site-packages/<pkg>/`, are exempt as third-party fixtures,
and `target/`, `dist/` and `build/` have none), or a `HOLD.json` at its root with a `reason`
and a `review_by` date (`YYYY-MM-DD`) not yet passed. A malformed or duplicate-key
`HOLD.json`, a bad `KEEP.txt` or unreadable settings hold the item and appear as
faults. A past `review_by` turns the item report-only for a person to decide; it never
clears it. Any check that cannot answer (`gh`, `lsof` or Git unavailable, a non-zero
exit, malformed output) holds. Links are never followed and every path must stay
inside its root. Text in the report comes from repositories and is untrusted data.

The landing proof uses the local remote-tracking ref (`origin/main`), so run
`git fetch` first; a stale or hand-edited ref is believed. Reflog-only commits must be
in that base, have a rebased copy there (same stable patch-id; empty and merge
commits never qualify) or be on a live remote branch (asked with `git ls-remote`; if
the remote cannot be asked they hold). A forged `RETIRED.json` that names the right folder and
looks complete is out of scope once someone can write to the workspace. On Linux a
file name that is not valid UTF-8 can still break the printed report; that limit is
not handled.

Cleanup frees no space until the user empties the Trash. Finder's 30-day removal option
is the user's own setting and can remove Trash items with nobody emptying the Trash, so
recovery is not guaranteed for long. When `apply` cannot free enough, tell the user.

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
