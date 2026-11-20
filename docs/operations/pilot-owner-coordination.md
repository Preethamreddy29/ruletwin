# Pilot Owner Coordination Record

## Purpose

This record converts the remaining external RuleTwin pilot decisions into a fail-closed, machine-checkable handoff. It contains identifiers and ownership information only. Do not place passwords, client secrets, database URLs, private keys, recovery codes, or access tokens in it.

The repository implementation is complete for the current synthetic pilot surface. A hosted pilot still requires decisions and evidence that only the account, infrastructure, and human operators can supply.

## Prepare the record

1. Copy [`deploy/pilot/owner-decisions.example.json`](../../deploy/pilot/owner-decisions.example.json) to a restricted operating location outside the repository.
2. Complete every blank field using the decisions below.
3. Keep the scope values as `synthetic-only`, `invitation-only`, and `private` or `unlisted`.
4. Record public Auth0 identifiers only. Store every Auth0 secret in the selected secret store.
5. Use distinct invited Auth0 subjects and cover both synthetic tenants and all four pilot roles.
6. Validate the completed record without printing its contents:

```powershell
.\.venv\Scripts\python.exe scripts\pilot.py validate-owner-decisions `
  --decisions-file C:\secure\ruletwin\owner-decisions.json
```

The command returns a non-zero exit code and lists every incomplete decision. It does not deploy anything and does not prove that a named external service is configured correctly.

## Decisions requiring the owner

| Area | Required input | Why automation cannot choose it |
|---|---|---|
| Hosting | Provider, region, budget owner, and operator | Creates cost, account, and operational responsibility |
| Domain | Pilot hostname and TLS owner | Requires control of DNS and certificates |
| Identity | Auth0 tenant, public SPA client ID, API audience, tenant claim, and invited subjects | Requires the owner's Auth0 account and named people |
| Secrets | Secret-store provider, deployment identity, and owner | Requires infrastructure access policy |
| Recovery | Backup storage, retention, RPO, RTO, and owner | Defines business risk and operating cost |
| Operations | Support window, alert receiver, and incident owner | Assigns real human responsibility |
| Acceptance | Named independent operator and rehearsal time | Human observation cannot be manufactured by CI |

## Work that can continue after the record passes

1. Configure Auth0 from [`auth0-pilot.md`](auth0-pilot.md).
2. Build and publish immutable images and configure the host from [`pilot-deployment-recovery.md`](pilot-deployment-recovery.md).
3. Run provider login/logout, invalid-token, and key-rotation evidence.
4. Capture the hosted deployment record and planted-marker log-redaction result.
5. Schedule a backup, rehearse an isolated restore, and compare the measured result with the approved RPO/RTO.
6. Connect alerts to the recorded receiver and rehearse the incident runbook.
7. Complete and sign [`pilot-acceptance-checklist.md`](pilot-acceptance-checklist.md).
8. Run the official release-candidate workflow only after all evidence is retained.

## Gate interpretation

A passing owner-decision validation means the external work has named inputs and owners. It does **not** close PILOT-01, PILOT-03, PILOT-04, PILOT-05, PILOT-07, or the human portion of PILOT-10. Those gates close only with evidence from the configured hosted environment and the signed rehearsal.
