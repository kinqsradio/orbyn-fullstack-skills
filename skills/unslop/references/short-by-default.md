# Short by default

For chat replies, PR descriptions, issues and checklists. The reader should get
the point in a few seconds. Long text gets skimmed or skipped, and then the one
line that mattered is missed.

## Rules

- **Answer first.** The first line is the result, the decision or the question.
- **Fragments and bullets are fine.** Full sentences are not required. One fact per bullet.
- **Only what the reader needs to act.** Leave out how you got there: chronology,
  repair rounds, retries, tool calls, alternatives you dropped.
- **Do not repeat what the page already shows.** CI results, the diff, commit lists,
  the title, the template's own questions.
- **Numbers and names over adjectives.** "3 tests fail on Windows", not "some
  flakiness was observed".
- **Link, do not paste.** Logs, traces and long evidence go in a linked comment,
  file or run.
- **Keep what changes a decision**, one line each: a limit, a risk, something not
  tested, a decision the reader must make.

Targets, not caps. Go longer only when a reader needs more to decide, such as a data
migration's recovery plan.

| Text | Target |
| --- | --- |
| Chat reply with a result or status | Under 100 words |
| PR description, outside required template fields | Under 150 words |
| Issue | Under 150 words |
| Checklist item | One line, under 12 words |

## Chat replies

- First line: what happened or the answer. Then only what the user needs: what
  changed, what is left, what they must decide.
- No recap of steps the user watched, and no restating the question.
- A table only for comparing several items. No headings in a short reply.
- At most one question, at the end.

## PR descriptions

```markdown
## Summary
- <what changes for a user, one line>
- <second change, if any>

Closes #<n>

## Testing
- CI covers the rest.
- <a check CI does not run, with its result>
- Not tested: <what, or "none">
```

Required template fields stay. Fill each with a few words, not a paragraph.
Review feedback is answered in the review thread; the description says only what
the PR does now.

## Issues

- Bug: one-line problem, numbered steps, expected and actual, version.
- Feature: what a user can do afterwards, in one line, then the checklist.
- Checklist items start with a verb and name the ID in brackets:
  `- [ ] Refresh the model list from the engine (I40)`. Put detail in the linked doc
  or PR, not under the box.

## Example

Before, about 6,000 characters: repair rounds, CI run links, local test counts,
cleanup races and limits, all in paragraphs.

After:

```markdown
## Summary
- Tab icons survive reloads, through the existing image proxy
- Move a live tab to a second panel and back, or open it in its own window

Closes #126

## Testing
- CI covers the rest.
- Not tested: pop-out window by hand on either platform
- Known failure, not from this PR: toolbar drag test (#144)
```
