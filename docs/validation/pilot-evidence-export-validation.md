# Pilot Evidence Export Validation

**Date:** 2026-10-25

**Branch:** `codex/pilot-evidence-export`

**Baseline:** `main` at `bf90277`

**Status:** Local implementation evidence complete; pull-request clean-runner evidence pending

## Scope

This increment implements download of a deterministic JSON evidence bundle for a completed simulation. The bundle binds the simulation to immutable rule, dataset, result, impact, risk, approval, and release-gate evidence through identifiers and checksums. It does not implement evidence import/reproduction, artifact storage, hosted identity, or hosted pilot operations.

## Authorization evidence

| Case | Expected | Result |
|---|---|---|
| Same-tenant QA reviewer exports completed evidence | Allow | Passed |
| Same-tenant release approver or auditor is assigned the export permission | Allow | Covered by the server role dependency and authorization matrix |
| Analyst attempts export | Non-enumerating denial | Passed |
| Authorized role uses another tenant's simulation identifier | Same 404 as absent object | Passed |
| Repeated export of unchanged evidence | Identical JSON and export checksum | Passed |
| Successful export | Append `evidence.exported` audit event | Passed |

## Validation results

| Validation | Result |
|---|---|
| Python formatting | Passed; 39 files already formatted |
| Python lint | Passed |
| Python type checking | Passed; no issues in 26 source files |
| Full Python test suite in Linux container | Passed; 46 tests |
| Python coverage | Passed; 93.56%, above the 80% gate |
| OpenAPI reference validation | Passed; 11 paths, 11 operations, 120 references |
| Web lint and type checking | Passed |
| Web component tests | Passed; 3 tests |
| Chromium critical workflows | Passed; 2 workflows, including real JSON download and content checks |
| Web production build | Passed |

## Remaining evidence

- Protected GitHub pull-request checks are required before merge.
- An operator rehearsal remains desirable usability evidence; the API authorization, web behavior, and real browser download have automated coverage.
- Evidence reproduction remains disabled and is not claimed by this increment.
- This increment does not satisfy the complete controlled-pilot release gate.
