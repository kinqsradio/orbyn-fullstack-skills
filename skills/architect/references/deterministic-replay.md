# Deterministic core and replay verification

Read when a result must be reproducible or checked on a server, such as a game
score, a simulation or a rules engine. Related: [runtime boundaries](runtime-boundaries.md).

- **Deterministic simulation.** Advance state in fixed timesteps with seeded
  randomness. State updates read no wall clock and no unordered iteration (use
  sorted keys or arrays).
- **Input log as the record of a run.** Store the seed, the version and the inputs
  by tick. The log, not the final state, is the source of truth.
- **Replay.** Feed the log back into the core to debug a report or as a test:
  same log, same final state.
- **Server-side re-simulation.** To verify a client-submitted result such as a
  score, the server replays the submitted log and computes the result itself.
- **Security boundary.** Trust only inputs, never client-reported outcomes. Also
  bound the log (length, rate, legal inputs) before replaying it.
- **Version the simulation.** Put a version in every log and keep old versions
  runnable, or migrate their logs, so old runs still replay.

Synthetic example: a client sends `{version: 3, seed: 42, inputs: [...], score: 900}`.
The server runs version 3 on the seed and inputs, gets 750 and rejects the claim.
