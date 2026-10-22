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
changes. New branches use purpose-based names such as `fix/retry-state` or
`docs/skill-routing`, without agent/vendor/model branding.

When checks are authorized, use disposable data and the project's own isolation
guards. Never substitute production credentials or an ordinary user's database.
Mock evidence and live-provider evidence are different. Documents need document
checks; changed native behavior needs appropriate native evidence when in scope.
