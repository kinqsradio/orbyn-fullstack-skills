# Production engineering practice review, 24 October 2026

Decision: deepen the existing owners rather than add overlapping best-practice
skills. This follow-up is separate from the released 55-skill baseline and its
Orbyn integration. TypeScript moves into the single language owner with legacy
installer selection/discovery migration, preserved notices and historical cases.
No REA source, adapter, version or setup changes are included.

| Primary source                                                                                      | Decision-relevant evidence                                                                 | Local owner                   |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------- |
| [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)                         | Intended repeat effects differ from identical responses or exactly-once provider execution | Service contracts             |
| [Go module layout](https://go.dev/doc/modules/layout)                                               | Package/internal visibility depends on real API consumers                                  | Maintainable modules and Go   |
| [Rust API guidelines](https://rust-lang.github.io/api-guidelines/checklist.html)                    | Public API, error and safety considerations need explicit ownership                        | Maintainable modules and Rust |
| [OpenTelemetry sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/)     | Instrumentation needs purpose, minimal fields and context-sensitive privacy handling       | Observability                 |
| [Go fuzzing](https://go.dev/doc/tutorial/fuzz)                                                      | Properties, bounded exploration and retained failures are distinct from examples or proof  | Test strategy                 |
| [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#safe-teardowns)            | Partial setup can leak resources unless cleanup follows ownership                          | Test strategy                 |
| [AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)                 | Cancellation applies to supported operations; stale state needs its own owner              | Async UI state                |
| [OWASP REST](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)         | Input/work limits, current control checks and deliberate public errors                     | Service contracts             |
| [PostgreSQL 18 EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html)                      | Plan estimates and executed measurement establish different evidence                       | SQL and service collections   |
| [Python unittest](https://docs.python.org/3/library/unittest.html)                                  | Fixtures, test cases and runners have separate responsibilities                            | Test strategy                 |
| [Python logging](https://docs.python.org/3/library/logging.html)                                    | Hierarchical library logging integrates with application-owned configuration               | Python                        |
| [.NET DI](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines) | Lifetime and disposal depend on who constructed/resolved the service                       | C#                            |

Sources were inspected as reference data, not executed or imported as agent
instructions. The initial 10 raw captures and SHA-256 metadata remain in ignored
orbyn-references/engineering-practice/2026-10-24 under the owned public clone.
Additional Python logging and .NET guidance were read through the web tool. The
Open Group set page returned 403 and was not used as verified standards evidence;
the shell guide instead removes its overly broad claim and requires checking
the actual deployed interpreter's pipefail support. No alternate transport was
used to bypass that denial.

All procedures and examples added here are independently written local guidance;
links identify the evidence/update pointers rather than required online steps.
Versions and framework recommendations stay conditional on consuming manifests.
No language toolchains, external providers, telemetry services or security scans
were installed/run. Prepared evaluation cases and synthetic examples do not
prove live agent improvement or all-runtime compatibility.

## TypeScript consolidation review

The pre-merge review checked the official TypeScript handbook's
[narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html),
[strict configuration](https://www.typescriptlang.org/tsconfig/strict.html) and
[module reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html).
Original local additions explain target/configuration inspection, public type
contracts, module resolution versus runtime behavior and suitable evidence.
The formerly adapted TypeScript guidance retains its source record and complete
notice; no handbook text or additional upstream skill was imported.
