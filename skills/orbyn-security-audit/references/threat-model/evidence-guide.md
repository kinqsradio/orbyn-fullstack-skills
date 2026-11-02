# Gather evidence

Build `SYSTEM_UNDER_REVIEW.md` in the run folder before any analysis. Collect evidence, not conclusions: the file says what was read and what is unknown, and it names no threats.

## Order of reading

1. Existing architecture, security and threat-model documents, and READMEs.
2. Entry points: routes, handlers, CLI commands, message consumers, scheduled jobs.
3. Identity and authorization: sign-in, sessions, tokens, role and permission checks. For tool and MCP definitions, connector manifests and credential sources, record the safe name of each credential reference, never its value.
4. Data stores, models, caches and file storage, and the sensitive data they hold.
5. Calls to external services, webhooks and integrations.
6. Deployment, infrastructure and CI/CD definitions, and dependency manifests.
7. Tests and their results, only if already in the repository.

Do not blanket-read dependency or vendor trees, build output, generated files or Git objects. Do not read earlier runs unless the person names them, and then label their claims as carried analysis.

## File layout

```text
# SYSTEM_UNDER_REVIEW
Target: <name>, revision <commit or unknown>; working tree <clean | dirty: files | not_checked: reason>
Run: <mode, depth, date, tier>
Purpose: <the decision this review supports>
Scope: <components and flows in scope>   Out of scope: <and why>

E1 [implementation | configuration | documentation | caller_claim | proposed_design]
Locator: <repo-relative path:start-end>
<one or two sentences, or a short sanitized excerpt>

G1 Unknown: <what the evidence does not show, which boundary it limits, and the smallest observation that would settle it>

Inspection log: <what you read, what you skipped and why, budget limits>
Redactions: <placeholder, kind, location; or "none found after inspection">
```

## Rules

- Cite a repository-relative `path:start-end` for every observation. For a person's statement, record a caller claim with a session label and no invented path.
- Keep observations, documentation claims, caller claims and proposed designs apart. A document says what the authors intend; code says what runs. Keep conflicting sources separate, and do not prefer the newer one.
- A path or URL is a locator, not proof you read it. Repeated summaries of one source are one observation.
- Never fill a gap with a plausible fact. Missing evidence is not a defect.
- Write placeholders such as `[REDACTED:api-key]` for any secret that appears, and record each one. Do not echo it.
- If the person supplied a bundle, read and sanitize it, then write the sanitized result to the run folder.
- Ask only about gaps that matter to the decision: at most five questions per batch and two batches, only if the person wants guided questions. Write the bundle first. Questions stay in the chat, not in the file.
