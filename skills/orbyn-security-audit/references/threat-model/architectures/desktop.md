# Desktop application checks

Use for a local user, project files, an application process, privileged helpers, plugins and update distribution. Do not infer a framework, operating system, parser isolation, plugin permission model or update mechanism from the label. Map one id per project, process, plugin, helper, release artifact and installation target. Add [CI/CD checks](cicd-supply-chain.md) for the build and release half of an update path.

## Trace

1. A project file from acquisition through open, parse, preview and save: document-controlled fields, the parser's authority, derived files, resource use. A crafted file is not evidence of parser exploitation.
2. Each external reference from document to resolution to a local read or network request and back. Opening a project is not blanket consent for unrelated reads or outbound disclosure.
3. Local messages from sender identity to the requested operation, the helper's authorization decision and the response recipient. An authenticated transport is not permission for that operation, including a message the application forwards for a plugin.
4. Plugin discovery, activation, update, disablement, removal. Who authorizes capabilities, what persists after revocation, and what runs with application or helper authority? Installed does not mean entitled to install or reach arbitrary local resources.
5. A release from build and publication through download, staging and install. Compare provenance and integrity with product, version, channel, target and requesting principal. A valid signature settles neither permission nor rollback policy.
6. Cancellation, restart, partial install, retry, rollback. Can the artifact or target change between approval and use? Assume no atomic install or rollback.
7. Project copies, previews, temp files, plugin output and diagnostic logs through user changes and cleanup. A helper denial says nothing about preview confidentiality.

## Scenario families

Crafted-document resolution; plugin or local-message operations beyond intended authority; update installation without artifact- and target-bound approval. Give each a grounded or partial disposition. A refusal for one operation does not cover another route.

## Checks to propose (all `not_run`)

- Document resolution with authorized and unauthorized resource cases.
- A plugin without install authority against an authorized updater, through target change and retry. Keep pass, fail and inconclusive separate.
