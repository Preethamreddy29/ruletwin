# Phase 4A Validation Evidence

**Date:** 2026-10-24  
**Original branch:** `codex/phase4a-multitenant-authorization`  
**Phase 3 base:** `5a13a3e`  
**Merged result:** PR #18 at `cffdb30`  
**Current verified main:** `d64275f`

## Automated results

| Validation | Result |
|---|---|
| Ruff format/lint and strict mypy | Pass |
| OpenAPI reference validation | Pass |
| Repository secret scan | Pass |
| Python dependency vulnerability audit | Pass — no known vulnerabilities in the validated run |
| Bandit static security scan | Pass — no findings in the validated run |
| PostgreSQL migration downgrade/upgrade and Alembic drift | Pass — zero drift |
| Python tests | Pass — 46 |
| Python measured coverage | Pass — 93.56% |
| Web component tests | Pass — 3 |
| Web measured statement coverage | Pass — 88.14% |
| TypeScript and production build | Pass |
| Compose image build and Phase 3-volume upgrade seed | Pass |
| Playwright Chromium multi-persona workflow | Pass — allow, block, and cross-tenant denial paths |

## Authorization evidence

- Invalid signature, issuer, audience, expiry, subject, and missing-token cases fail closed.
- Tokens carry subject and active tenant; roles and active membership are loaded from PostgreSQL.
- Same-tenant actions succeed only for the permitted role.
- Wrong-role and absent-membership actions are denied.
- Brightline cannot read the NovaBill simulation, and the response is indistinguishable from a random absent object.
- Audit-event reads are limited to the authenticated tenant.
- Existing stale-evidence, substituted-evidence, self-approval, idempotency, and worker-recovery cases remain covered.

## Live evidence

- API reports `0.3.0-alpha-authz`.
- Seed contains two synthetic tenants and eight active single-role memberships.
- Five simulations completed during final verification.
- Two allow and two block release gates were recorded.
- Zero outbox events remained unprocessed.
- API and worker logs contained no application errors during the verified flow.

## Clean-runner evidence

- PR #18 validation workflow passed all five required checks before merge.
- The post-merge main workflow passed all five required checks at `cffdb30`.
- Main CI passed all five required checks again at `d64275f` after the Gitleaks action upgrade.

This closes the previously pending clean-runner evidence item. These results support Phase 4A only and do not prove the controlled-pilot gates in [`docs/pilot-readiness-plan.md`](../pilot-readiness-plan.md).
