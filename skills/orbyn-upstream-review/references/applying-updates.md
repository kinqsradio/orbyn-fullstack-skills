# Applying a code or skill update

Read this when a reviewed change will alter code, a dependency, a skill or an
adaptation.

## Code and dependency updates

Inspect API/ABI and stored-format compatibility, supported platforms/toolchains,
transitive dependencies, license changes and relevant security advisories. Map the
patch to actual callers, configuration and data. Choose a patch, dependency upgrade,
maintained local adaptation or no update with a concrete reason.

Update packages through the project's lockfile/package manager and vendored source
through its source manifest. Do not relabel a source review as a security audit or
import a generated build/cache tree as application code.

Run the applicable build/type/behavior checks and prepare a migration or rollback
plan; a source comparison alone leaves runtime compatibility unverified.

## Skill updates

Update routing, related skills, discovery, provenance, manifest and relevant
evaluation cases together. Do not change frozen holdout criteria to improve a
measured result.

## Where changes belong

Identify the canonical repository or consumer-owned adaptation first. Keep
company-only changes in the target's established owner paths under its own discovery
rules; setup imposes no directory convention. Shared improvements follow the
allowlisted public contribution path. Preserve licenses and honest provenance.
Independently written ideas do not justify removing notices from copied or derived
material.
