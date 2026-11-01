# TypeScript: schemas, states and callers

Follow the consuming project's instructions first. Use [project instructions and scope](../../orbyn-workflow/references/project-policy.md#scope-and-evidence) and [host configuration](../../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration) where applicable.

This guide owns TypeScript contract changes, including repeated illegal states:
carry each change through the schema and its callers.
[Type-system discipline](principles/type-system-discipline.md) supports state design;
[structural learning](../../architect/references/principles/encode-lessons-in-structure.md)
supports preventing a demonstrated recurrence.

## Resolve the compiler and runtime

Inspect package manifests, the lockfile, tsconfig inheritance, project references
and the actual emitter/runtime. Preserve the supported compiler, strictness, module
format and resolution mode, and do not change compiler options across the repository
as a side effect of an ordinary fix. Use the project's configured check command. A
bundler stripping types does not establish that a type-check ran, and passing
individual files to tsc bypasses the project configuration (TypeScript 7 rejects it
in a directory with a tsconfig unless `--ignoreConfig` is passed).

Read the installed compiler version before reasoning from a missing option:

- TypeScript 6 and 7 default `strict` to true, `types` to `[]` and `rootDir` to the tsconfig directory. Older compilers differ, and a project relying on global Node or test typings must now list them.
- TypeScript 7 is a native port with no programmatic API yet. Tools that need the 6.0 API use `@typescript/typescript6`. Embedded-template checkers for Vue, Svelte, Astro, MDX and Angular may need to stay on 6.0.
- TypeScript 7 makes these errors: `baseUrl`, `moduleResolution` of `node`/`classic`, `target: es5`, and AMD/UMD/SystemJS modules. Treat moving off them as a migration, not a drive-by fix.
- `strict` does not include `noUncheckedIndexedAccess`. Without that option, `rows[0]` has type `Row` on an empty array. Check the length or the configured option before dereferencing.

An ambient declaration can describe an API without making it exist in the deployed
runtime. Node strips types without checking them and ignores tsconfig, so `paths`
aliases do nothing; `enum`, runtime `namespace` and parameter properties fail.
`erasableSyntaxOnly` and `verbatimModuleSyntax` surface those problems in the compiler.

## Represent valid states

Use discriminated unions for state variants, with exhaustive handling where a new
variant must trigger review. Avoid optional-field bags that admit contradictory
states. Take `unknown` for untrusted input, parse it with the owning runtime schema,
and derive shared types from that schema rather than maintaining parallel definitions.

Use `satisfies` to check literals without widening. Narrow before casting; keep an
unavoidable interoperability assertion local and state its invariant. Brand
identifiers when mixing them would cause a real class of bug, not as a blanket rewrite.

Keep total inputs simple: `sum([])` may legitimately return zero. A partial
`newest(xs)` needs an optional result or a justified nonempty contract, not a hidden
non-null assertion. `{start, duration: number}` does not exclude a negative or NaN
duration; enforce that at runtime before claiming the invariant.

Internal types do not establish tenant access or the freshness of stored data, so
keep cancellation, cleanup and authority checks near effects. Match the repository's
formatter and dependency direction in
[development](../../orbyn-workflow/references/project-policy.md#development-resources).

## Keep public types and modules deliberate

Let local inference work, and make exported or cross-package contracts explicit. Use
a generic when it preserves a real relationship between inputs and outputs. Utility
types do not make an internal persistence object a safe public response.

`readonly`/`Readonly<T>` constrain checked assignments, not runtime mutation or deep
immutability. Take an owned snapshot at a validation boundary when values must stay
stable.

Use `import type` for type-only dependencies. Match package exports, ESM/CommonJS
behavior and consumer resolution; a tsconfig path alias does not rewrite a runtime
import. Do not import application code into shared types to repair a cycle.

## One contract across clients

When changing a run's result shape, update the owning runtime schema, derived shared types, transport and web/mobile consumers together. Keep platform-only presentation state separate. Exhaustive handling should expose an unhandled lifecycle variant without forcing the domain layer to import application components.

## Runtime and polyglot boundaries

Use the [JavaScript reference](javascript.md) for runtime, cancellation and resource
effects. Other languages route through [language guidance](../SKILL.md); schema-library
examples here are not a mandatory dependency for them.

## Local contract example

Use the [TypeScript contract guide](typescript-contracts.md) for a lifecycle example,
unknown-input handling, runtime effects and caller migration.

## Evidence to return

Report the actual compiler and configuration, owning schema and affected callers,
plus authorized check results and remaining runtime limits. For a new union variant,
check an exhaustive consumer; for untrusted input, check the real parser's rejection
and legitimate path. A type-check cannot prove tenant access, database compatibility,
rendering or cancellation of an unsupported effect.

## Primary references

Reviewed 24 October 2026: [narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html), [strict configuration](https://www.typescriptlang.org/tsconfig/strict.html), [module contracts](https://www.typescriptlang.org/docs/handbook/modules/reference.html).

Focused semantics reviewed 30 October 2026: [readonly properties](https://www.typescriptlang.org/docs/handbook/2/objects.html#readonly-properties).

Reviewed 1 November 2026: [TypeScript 7.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/), [TypeScript 6.0 notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html), [Node 26 type stripping](https://nodejs.org/docs/latest-v26.x/api/typescript.html).

## Attribution and licence

The language owner includes independently authored operational guidance and synthetic
examples. This consolidated TypeScript guide retains its adapted source lineage and
[original notice](typescript-LICENSE.txt), which continues to apply; consolidation
does not change that history or claim exclusive original authorship.
