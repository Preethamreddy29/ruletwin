# Pilot Deployment and Recovery Validation

**Date:** 2026-11-10

**Branch:** `codex/pilot-deployment-recovery-foundation`

**Scope:** Local implementation evidence for PILOT-03, PILOT-04, and PILOT-05

## Result

The repository now contains a reproducible HTTPS pilot topology, file-mounted secret support, immutable-image validation, deployment evidence capture, checksum-bound backup creation, isolated restore verification, and worker-restart evidence capture. This is an implementation foundation, not hosted exit evidence.

## Evidence produced

| Check | Result |
|---|---|
| Pilot Compose rendering with required HTTPS, OIDC, digest image, and absolute secret-file inputs | Passed |
| Mutable image and non-HTTPS configuration rejection | Passed by unit test |
| Mounted database/JWT secret loading and ambiguous configuration rejection | Passed by unit test |
| Python formatting | 104 files passed |
| Python lint | Passed |
| Python static typing | 28 source files passed |
| Reversible migration cycle and schema drift check | Passed across all three migrations; no new upgrade operations detected |
| Complete Python suite with PostgreSQL | 75 passed, 89.01% coverage |
| Web lint, static typing, component tests, and production build | Passed; 8 tests and 84.21% statement coverage |
| OpenAPI validation | Passed: 13 paths, 13 operations, 136 references |
| Repository secret scan | Passed |
| Live local backup | Passed: 110,494-byte custom dump with SHA-256 manifest in 0.816 seconds |
| Isolated local restore and worker restart | Passed: fingerprint match, temporary database removed, worker returned; 6.564-second restore |

## Security properties inspected

- Only the HTTPS gateway publishes a host port in the pilot topology.
- Database, API, worker, web, and Prometheus traffic remains on internal Compose networks.
- Runtime application services are read-only, capability-dropped, and use `no-new-privileges`.
- Database credentials are referenced through mounted files, not interpolated into the pilot Compose environment.
- Every deployable image reference must contain a SHA-256 digest.
- The release record excludes secret values.
- Restore verification uses a temporary database and compares migration, row-count, and evidence-checksum fingerprints before removing it.

## Remaining exit evidence

The following cannot be truthfully produced from repository-only validation:

1. hosted commit/image-digest/migration/HTTPS smoke record;
2. provider secret-store access-policy evidence;
3. planted-secret scan across hosted logs and error paths;
4. scheduled encrypted-backup and freshness-monitor evidence;
5. timed hosted restore and release-specific rollback rehearsal;
6. owner-approved backup retention and RPO/RTO targets; and
7. an approved interpretation of local timing; the observed local backup age was 18.913 seconds and is not an owner-approved RPO.

Therefore PILOT-03, PILOT-04, and PILOT-05 are partially satisfied and remain open.
