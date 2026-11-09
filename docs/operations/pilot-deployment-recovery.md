# Pilot Deployment, Secrets, and Recovery Runbook

## Purpose and boundary

This runbook deploys RuleTwin as an invitation-only, synthetic-data pilot. It does not authorize real customer data, public signup, a production SLA, or a claim of general production readiness. The hosted environment must use OIDC authentication and immutable images; development identities are not supported by the pilot topology.

The repository provides the repeatable deployment and recovery mechanism. PILOT-03, PILOT-04, and PILOT-05 close only after the selected host supplies the recorded image digests, HTTPS smoke evidence, secret-store configuration, scheduled-backup evidence, and a timed restore rehearsal.

## Deployment topology

[`deploy/pilot/compose.yaml`](../../deploy/pilot/compose.yaml) starts:

- PostgreSQL and the migration, seed, API, and worker processes on an internal backend network;
- the API, web application, and Prometheus on an internal frontend network; and
- a Caddy HTTPS gateway as the only host-exposed service.

All deployable images must be referenced by `@sha256` digest. The migration must complete before the deterministic synthetic seed, and the seed must complete before the API and worker start. Runtime application containers are read-only, drop Linux capabilities, and enable `no-new-privileges`.

## Required external decisions and services

Before a hosted deployment, the owner must record:

1. hosting provider, region, budget, and operator access;
2. pilot hostname and ownership of its TLS certificate;
3. Auth0 tenant, client, API audience, tenant claim, and invited identities;
4. provider secret store and the identity allowed to read each RuleTwin secret;
5. backup storage, encryption, retention, acceptable RPO/RTO, and deletion owner; and
6. support window, alert receiver, and incident owner.

Keep the host private or invitation-only until every controlled-pilot gate passes.

## Build immutable images

Build the API image from `apps/api/Dockerfile`. Build the web image from `apps/web/Dockerfile` with the approved OIDC values supplied as build arguments:

```text
VITE_RULETWIN_AUTH_MODE=oidc
VITE_RULETWIN_OIDC_AUTHORITY=<exact Auth0 issuer>
VITE_RULETWIN_OIDC_AUDIENCE=<exact RuleTwin API audience>
VITE_RULETWIN_OIDC_CLIENT_ID=<SPA client ID>
VITE_RULETWIN_OIDC_REDIRECT_URI=https://<pilot-host>/callback
VITE_RULETWIN_OIDC_POST_LOGOUT_REDIRECT_URI=https://<pilot-host>/
```

Push versioned images to the approved registry, resolve every image to its registry digest, scan those exact digests, and place the digest references in a release environment file outside Git. Never deploy a mutable tag such as `latest`.

## Prepare external files

Copy [`deploy/pilot/release.env.example`](../../deploy/pilot/release.env.example) outside the repository and replace every example. The file contains public deployment configuration and paths only; it must not contain credential values.

The paths must be absolute and point to files injected by the provider secret store or protected by host access controls:

| File | Content |
|---|---|
| PostgreSQL administrator password | Random administrator credential |
| PostgreSQL application password | Separate random least-privilege credential |
| Administrator database URL | `postgresql+psycopg://ruletwin_admin:<credential>@postgres:5432/ruletwin` |
| Application database URL | `postgresql+psycopg://ruletwin_app:<credential>@postgres:5432/ruletwin` |
| TLS certificate and private key | Certificate for the exact pilot hostname |

The secret values must never be committed, placed in an image layer, printed in a deployment record, or pasted into an incident ticket. Grant read access only to the deployment identity and the containers that require each file.

## Validate and deploy

From the repository root, validate without displaying secret values:

```powershell
.\.venv\Scripts\python.exe scripts\pilot.py `
  --env-file C:\secure\ruletwin\release.env `
  --compose-file deploy\pilot\compose.yaml `
  validate-config
```

Deploy the exact reviewed configuration:

```powershell
docker compose `
  --env-file C:\secure\ruletwin\release.env `
  -f deploy\pilot\compose.yaml `
  up --detach
```

After every service is healthy, capture the required record:

```powershell
.\.venv\Scripts\python.exe scripts\pilot.py `
  --env-file C:\secure\ruletwin\release.env `
  --compose-file deploy\pilot\compose.yaml `
  deployment-record `
  --ca-file C:\secure\ruletwin\trusted-ca.pem
```

The JSON record contains the Git commit, declared image digests, applied migration, HTTPS smoke results, and service states. Store it in the restricted release-evidence location; `artifacts/` is intentionally ignored by Git.

## Back up and verify

Schedule the following command with the provider scheduler or an operator-owned scheduled task. Store the dump and manifest in encrypted storage separate from the deployment host, and monitor both command failure and absence of a fresh manifest.

```powershell
.\.venv\Scripts\python.exe scripts\pilot.py `
  --env-file C:\secure\ruletwin\release.env `
  --compose-file deploy\pilot\compose.yaml `
  backup --output D:\protected\ruletwin\backups
```

Each manifest records the backup checksum, size, duration, source commit, migration, table counts, and aggregate evidence checksums. A manifest is not a successful recovery test by itself.

## Isolated restore rehearsal

Run this against an isolated pilot environment, never by overwriting the active database:

```powershell
.\.venv\Scripts\python.exe scripts\pilot.py `
  --env-file C:\secure\ruletwin\release.env `
  --compose-file deploy\pilot\compose.yaml `
  restore-rehearsal `
  --backup D:\protected\ruletwin\backups\<backup>.dump `
  --manifest D:\protected\ruletwin\backups\<backup>.manifest.json `
  --output D:\protected\ruletwin\recovery-evidence `
  --restart-worker
```

The command verifies the dump checksum, restores into a randomly named temporary database, compares migration/table/evidence fingerprints, proves the worker returns after restart, records observed restore time and backup age, and removes the temporary database. Preserve the JSON result with the release evidence.

The owner must compare the measured values with the approved RPO/RTO. Until those targets exist and a hosted rehearsal passes, PILOT-05 remains open.

## Release and migration rollback

1. Stop new pilot activity and preserve logs, the failed deployment record, and database evidence.
2. Identify the last approved release environment file containing the prior immutable image digests.
3. If the failed release did not change the database schema, deploy the prior digests and rerun readiness and the critical synthetic workflow.
4. If the schema changed, do not run an ad-hoc downgrade against the active database. Restore the verified pre-deployment backup into an isolated database, validate its fingerprint and application compatibility, then switch only with owner approval.
5. The clean migration downgrade/upgrade test in `scripts/test_migrations.py` proves migration reversibility during CI; it does not replace a release-specific data-preserving restore rehearsal.
6. Record the final commit, image digests, migration, backup/restore identifiers, decision owner, and post-recovery smoke results.

## Secret-redaction check

Before pilot acceptance, plant a unique non-credential marker in the isolated secret store, exercise startup and expected failure paths, export bounded API/worker/gateway logs, and prove the marker is absent. Do not use a real credential as the planted marker. Save only the scan result, timestamps, services searched, and marker hash—not the marker value.

## Exit checklist

- [ ] Exact hosted commit and all image digests recorded.
- [ ] Automated migration and HTTPS smoke record passed.
- [ ] Provider secret-store configuration and access policy recorded.
- [ ] Planted-secret log-redaction scan passed.
- [ ] Encrypted scheduled backup and freshness alert passed.
- [ ] Isolated restore fingerprint matched.
- [ ] Worker restart passed.
- [ ] Release-specific rollback rehearsal passed.
- [ ] Observed RPO/RTO met owner-approved targets.
- [ ] Synthetic data and invitation-only access confirmed.
