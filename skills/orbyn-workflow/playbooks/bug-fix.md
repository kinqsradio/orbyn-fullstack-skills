# Bug fix

The lead owns the diagnosis and corrected contract. Delegate substantial
investigation and implementation under the parent [workflow](../SKILL.md).

1. Capture expected and observed behavior and the closest authorized reproduction
   using the [reproduction contract](../../how/references/reproduction.md).
   Trace the producing boundary with `how`, using `why` for relevant history.
2. Write the throughput checkpoint. Delegate bounded hypotheses or source paths
   to Investigators; keep observations, inference and missing evidence distinct.
3. Select the supported root cause and design the correction. Assign the fix to
   an Engineer with owned files and allowed checks. Use `tdd` only when authorized.
4. Review the diff, affected consumers and recovery behavior. Return concrete
   fixes to the same child and inspect its changes.
5. Perform authorized verification of the corrected contract, using the original
   reproduction when available. Unavailable reproduction remains a limitation.

6. After the fix, ask whether the bug belongs to a class that happened before or
   could recur (for example, an awaited call missing in a loop). If so, climb the
   [ladder in encode lessons in structure](../../architect/references/principles/encode-lessons-in-structure.md#the-ladder-highest-level-that-works):
   architecture, types, then a lint rule in the project's existing linter whose
   message names the fix, then a test. Prove the new check fails on this bug.

Make the check pass by fixing the code. Never loosen lint, format, type or test
configuration, or delete or weaken a test, to get green; a needed configuration
change is a separate, user-approved decision. Review and fix loops stop after
three unresolved rounds, with the open findings handed to the user.

Small clear fixes stay direct; children implement their assigned fix directly.
Do not broaden runtime access, testing or delivery authority to obtain evidence.
Reproduction-only requests stop at the evidence and limitations. For an upstream
issue, use [contribution intake](contribution-intake.md) to establish availability,
target guidance and scope; submitted PR feedback uses
[bounded iteration](pr-iteration.md). The agent selects these handoffs directly.
