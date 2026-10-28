# Controlled Pilot Readiness Plan
**Status:** Approved implementation baseline  
**Baseline:** `main` at `e95e3ba`
**Pilot data:** Synthetic data only  
**Deployment audience:** Invited users only until every exit criterion passes
## Objective
Deliver RuleTwin as a controlled, independently deployable pilot that demonstrates the rounding-rule workflow with defensible tenant isolation, authentication, recovery, operations, and release evidence. This plan does not authorize production customer data or claim general production readiness.
## Supported pilot scope
- One deterministic rounding-rule family.
- NovaBill and Brightline synthetic tenants.
- Analyst, QA reviewer, release approver, and auditor roles.
- Immutable rule, dataset, and policy versions.
- Baseline-versus-candidate simulation, impact calculation, and fail-closed risk decision.
- Checksum-bound approval, allow/block release gates, and append-only audit evidence.
- Invitation-only hosted environment after the deployment gate passes.
## Explicit exclusions
- Real customer, employer, payment, or production data.
- Billing execution or writes to an external system.
- Tiered-rate, late-fee, effective-date, and exception-routing rule families.
- General-purpose scripts, AI-generated rules, or probabilistic safety decisions.
- Public self-service signup.
- A production SLA or multi-region availability.
- DecisionTrace and BoundaryOps integration.
## Workstreams and exit evidence
| ID | Workstream | Required outcome | Exit evidence |
|---|---|---|---|
| PILOT-01 | Identity | Replace the development token endpoint with a selected OIDC provider; validate issuer, audience, expiry, and key rotation; disable development identities outside local mode. | Login/logout tests, invalid-token matrix, key-rotation test, and deployed configuration record |
| PILOT-02 | Tenant isolation | Protect every exposed list, object, export, artifact, worker, metric, and operator path, or keep the unfinished surface disabled. | Complete cross-tenant negative matrix with non-enumerating responses |
| PILOT-03 | Deployment | Reproducible HTTPS deployment of web, API, worker, and PostgreSQL with immutable versioned images and automated migrations. | Deployment record containing commit, image digests, migration version, and smoke results |
| PILOT-04 | Secrets | Store database and identity credentials outside Git and images; redact them from logs and errors. | Secret-store configuration evidence plus planted-secret log scan |
| PILOT-05 | Recovery | Automate backups and prove restore, migration rollback, and worker restart behavior. | Timed restore rehearsal recording achieved RPO/RTO and recovered checksums |
| PILOT-06 | Resource safety | Enforce request, rule, dataset, execution, queue, retry, and concurrency limits. | Boundary, oversize, timeout, saturation, and recovery tests |
| PILOT-07 | Operations | Centralize structured logs and actionable health, error, queue, database, and availability alerts. | Alert smoke tests and an operator/incident runbook |
| PILOT-08 | Supply chain | Gate deployments on CI, dependency/container scanning, SBOM generation, and immutable artifacts. | Passing protected workflow plus SBOM and scan artifacts for the release candidate |
| PILOT-09 | Performance | Measure the named reference profile; never replace isolation or fail-closed behavior to meet latency. | Recorded machine/profile, data set, samples, P95 acceptance latency, and replay results |
| PILOT-10 | Usability | Provide evidence export, pagination, clear failure/retry states, and a rehearsed operator-led pilot flow. | Browser evidence, accessibility checks, and signed pilot acceptance checklist |
## Delivery sequence
1. Close the Phase 4A evidence record and keep `main` green.
2. Implement evidence export and complete authorization for every pilot-visible surface.
3. Integrate production OIDC and disable development identities in pilot mode.
4. Add limits, rate controls, observability, and alerting.
5. Add deployment, secret management, backup/restore, and rollback automation.
6. Run security, isolation, recovery, performance, and usability acceptance.
7. Publish an immutable `v0.4.0-pilot.1` release only after all gates pass.

## Release gate

The pilot release is blocked unless:

- all protected CI checks pass from a clean runner;
- no known S0/S1/S2 defect is open;
- the full exposed-surface tenant-isolation matrix passes;
- development authentication is disabled in the hosted environment;
- backup restore and rollback have been rehearsed;
- secrets, dependency, and container scans have no unaccepted high-severity finding;
- resource limits and alert paths have executable evidence;
- the deployed commit and image digests are recorded;
- only synthetic data is loaded; and
- the owner records the hosting, identity, domain, retention, availability, and access decisions below.

## Owner decisions required

| Decision | Status |
|---|---|
| Hosting provider and budget | Required |
| Domain and TLS ownership | Required |
| OIDC provider and pilot identities | Required |
| Invitation-only user list and tenant-role assignments | Required |
| Backup retention and acceptable RPO/RTO | Required |
| Availability and support window | Required |
| Hosted visibility: private/invitation-only or public | Required |
| Approval to use any data beyond the deterministic synthetic packs | Not granted |

## Current assessment

Phase 4A, evidence export, provider-neutral OIDC verification, and Auth0/PKCE browser integration are merged with protected CI evidence. Resource-safety implementation is the current increment. The controlled-pilot release gate is not yet satisfied: Auth0-hosted identity evidence, full-surface isolation, deployment, secrets, recovery, operations, supply-chain release artifacts, performance, and usability acceptance remain.
