# Auth0 Controlled-Pilot Configuration

This runbook connects RuleTwin's provider-neutral OIDC boundary to an invitation-only Auth0 tenant. It does not authorize public signup, real customer data, or production use.

## Security boundary

- The browser uses authorization code with PKCE. It never receives or stores a client secret.
- Auth0 establishes the external subject and signed access token.
- RuleTwin validates RS256 signature, exact issuer and audience, lifetime, tenant claim and key rotation.
- RuleTwin ignores provider roles. PostgreSQL remains authoritative for tenant membership and role.
- Access is denied until an operator maps the exact Auth0 `sub` to one pre-seeded pilot identity.
- The access token is kept in session storage by the OIDC client and is cleared with the browser session or provider logout.

## 1. Create the Auth0 API

Create one custom API in the selected Auth0 tenant:

- **Name:** `RuleTwin Pilot API`
- **Identifier / audience:** a stable URI owned for this pilot, for example `https://pilot.ruletwin.example/api`
- **Signing algorithm:** `RS256`
- **Access-token lifetime:** no more than 3600 seconds

Record the identifier exactly. RuleTwin rejects a token issued for any other audience.

## 2. Create the browser application

Create a **Single Page Application** and configure only the actual pilot origin:

- Allowed callback URL: `https://<pilot-host>/auth/callback`
- Allowed logout URL: `https://<pilot-host>/`
- Allowed web origin: `https://<pilot-host>`
- Authorization flow: authorization code with PKCE

For local provider testing, add `http://localhost:8080/auth/callback`, `http://localhost:8080/`, and `http://localhost:8080` as separate temporary entries. Remove them from the hosted pilot application if local testing uses a different Auth0 application.

Do not create or place an Auth0 client secret in the SPA configuration. The client ID and API audience are public identifiers, not secrets.

## 3. Add the tenant claim

Create a Post Login Action attached to the pilot login flow. Store each invited user's assigned RuleTwin tenant UUID in Auth0 `app_metadata.ruletwin_tenant_id`. Emit it as a namespaced access-token claim:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const tenantId = event.user.app_metadata?.ruletwin_tenant_id;
  if (!tenantId) {
    api.access.deny("RuleTwin pilot membership is not configured.");
    return;
  }
  api.accessToken.setCustomClaim(
    "https://ruletwin.example/claims/tenant_id",
    tenantId,
  );
};
```

The action must not emit RuleTwin authorization roles. Roles are loaded from PostgreSQL after the token has been verified.

## 4. Configure RuleTwin

Backend configuration:

```text
RULETWIN_ENVIRONMENT=staging
RULETWIN_AUTH_MODE=oidc
RULETWIN_OIDC_ISSUER=https://<auth0-domain>/
RULETWIN_OIDC_AUDIENCE=https://pilot.ruletwin.example/api
RULETWIN_OIDC_JWKS_URL=https://<auth0-domain>/.well-known/jwks.json
RULETWIN_OIDC_TENANT_CLAIM=https://ruletwin.example/claims/tenant_id
RULETWIN_OIDC_MAX_TOKEN_LIFETIME_SECONDS=3600
```

Public browser build configuration:

```text
VITE_RULETWIN_AUTH_MODE=oidc
VITE_RULETWIN_OIDC_AUTHORITY=https://<auth0-domain>/
VITE_RULETWIN_OIDC_AUDIENCE=https://pilot.ruletwin.example/api
VITE_RULETWIN_OIDC_CLIENT_ID=<spa-client-id>
VITE_RULETWIN_OIDC_REDIRECT_URI=https://<pilot-host>/auth/callback
VITE_RULETWIN_OIDC_POST_LOGOUT_REDIRECT_URI=https://<pilot-host>/
```

The issuer, authority and JWKS host must be the selected Auth0 tenant or approved custom domain. Never mix domains from different tenants.

## 5. Provision invited identities

Seed the synthetic pilot identities first. For each invited Auth0 user, obtain the exact `sub` from a validated token or the Auth0 user record and provide it through a temporary environment variable so it does not enter shell history:

```powershell
$env:RULETWIN_PROVISION_OIDC_SUBJECT = '<exact-auth0-sub>'
ruletwin-provision-oidc `
  --identity-key novabill-analyst `
  --approved-by-identity-key novabill-approver
Remove-Item Env:RULETWIN_PROVISION_OIDC_SUBJECT
```

Repeat with a distinct invited Auth0 subject for every required pilot role. One subject cannot be mapped to more than one identity. Replacing an existing mapping fails closed. Provisioning records the approving release persona and only a SHA-256 digest of the subject in the audit trail.

## 6. Required provider evidence

PILOT-01 remains open until all of the following are recorded without secrets:

1. Successful browser login and logout from the deployed pilot origin.
2. Successful `GET /v1/session` and `GET /v1/scenarios` using the Auth0 access token.
3. Wrong issuer, audience, signature, expiry, lifetime and tenant claim are rejected.
4. Unknown subject and wrong-tenant membership return equivalent non-enumerating responses.
5. Auth0 signing-key rotation is rehearsed or evidenced with a controlled provider key change.
6. Development identity endpoints return `404` in the hosted environment.
7. Issuer, audience, JWKS endpoint, callback/logout URLs, deployed commit and secret-store references are recorded.

Do not record access tokens, refresh tokens, client secrets, database passwords, user passwords or raw provider subjects in repository evidence.
