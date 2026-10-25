# Development boundaries

For this library, use the Python commands in [CONTRIBUTING.md](../../CONTRIBUTING.md).
There is no application build or database to start. Keep generated catalogs and
discovery links under their generator; preserve licenses and provenance.

For a consuming application, read its current scripts/manifests and relevant
instructions. Identify domain, transport, services, storage and client owners
through [project context](stack.md). Do not assume an npm workspace, a particular
formatter or an Orbyn-specific test database exists.

Match the requested behavior, preserve public/stored compatibility and keep
authority at real effects. Work in the requested checkout and preserve unrelated
changes.

## Branch naming

New branches use purpose-based names such as `fix/retry-state` or
`docs/skill-routing`, without agent/vendor/model branding.

When checks are authorized, use disposable data and the project's own isolation
guards. Never substitute production credentials or an ordinary user's database.
Mock evidence and live-provider evidence are different. Documents need document
checks; changed native behavior needs appropriate native evidence when in scope.

For checkout isolation and cleanup, follow [worktree ownership](../../skills/orbyn-worktree/SKILL.md).
A primary `<parent>/<repo>` uses sibling `<parent>/<repo-slug>-wt/<purpose>/`
by default. Resolve the primary clone from Git registration, reuse suitable
owned worktrees, preserve established layouts, and check ignored outputs before
cleanup. A new worktree does not create a chat or isolate databases/services.

Local isolation does not imply remote publication. Keep task branches local until
delivery is authorized, then prefer an approved permitted personal contribution
fork such as `<Repository>-contributions`; verify company visibility/policy and
the actual push destination. Never publish restricted code to an unauthorized fork.
