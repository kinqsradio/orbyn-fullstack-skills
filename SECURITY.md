# Security policy

## Supported scope

The current default branch is maintained. Report exploitable issues in this
library's scripts, install/sync boundaries or GitHub workflows, and instructions
that cause a concrete unauthorized effect. Problems in an optional external
runtime belong to that upstream project unless the defect is in this integration.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/kinqsradio/orbyn-fullstack-skills/security/advisories/new).
Include the affected revision, a minimal reproduction with synthetic data,
expected/actual effects and any suggested correction. Do not attach real tokens,
private project files, customer data or working credentials.

If the private-report option is unavailable, open a public issue requesting a
private contact channel without vulnerability details or secrets. The maintainer
will provide a route; no unverified response-time guarantee is made here.

## Trust boundaries

Skills are instructions, not a sandbox. Review helpers before execution, preserve
your project's authorization rules and inspect public exports before pushing.
Library validation is not a security audit of a consuming application. Do not
run a Codex Security scan without the user's specific request.

Fork-PR CI runs without project secrets and with a read-only token. Maintainer
publication and private-repository access do not occur in that lane. Report
workflow paths that break this separation as security issues.
