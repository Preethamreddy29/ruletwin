# Pilot OIDC Foundation Validation

**Date:** 2026-10-25

**Branch:** `codex/pilot-oidc-foundation`

**Baseline:** `main` at `257e604`

**Status:** Local foundation evidence complete; provider and protected clean-runner evidence pending

## Implemented scope

- Provider-neutral RS256 access-token verification.
- Exact issuer and audience validation.
- Required expiry, issued-at, subject, and configurable tenant UUID claim.
- Maximum accepted token lifetime.
- Bounded JWKS parsing, caching, controlled refresh, and same-key-ID rotation recovery.
- Nullable, unique OIDC subject mapping on existing users.
- PostgreSQL-resolved tenant memberships and roles; provider role claims are ignored.
- Generic authenticated session endpoint.
- Development token/persona endpoints disabled outside local development authentication.

## Validation results

| Validation | Result |
|---|---|
| Python formatting, lint and strict type checking | Passed |
| OpenAPI validation | Passed; 12 paths, 12 operations, 125 references |
| Repository secret scan | Passed |
| Migration upgrade/downgrade/forward cycle | Passed |
| Alembic schema drift check | Passed; no new operations detected |
| Full Python suite in Linux container | Passed; 58 tests |
| Python coverage | Passed; 90.46%, above the 80% gate |
| Web formatting, lint, type checking and production build | Passed |
| Web component suite | Passed; 3 tests and 88.31% statement coverage |
| Chromium critical workflows | Passed; allow and block flows |
| Docker image build and core stack startup | Passed; API and PostgreSQL healthy |

## Security cases covered

- Valid OIDC token establishes the provisioned database user, tenant, and role.
- Wrong issuer, audience, signature, expiry, excessive lifetime, malformed tenant, empty subject, unsupported algorithm, and unavailable/invalid JWKS fail closed.
- Cached signing keys avoid a network call per request.
- Signing-key rotation refreshes the cache and accepts the new valid key.
- Unknown subjects and wrong-tenant memberships return equivalent non-enumerating responses.
- Staging configuration rejects development authentication, missing OIDC settings, and non-HTTPS issuer/JWKS URLs.

## Remaining PILOT-01 evidence

- Select and configure the external OIDC provider.
- Register the browser client and API audience.
- Implement and test authorization-code with PKCE login and provider logout.
- Provision the approved pilot subjects and tenant-role assignments.
- Run a provider-hosted invalid-token and key-rotation rehearsal.
- Record deployed issuer, audience, JWKS endpoint, redirect/logout URLs, and secret-store references without recording secrets.

This branch advances PILOT-01 but does not close it and does not authorize an externally hosted pilot.
