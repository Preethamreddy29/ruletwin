# Phase 4A Authorization Demo Guide

## Purpose

Demonstrate that RuleTwin now enforces an executable tenant and role boundary while preserving the deterministic Phase 3 workflow. All identities and data are fictional and development-only.

## Start

From the repository root:

```powershell
./scripts/dev.ps1 up
```

Open `http://localhost:8080`. Confirm the page identifies itself as **Phase 4A · executable tenant isolation**.

## Demonstration flow

1. Select **NovaBill Analyst**.
2. Create the proposed rounding rule and run the simulation.
3. Inspect the deterministic impact result.
4. Switch to **Brightline QA Reviewer**. Show that the isolation panel cannot read the NovaBill simulation and reports the same non-enumerating result used for an absent object.
5. Switch to **NovaBill QA Reviewer** and submit the review.
6. Switch to **NovaBill Release Approver** and evaluate the release gate.
7. Switch to **NovaBill Auditor** and select **Inspect tenant audit trail**. Show that only NovaBill audit evidence is returned.
8. Repeat with the alternate rounding increment to demonstrate both allow and block risk outcomes.

## Architecture narration

- The browser obtains a short-lived development token containing only the user subject and active tenant.
- The API validates signature, issuer, audience, timestamps, and identifiers.
- The API loads active membership and roles from PostgreSQL; it does not trust a role selected or claimed by the browser.
- Every implemented resource lookup is scoped to the authenticated tenant.
- Cross-tenant and random identifiers produce the same response so the API does not reveal whether another tenant owns an object.
- The reviewer and release approver are separate identities, and approval remains bound to the immutable simulation evidence checksum.

## Honest limitations

- The token issuer and persona selector are local demonstration infrastructure, not production OIDC.
- Phase 4A covers the implemented rounding workflow and audit listing, not future exports, artifacts, webhooks, metrics, or operator tools.
- Full Phase 4 still requires five rule families, dependency analysis, richer impact dimensions, evidence export, pagination, and expanded usability work.
