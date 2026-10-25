# ADR-010: OIDC Establishes Identity, PostgreSQL Grants Access

**Status:** Accepted for controlled-pilot implementation (2026-10-25)

**Decision:** A single configured OIDC issuer authenticates pilot users with RS256 access tokens. RuleTwin validates the exact issuer, audience, signature, expiry, issued-at time, bounded token lifetime, signing-key identity, and a signed tenant UUID claim. The immutable provider `sub` maps to nullable `users.oidc_subject`. Tenant membership and all RuleTwin roles continue to come exclusively from PostgreSQL.

**Why:** Provider roles and mutable email addresses are unsuitable authorization authorities for a tenant-sensitive decision system. A stable subject mapping preserves the existing object and role authorization model while allowing the provider to own authentication and key rotation.

**Controls:** Development tokens are permitted only in `dev`/`test`; hosted modes require complete HTTPS OIDC configuration. Algorithms are fixed to RS256. JWKS responses are bounded, cached, and refresh-throttled. Missing keys trigger one controlled refresh. Unknown subjects, missing memberships, wrong tenants, and unauthorized roles fail closed without enumerating identities or objects.

**Alternatives:** Trust provider role claims; map users by email; implement an internal identity provider; accept arbitrary JWT algorithms. These were rejected because they increase privilege drift, account-reassignment, operational, or algorithm-confusion risk.

**Consequences:** Pilot users require explicit subject and membership provisioning. The chosen provider must emit the configured tenant claim. Provider authorization-code/PKCE login, logout, deployment configuration, and key-rotation rehearsal remain necessary before PILOT-01 closes.

**Supersedes:** The production-evolution portion of ADR-008; local development authentication remains as documented there.
