# Orbyn engineering workflow ownership

The library maintains one active owner for each engineering decision. Improvements
are integrated into these skills rather than installing overlapping collections
or making the user invoke a sequence of helper skills.

| Decision                                                                                        | Owning guidance                    |
| ----------------------------------------------------------------------------------------------- | ---------------------------------- |
| Caller burden, useful hidden complexity, actual variation and public/private module boundaries  | `architect`                        |
| Complete narrow delivery outcomes, prerequisites, blocking edges and acceptance                 | `orbyn-plan`                       |
| Investigation, scoped implementation, verification and delivery handoffs                        | `orbyn-workflow` / `figure-it-out` |
| Repeatable symptom, source tracing, one material hypothesis change and missing runtime evidence | `how` and the defect playbook      |
| Observable behavior, effect seams and one verified failing contract at a time                   | `tdd`                              |
| Concrete caller/contract risks, counterexamples and proportionate evidence                      | `interrogate`                      |
| Existing project discovery, local company namespaces and backed-up setup                        | `orbyn-setup`                      |
| Explicit portable source audit, coverage, independent verification and structured records       | `orbyn-security-audit`             |

The user describes the outcome. The agent chooses relevant owners, uses the
consumer’s terminology, completes authorized helper steps and reports actual
evidence. Setup/spec/ticket commands are implementation tools, not extra manual
invocations for the human. Company-only procedures remain consumer-owned.

`openSrc/` is an ignored local research scratch area. It is never tracked,
published, installed, exported or required by CI or active skills. The library
checker rejects tracked files there. Active instructions are self-contained local
guides; only necessary licensed support files are deliberately distributed, with
copyright, license, revision and hashes in their legal/provenance records.

CI validates metadata, links, managed hashes and helper behavior using synthetic
fixtures. These checks do not establish live model quality, application runtime
behavior or a completed independently verified target audit.

## Languages and stack decisions

`language-best-practices` selects a local reference from actual code and runtime
evidence; TypeScript schemas use the local TypeScript reference under that same owner. `orbyn-stack-selection`
connects research to architect with a constraint-led decision and operating/exit
costs. Neither route replaces API/migration/UI/CI owners or requires an additional
human invocation. Written examples and evaluation definitions are not live-agent
qualification.

## Production best practices at existing owners

Maintainable modules and polyglot contracts stay with architect. Bounded APIs,
pagination/retry semantics and useful private diagnostics stay with backend
design. TDD selects practical contract-test boundaries when testing is requested;
CI maintains consumer-owned recipes and last-confirmed evidence. Async screen
state remains with the UI owner. Language guidance selects one local reference
for all 13 languages, including TypeScript; no overlapping collection or extra
human invocation is required.
