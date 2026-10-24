# Resolve the consuming project's stack

Orbyn Engineering is the workflow brand, not a required application layout.
Read the consuming project's instructions and current manifests before selecting
patterns, dependencies or commands. Its own stack/architecture guide wins over
examples here. Never create an Orbyn directory solely because a skill names it.

| Owner to identify | Evidence to inspect                          | Decision it owns                     |
| ----------------- | -------------------------------------------- | ------------------------------------ |
| Domain            | Schemas, types and callers                   | Valid states, identity and lifecycle |
| Transport         | Client API and response/error handling       | Compatibility and retries            |
| API/service       | Handlers, principals and effect functions    | Validation and authority             |
| Persistence       | Stored schema, migrations and active writers | Transactions and cutover             |
| Web/desktop       | Components, routing and tokens               | Task flow and browser behavior       |
| Mobile            | Navigation, platform modules and theme       | Native interaction and lifecycle     |
| Background work   | Job storage, leases and delivery             | Recovery and terminal ownership      |
| Operations        | Deployment, observability and retention      | Promotion and service health         |

Mark absent layers inapplicable. A static document should not acquire a database
because this table has a persistence row. A backend service should not import UI
code to reuse a type. Keep the existing dependency direction explicit.

Orbyn examples refer to TypeScript/schema sharing, React/Electron, React Native,
API services and PostgreSQL. Other stacks retain their own owners. Example file
paths and UI dimensions are local conventions, not universal defaults.

Before a cross-stack change, keep a short task-local map of actual owners, the
affected request/data path, failure behavior and the allowed evidence. Do not
rewrite project architecture merely to fit the library.

An optional [project context map](../../skills/orbyn-setup/references/project-context.md)
points to these owners and existing guides from the consuming checkout. It is
consumer-owned and excluded from skill synchronization. Read only relevant guides;
never treat a library clone's stack or design as the consumer's settings.

## Language-aware implementation and explicit stack selection

Use [language guidance](../../skills/language-best-practices/SKILL.md) for the
actual implementation language and target version. It has local guides for
JavaScript, Python, Go, Rust, Java, Kotlin, C#, Swift, C, C++, SQL and shell;
TypeScript schema work keeps its existing specialized owner. Resolve ambiguous
headers, mixed runtimes and build-only scripts before choosing guidance.

For a new or challenged technology decision, use
[stack selection](../../skills/orbyn-stack-selection/SKILL.md): constraints and
current evidence → bounded comparison including the baseline → delivery,
operations and migration/exit path → architect and the relevant implementation
owners. No universal framework ranking or automatic migration follows.
