# Language, stack-selection and contribution-privacy review

Reviewed 24 October 2026. Scope: extend the portable library and its existing
routing; no product runtime migration, toolchain installation or REA update.
The implementation is independently authored. Existing imported licenses,
provenance and immutable snapshots remain unchanged.

## Result and ownership

| Need                            | Owning change                                                            | Why this boundary                                                                                |
| ------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Broader language implementation | `language-best-practices` with 12 local guides and name-only router      | Load the affected language reference; keep TypeScript schema ownership                           |
| Decide a technology stack       | `orbyn-stack-selection`                                                  | A constraint/evidence decision feeds architect; ordinary coding retains the established stack    |
| Automatic use                   | Workflow, architecture, research, setup, catalog, presets and both hosts | The agent selects relevant guidance from the task, not another human invocation                  |
| Contribution privacy            | Existing `orbyn-worktree` and PR/delivery links                          | Prefer actual permitted private storage; keep work local when native fork privacy is unsupported |

## Primary evidence and applied decisions

| Area            | Evidence                                                                                                                                                                                                                                                                                                                               | Applied implication                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| JavaScript      | [MDN promise lifecycle](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises), [Node modules](https://nodejs.org/api/packages.html)                                                                                                                                                                            | Await owned work; explicit cancellation/settlement and target module boundaries                                  |
| Python          | [Python 3.13 asyncio](https://docs.python.org/3.13/library/asyncio-task.html), [dataclasses](https://docs.python.org/3.13/library/dataclasses.html)                                                                                                                                                                                    | Cancellation survives cleanup; mutable state has an instance/call owner                                          |
| Go              | [Project review guidance](https://go.dev/wiki/CodeReviewComments), [race detector](https://go.dev/doc/articles/race_detector), [error wrapping](https://go.dev/blog/go1.13-errors)                                                                                                                                                     | Explicit context/worker lifetime, error identity and qualified race evidence                                     |
| Rust            | [Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html), [MSRV](https://doc.rust-lang.org/cargo/reference/rust-version.html), [unsafe](https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html)                                                                                                                     | Real borrow/ownership boundaries, supported targets and explicit unsafe invariants                               |
| Java            | [JLS 25 resources](https://docs.oracle.com/javase/specs/jls/se25/html/jls-14.html#jls-14.20.3), [JDK 25 interruption/threads](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html)                                                                                                                      | Resource release, retained interruption and target-aware concurrency                                             |
| Kotlin          | [Structured coroutines](https://kotlinlang.org/docs/coroutines-basics.html), [exception handling](https://kotlinlang.org/docs/exception-handling.html)                                                                                                                                                                                 | Lifecycle scope and cancellation preservation                                                                    |
| C#              | [Disposal](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/using), [unawaited task resource warning](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2025), [cancellation](https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/task-cancellation) | Await dependent work before disposing; preserve cooperative cancellation                                         |
| Swift           | [Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/), [closure cycles](https://docs.swift.org/latest/documentation/the-swift-programming-language/closures/)                                                                                                                     | Actor suspension can interleave state; own task/closure lifetimes                                                |
| C               | [CERT allocation](https://wiki.sei.cmu.edu/confluence/spaces/flyingpdf/pdfpageexport.action?pageId=87152128), [Clang UB checks](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)                                                                                                                                           | Validate allocation arithmetic and pointer/resource contracts                                                    |
| C++             | [Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), [Clang ASan](https://clang.llvm.org/docs/AddressSanitizer.html)                                                                                                                                                                                       | RAII and borrowed-view lifetime; sanitizer evidence remains scoped                                               |
| SQL             | PostgreSQL 18 [isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [NULL comparisons](https://www.postgresql.org/docs/18/functions-comparisons.html), [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)                                                                                                  | Real engine/isolation, atomic conflicts, and execution-aware query inspection                                    |
| Shell           | Bash [quoting](https://www.gnu.org/software/bash/manual/html_node/Quoting.html), [set semantics](https://www.gnu.org/s/bash/manual/html_node/The-Set-Builtin.html)                                                                                                                                                                     | Arguments stay data; explicit failures, interpreter and utility compatibility                                    |
| Stack selection | [Workload-oriented choices](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/technology-choices-overview), [React constraints](https://react.dev/learn/creating-a-react-app), [SQLite topology](https://sqlite.org/whentouse.html)                                                                        | Hard constraints first, current-system baseline, operations/exit cost and a revisit trigger                      |
| Fork privacy    | [GitHub fork rules](https://docs.github.com/en/pull-requests/reference/forks)                                                                                                                                                                                                                                                          | Public native forks cannot independently become private; a private standalone backup is a separate delivery path |

Versioned references explain semantics, not the current project's installed
version. Moving documentation is dated evidence, not a guarantee of latest
support/pricing or a recommendation to upgrade the consumer. Vendor-specific
pages settle their stated capabilities; they do not establish a cross-vendor
benchmark or universal technology ranking.

## Offline, source and validation boundaries

The committed guides and original worked examples contain the operational
instructions. Raw primary-page downloads and their URL/date/byte-hash receipts
stay in ignored `orbyn-references/language-stack/2026-10-24/`; they are not required
at runtime and are not imported public documentation snapshots. The CERT PDF was
read through the primary web result but its raw archive download was unavailable.
Some Swift pages expose JavaScript-only shells, so the relevant semantics were
checked against the primary rendered/search source as well. Do not call raw HTML
archiving proof of complete rendered-document capture.

The router processes supplied path names only: no workspace crawl, project source
execution, network request or stack/version inference. Ambiguous C/C++ headers
remain explicit. Unsupported languages retain the project's actual owner and a
focused research step; this is coverage for the listed languages, not every
language or framework.

New evaluation definitions cover each language failure, polyglot ownership,
research-only/offline selection, ordinary-edit/prose negatives and private/public
contribution boundaries. All pre-existing cases retain their original criteria.
Structural checks and helper fixtures are not live Codex/Claude trials, proof that
all snippets compiled, platform qualification or a production performance claim.
