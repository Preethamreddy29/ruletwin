# Security Policy

## Supported versions

RuleTwin is pre-release. Only the latest commit on `main` receives security fixes.

## Reporting

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature for this repository. Include reproduction steps, affected commit, impact and any proposed mitigation.

Do not include real customer, employer, credential or production data. RuleTwin development uses synthetic data only.

## Current limitations

The application is not production-ready. Development mode uses short-lived local tokens and synthetic identities and must remain disabled outside local environments. The controlled-pilot OIDC implementation validates provider issuer, audience, signature, expiry, maximum lifetime, tenant context, and signing-key rotation while resolving users and roles from PostgreSQL; the browser includes an Auth0-compatible authorization-code/PKCE login/logout flow. A hosted provider has not yet been configured or validated. Authorization evidence covers the implemented rounding workflow, audit list, evidence export, and two synthetic tenants; artifacts, webhooks, operational telemetry isolation, general request-rate controls, and the remaining controlled-pilot matrix remain future work.
