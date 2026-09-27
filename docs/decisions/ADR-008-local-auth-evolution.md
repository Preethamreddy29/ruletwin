# ADR-008: Local JWT/RBAC with OIDC Evolution

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Phase 2 may implement local development identity using signed short-lived JWTs and server-side tenant RBAC behind an identity-provider interface. Production evolution targets standards-based OIDC without changing domain authorization rules.
**Why:** Local reproducibility is required, but authentication mechanics must not be confused with authorization or embedded throughout domain logic.
**Alternatives:** Build a full identity provider; anonymous/local headers; immediate external hosted IdP.
**Consequences:** Keys, token lifecycle, issuer/audience validation and test identities require explicit controls; identity headers alone are never trusted.
**Revisit when:** OIDC integration begins or token/role requirements materially change.
