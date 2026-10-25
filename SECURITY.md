# Security Policy

## Supported versions

RuleTwin is pre-release. Only the latest commit on `main` receives security fixes.

## Reporting

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature for this repository. Include reproduction steps, affected commit, impact and any proposed mitigation.

Do not include real customer, employer, credential or production data. RuleTwin development uses synthetic data only.

## Current limitations

The application is not production-ready. Development mode uses short-lived local tokens and synthetic identities. The controlled-pilot OIDC foundation validates provider issuer, audience, signature, expiry, maximum lifetime, tenant context, and signing-key rotation, while resolving users and roles from PostgreSQL. It does not yet provide a configured provider or browser login/logout. Authorization evidence covers the implemented rounding workflow, audit list, evidence export, and two synthetic tenants; artifacts, webhooks, operational telemetry isolation, rate limits, and the remaining controlled-pilot matrix remain future work.
