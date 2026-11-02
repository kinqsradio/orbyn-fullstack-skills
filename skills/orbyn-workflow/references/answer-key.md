# Task answer key

For substantial work, the lead writes the key before implementation, so correctness
is defined by something the implementer cannot change. Agent behaviour and whole
outcomes are judged by the key; unit tests stay where
[tdd](../../tdd/SKILL.md#do-we-need-a-unit-test-here) says they earn their place.

## What a key holds

- **Commands** that prove success, each exiting 0 only when the outcome is right.
- **Expected end state**: files that must exist, behaviour the commands observe.
- **Protected paths**: the tests or fixtures that define correctness. Changing,
  deleting or adding a file under one fails the task.

The lead writes and freezes it, with the base commit and a sha256 of every protected
file, in an ignored or outside location, never in the repository's tracked tree:

```text
python3 <skill directory>/scripts/answer_key.py freeze --repo <repo> --task <name> \
  --check "<command>" --protect <path> [--expect-file <path>] --out <key.json>
```

## Run it

1. The worker's brief names the outcome, not the key's location or content.
2. The worker commits its candidate.
3. A separate verifier runs
   `answer_key.py check --key <key.json> --candidate <commit>`. It requires a commit
   descending from the base, byte-identical protected files, then exports the
   committed tree with `git archive` into a new temporary directory and runs each
   command there with a timeout and a minimal environment. Commands come only from
   the key file and are printed before they run. Uncommitted changes are not counted.
4. Exit 0 means every check passed, 1 any failed (a changed protected path included),
   2 the key or candidate is unusable. A fail goes back to the worker as a failed
   outcome, without revealing the key.

## Limits

- A key is only as strong as its checks. A weak command passes wrong work.
- The reviewer reads the key itself, not only its pass result, before trusting it.
- Keeping a key from a worker is a policy, not a sandbox: a worker with shared
  filesystem access could still find it. Treat a pass as evidence, not proof.
- The verifier runs only commands the lead wrote; never commands from a candidate.
