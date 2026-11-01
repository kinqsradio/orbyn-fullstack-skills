# C# / .NET: contracts to preserve

## Resolve the target

Inspect global.json, target frameworks, language version, nullable context and package locks. Preserve the configured SDK, analyzers and dependency injection lifetimes.

## Apply at the affected boundary

- Nullable annotations help static reasoning; still validate external and deserialized values. Records and readonly references do not recursively freeze mutable objects.
- Return and await Task/ValueTask work, and pass the matching CancellationToken. Reserve async void for interfaces that require it, such as event handlers with explicit error handling.
- Do not block on async work with `.Result` or `.Wait()`: it can deadlock under a synchronization context and starves the thread pool.
- Keep IDisposable/IAsyncDisposable alive until dependent asynchronous work finishes, and use using/await using to match the implemented interface.
- Do not share scoped mutable services such as a DbContext across concurrent operations. Match DI lifetime to owned state: a singleton must not capture request-scoped work.

## Worked failure and correction

Keep the resource alive through the asynchronous read:

```csharp
async Task<string> ReadAsync(string path, CancellationToken token)
{
    using var reader = File.OpenText(path);
    return await reader.ReadToEndAsync(token);
}
```

This requires a target with that overload. Returning the unfinished task from inside
using can dispose reader too early.

## Traps to check

- Rethrow with `throw;`. `throw ex;` restarts the stack trace.
- Do not create and dispose an HttpClient per request. Use a long-lived client with `PooledConnectionLifetime` set, or `IHttpClientFactory`.
- Compare identifiers with `StringComparison.Ordinal` or `OrdinalIgnoreCase`. Some default string overloads are culture-sensitive. Persist numbers and dates with the invariant culture.
- Inspect deferred IEnumerable execution and repeated enumeration. An `AsEnumerable()` or `ToList()` before `Where` moves the filter from the database into memory.
- Consume a returned ValueTask once: await it, or call AsTask once and use that Task. A pooled source may be reused. An ordinary Task supports repeated awaits.
- Distinguish container-owned from explicitly constructed disposal.

## Evidence to report

Use the configured dotnet build/analyzers and scoped authorized tests on supported targets. A cancellation request is cooperative; it does not establish that remote effects were undone.

## Primary references

Reviewed 24 October 2026: [C# disposal statements](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/using), [Disposal with unawaited work](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2025), [.NET cancellation](https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/task-cancellation), [.NET dependency injection lifetimes and disposal](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines).

Focused semantics reviewed 30 October 2026: [Microsoft ValueTask consumption](https://devblogs.microsoft.com/dotnet/understanding-the-whys-whats-and-whens-of-valuetask/).

Reviewed 1 November 2026: [HttpClient guidelines](https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines), [CA2200 rethrow](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2200), [string comparison](https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-strings), [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core) (.NET 10 is the active LTS; .NET 8 and 9 end support on 10 November 2026).
