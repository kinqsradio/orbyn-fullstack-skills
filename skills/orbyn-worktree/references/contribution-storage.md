# Contribution storage and publication

Read this before choosing a push destination, creating or reusing a fork, storing
a private backup or preparing a public PR. Keep work local by default. Publish only
when pushing/PR delivery is authorized and the patch is concrete and reviewable.

## Choose the destination

Inspect existing project contribution policy, sanitized remote identities, upstream
relationship, repository visibility, account permission and fork restrictions.
Confirm what each remote points to; a remote named `origin` may not be a personal fork.
Respect an existing explicit company-branch instruction instead of inventing a
fork requirement.

For company upstreams, prefer one existing permitted **private** personal contribution fork
for the approved account. Create one only within authorized delivery/setup scope
and when company/host policy allows it. Use a meaningful stable name such as
`<Repository>-contributions`, retaining the upstream identity:

| Identity                                             | Example                                       |
| ---------------------------------------------------- | --------------------------------------------- |
| Company upstream                                     | `company/Orbyn`                               |
| Reused personal fork                                 | `approved-account/Orbyn-contributions`        |
| Task branch on that fork, when publication is needed | `feat/task-rescheduling`                      |
| Local task checkout                                  | `Documents/GitHub/orbyn-wt/task-rescheduling` |

Verify that a candidate fork actually belongs to the intended upstream; a matching
name is not enough. Preserve an established fork/name rather than renaming it or
creating one per task. A local worktree stays within the primary clone's Git
repository and can push its task branch to the permitted fork remote; it is not
another hosted fork. Keep fetch/base selection tied to the canonical upstream and
target the contribution PR back to the correct upstream branch.

## Privacy before publication

Prefer private contribution storage whenever the host, upstream visibility and
organization policy support it. Read visibility from the actual API/host result
after creation, not from a requested flag or a private-sounding name. Verify
upstream permissions and organization approval before copying restricted code
into any personal account, including a private repository.

On GitHub, native forks of a public repository are public and cannot independently
be made private. Private upstream forks stay private where forking is permitted;
internal-repository behavior also depends on account/enterprise policy. Do not
attempt to bypass these rules or promise a private public-parent native fork.

Verified 24 October 2026 against [GitHub fork visibility and permissions](https://docs.github.com/en/pull-requests/reference/forks).
Check each other provider's current policy; do not generalize GitHub's constraints
into a universal claim about forks.

If the desired privacy is unavailable, keep task branches/commits local. Within
explicit backup scope, a permitted private standalone repository can hold work,
but it is a separate repository, not a native fork or an automatic upstream PR
source. Verify its actual visibility, access and remotes before any push. Do not
create it merely because an API token can. Never detach, delete or recreate an
existing fork, rewrite its history or change upstream visibility to enforce a
naming/privacy preference.

## Restricted company code

Never copy private/restricted company code into a public or otherwise unauthorized
fork, standalone mirror or account. An available API token does not establish
redistribution authority. If forks are disallowed, use an explicitly authorized
internal contribution path; otherwise preserve the local branch/commits and prepare
a reviewable patch with the exact publishing blocker. Do not silently fall back
to pushing a new company branch or stop independent local work.

## Public upstream PR

When a public upstream PR is explicitly authorized, promote only its reviewed
allowlisted changes through the required public contribution path. Keep unrelated
branches, company-only material, reports and backups local/private. Explain the
visibility boundary before a public push when privacy was requested; if public
publication is not authorized, preserve the patch and report the specific limit.
A private backup does not retract commits already published to a public network.

## Before any push

Verify the destination account/repository/visibility, source branch and refspec.
Add/change a remote or branch tracking only within scope; do not rewrite `origin`,
alter global Git settings, force-push a foreign branch or publish merely because a
branch exists. Report where work is local, backed up, pushed and proposed for review.
