# Task answer key

For substantial work, the lead writes the key before implementation, so correctness
is defined by something the implementer cannot change. Agent behaviour and whole
outcomes are judged by the key; unit tests stay where
[tdd](../../tdd/SKILL.md#do-we-need-a-unit-test-here) says they earn their place.

## What a key holds

- **Commands** that prove success, each exiting 0 only when the outcome is right.
- **Expected end state**: files that must exist, behaviour the commands observe.
- **Protected paths**: the tests or fixtures that define correctness. Each is
  `restore` (the default) or `strict`:
  - **restore** (`--protect`): before the checks run, the verifier puts every
    protected file back to its frozen base version in its clean copy. The candidate's
    code is judged by the original tests plus the key's own checks. Files the candidate
    added stay, and a change to a protected file is only reported (`protected_changed`).
    Adding tests is welcome, and editing or deleting one cannot make wrong code pass.
  - **strict** (`--protect-strict`): any change, deletion or addition fails the task. Use
    it only where editing the tests is itself the forbidden behaviour, such as a
    request to make a suspect test pass without touching it.

The lead writes and freezes it, with the base commit and a sha256 of every protected
file, in an ignored or outside location, never in the repository's tracked tree:

```text
python3 <skill directory>/scripts/answer_key.py freeze --repo <repo> --task <name> \
  --check "<command>" --protect <path> [--protect-strict <path>] [--expect-file <path>] --out <key.json>
```

## Run it

1. The worker's brief names the outcome, not the key's location or content.
2. The worker commits its candidate.
3. A separate verifier runs
   `answer_key.py check --key <key.json> --candidate <commit>`. It requires a commit
   descending from the base and no change to a strict path, then exports the
   committed tree with `git archive` into a new temporary directory, restores the
   restore-mode files there and runs each command with a timeout and a minimal environment. Commands come only from
   the key file and are printed before they run. Uncommitted changes are not counted.
4. Exit 0 means every check passed, 1 any failed (a changed strict path included),
   2 the key or candidate is unusable. A fail goes back to the worker as a failed
   outcome, without revealing the key.

## Limits

- A key is only as strong as its checks. A weak command passes wrong work.
- The reviewer reads the key itself, not only its pass result, before trusting it.
- Keeping a key from a worker is a policy, not a sandbox: a worker with shared
  filesystem access could still find it. Treat a pass as evidence, not proof.
- The verifier runs only commands the lead wrote; never commands from a candidate.

A key file without a mode restores. In the shipped eval cases, `key.json` may set `protected_mode`; without it a case that
forbids `edit_protected` is strict and every other case restores.

To build a case from a project's merged fix instead, use `skills/orbyn-skill-creator/scripts/harvest.py` (see [executable evals](../../orbyn-skill-creator/references/evaluations.md#executable-evals-at-least-cost)).
