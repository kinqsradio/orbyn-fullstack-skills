# CI/CD and supply-chain checks

Use for the path from contributor to consumer: source change, build worker, dependencies, artifact storage, approval, signing and deployment. Trace the exact inputs, execution authority, build identity, approval subject and released output before forming hypotheses. A protected path is protective evidence, not a defect. NIST SP 800-204D frames CI/CD supply-chain strategy; it is not a compliance claim and a signature is not proof of trust.

## Trace

1. **Contribution to execution.** Permission to submit source differs from permission to run a job with credentials. Follow source, build instructions and dependency declarations through review, job selection and worker start. Which exact revision was approved, and does a later change invalidate it?
2. **Worker and credential lifetime.** Controller, worker process and execution principal are separate. Follow credentials, workspace remnants, caches and outputs across external-contribution jobs, trusted builds, retries and cleanup. A shared worker label proves neither isolation nor escape.
3. **Dependency selection.** The requested identity against the bytes consumed, including indirect inputs, caches and mirrors. Who can replace the input, or the evidence describing it?
4. **Build, approval, promotion.** Correlate source revision, build invocation, material set, output identity and approval subject. Check replacement, rebuild and rollback after approval. An old approval does not describe a different build.
5. **Signing and release authority.** Requesting a signature, signing, approving a release and changing a customer-visible channel are four powers. A valid signature does not prove permitted release, safe source or an uncompromised signer.
6. **Consumer and runtime.** Package, build result and deployable image are different identities. Release promotion, platform admission and scheduling each need one owner.
7. **Failure and recovery.** Interrupted upload, stale approval, signing outage, revoked credential, rollback, emergency publication: pending, failed and published are different states. Invent no freshness window or rollback rule.
8. **Evidence.** Who can alter build, approval, signing and deployment evidence? A worker's own assertion is not an independently protected observation.

## Scenario families

Contributor influence reaching credentials or privileged execution; dependency or artifact substitution between build, approval and deployment; compromised signing or release authority reaching customer-visible software. Treat compromise as an explicit prerequisite unless observed.

## Checks to propose (all `not_run`, isolated, harmless markers)

- The same contributor-controlled build instruction before and after the exact-revision approval, including a retry on a reused worker. Pass: the unapproved job reads no marker and performs no privileged effect.
- Replace a stored candidate after approval; change dependency material before a build consumes it; try promotion through each normal and recovery route; include a signed but unapproved output and a revoked identity. Pass: only the exact approved subject reaches the channel. One denial does not cover other stages. These plans authorize no publication or deployment.
