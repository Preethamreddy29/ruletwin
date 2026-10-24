# Security Policy

## Supported versions

RuleTwin is pre-release. Only the latest commit on `main` receives security fixes.

## Reporting

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature for this repository. Include reproduction steps, affected commit, impact and any proposed mitigation.

Do not include real customer, employer, credential or production data. RuleTwin development uses synthetic data only.

## Current limitations

The application is not production-ready. Phase 4A uses short-lived signed tokens and server-resolved tenant RBAC, but its token-minting endpoint and identities are explicitly development-only. It is not an external identity provider or production OIDC integration. Authorization evidence currently covers the implemented rounding workflow, audit list, and two synthetic tenants; exports, artifacts, webhooks, operational telemetry isolation, rate limits, and the full Phase 4/5 matrix remain future work.
