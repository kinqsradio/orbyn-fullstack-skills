# SQL: contracts to preserve

## Resolve the target

Identify the engine, exact supported version, driver, schema owner and transaction configuration. Dialects and defaults are not interchangeable: PostgreSQL defaults to READ COMMITTED, MySQL InnoDB to REPEATABLE READ, and SQLite leaves foreign keys off until each connection sets `PRAGMA foreign_keys = ON`.

## Apply at the affected boundary

- Bind values through the driver and allowlist dynamic identifiers separately. Keep tenant predicates and authorization with the effect and database policy owner.
- Encode durable invariants in constraints and atomic writes. A read-then-write transaction at a weak isolation level can still race; use a unique constraint with upsert, compare-and-set, locks or serializable retry.
- Handle NULL's three-valued logic: `= NULL` never matches, `COUNT(col)` skips NULLs, and `NOT IN` returns no rows when its subquery yields NULL. Prefer `NOT EXISTS`.
- Add a unique tiebreak to every ORDER BY that drives pagination; without ORDER BY, row order is unspecified. Keyset pagination stays stable under inserts, where OFFSET skips rows.
- Choose indexes from actual access paths and representative plans. EXPLAIN ANALYZE executes the statement, so use authorized disposable scope for effects. Stored schema and writer transitions belong to the migration skill.

## Worked failure and correction

For PostgreSQL, a revision-checked update can express the conflict boundary:

```sql
UPDATE tasks SET title = $1, revision = revision + 1
WHERE id = $2 AND owner_id = $3 AND revision = $4
RETURNING revision;
```

The caller must distinguish no matched row from success under its authorization
policy. This is not portable placeholder syntax or a full retry protocol.

Keyset pagination with a tiebreak, in PostgreSQL row-comparison syntax:

```sql
SELECT id, created_at, title FROM tasks
WHERE owner_id = $1 AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

## Traps to check

- Use half-open time ranges (`>= start AND < end`); `BETWEEN` includes both ends and can double-count or miss a boundary. In PostgreSQL, store instants as `timestamptz`.
- A function or cast on an indexed column, such as `lower(email) = $1`, usually cannot use a plain index. Add a matching expression index or change the predicate.
- Escape `%` and `_` in user input bound into LIKE patterns.
- Fetch related rows in one query or batch; avoid one query per row from application loops.
- Store money in exact numeric types, not floating point.
- Take row locks in one consistent order to avoid deadlocks, and keep transactions free of network calls.
- Plain PostgreSQL `CREATE INDEX` blocks writes. `CONCURRENTLY` cannot run in a transaction block and can leave an INVALID index after failure; check before retrying.
- For PostgreSQL serialization failures, retry the whole transaction under a bounded policy; replaying its final statement reuses stale reads. Do not blindly retry permanent constraint failures or duplicate external effects.
- A PostgreSQL `CHECK (price > 0)` permits NULL. Add NOT NULL when absence is forbidden.

## Evidence to report

Use the actual engine in a guarded disposable database when tests are authorized. A SQLite fixture does not prove PostgreSQL locking, migration or query-plan behavior.

## Primary references

Reviewed 24 October 2026: [PostgreSQL 18 isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [PostgreSQL 18 comparison/NULL](https://www.postgresql.org/docs/18/functions-comparisons.html), [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html).

Focused semantics reviewed 30 October 2026: [PostgreSQL 18 full-transaction retry](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html), [CHECK/NOT NULL](https://www.postgresql.org/docs/18/ddl-constraints.html).

Reviewed 1 November 2026: [PostgreSQL 18 CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html), [supported PostgreSQL versions](https://www.postgresql.org/support/versioning/) (18 is the newest listed), [MySQL 8.4 isolation levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html), [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html).
