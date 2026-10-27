# Pilot Auth0 Integration Validation

**Date:** 2026-10-27

**Branch:** `codex/pilot-auth0-integration`

**Baseline:** `codex/pilot-oidc-foundation` at `1a4c240`

**Status:** Implementation validation in progress; provider-hosted evidence pending

## Implemented scope

- Authorization code with PKCE through the maintained `oidc-client-ts` browser client.
- Session-storage state and token handling; no browser client secret.
- Sign-in callback processing and provider logout redirect.
- OIDC and local-development identity modes remain explicitly separate.
- Authenticated `GET /v1/scenarios` returns only the active tenant's synthetic scenario.
- Container build arguments for public browser OIDC configuration.
- Fail-closed invited-subject provisioning with same-tenant release-approver attribution.
- Unique subject binding, immutable replacement behavior and redacted audit metadata.
- Auth0 application, API, namespaced tenant-claim and deployment runbook.

## Local validation

| Validation | Result |
|---|---|
| Web formatting | Passed |
| Web lint | Passed |
| Web type checking | Passed |
| Web component tests | Passed; 8 tests |
| Web coverage | Passed; 84.21% statements, 87.57% branches, 86.48% functions, 86.45% lines |
| Web production build | Passed |
| Python formatting and lint | Passed; 98 files formatted and lint-clean |
| Python type checking | Passed; 27 source files |
| Provisioning unit tests | Passed; 5 tests |
| OpenAPI validation | Passed; 13 paths, 13 operations and 133 references |
| Repository secret scan | Passed |
| Compose configuration | Passed for the `full` profile |
| Integration, migration and browser workflows | Pending Linux-container rerun; Docker Engine was unavailable during the local validation attempt |

## Remaining PILOT-01 evidence

- Merge prerequisite PR #22 and this dependent increment through protected clean-runner CI.
- Create/configure the selected Auth0 tenant, custom API, SPA and Post Login Action.
- Provision distinct approved pilot subjects and record only redacted evidence.
- Run deployed browser login/logout and active-session/scenario checks.
- Exercise provider-hosted invalid-token and signing-key-rotation behavior.
- Record deployed issuer, audience, JWKS URL, callback/logout URLs, commit, image digests and secret-store references without secrets.

This increment must not be described as completed provider integration or pilot readiness until those external checks pass.
