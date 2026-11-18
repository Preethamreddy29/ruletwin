# Pilot Supply-Chain Validation

**Date:** 2026-11-10

**Scope:** Repository implementation evidence for PILOT-08

**Branch:** `codex/pilot-supply-chain-release`

## Implemented controls

- API and web container SBOM generation in SPDX JSON format.
- API and web high/critical vulnerability reports and fail-closed gates.
- Immutable local image-ID capture for the exact reviewed commit.
- Checksum- and size-bound manifest generation with path-containment and tamper verification.
- Per-PR 30-day evidence upload and main-branch 90-day preflight evidence upload.
- Main-only, preflight-only workflow guard that prevents premature official pilot release creation.

## Local validation

| Check | Result |
|---|---|
| Release-evidence unit tests | Passed; 8 focused manifest, validation, path-containment, and tamper tests |
| Python formatting and lint | Passed across 110 files |
| Python typing and complete database-backed suite | Passed; 28 typed source files, reversible migration cycle with zero drift, 83 tests, 89.01% coverage |
| Web lint, typing, tests, and build | Passed; 8 tests, 84.21% statement coverage, successful production build |
| Workflow syntax, OpenAPI, and repository secret scan | Passed; 13 paths, 13 operations, 136 references |
| API/web image build | Passed; both runtime images built successfully and retained non-root users |
| Local SPDX SBOM and Trivy rehearsal | Passed; reports generated for both images with zero unfixed high/critical findings after upgrading the web runtime base |
| Checksum-bound manifest build and verification | Passed for six evidence files; tamper verification is covered by tests |

## Exit assessment

PILOT-08 is closed. PR #31 passed all five protected checks and merged as `d9b1fa9`. Main preflight run `44348823858` passed for `0.4.0-pilot.preflight.1`; its 539,754-byte artifact `ruletwin-0.4.0-pilot.preflight.1-d9b1fa9d8fc68d81a4fcff8d5e9f3c2a5823d32e` is retained until 2027-02-16. Official `v0.4.0-pilot.1` publication remains blocked until every other controlled-pilot gate passes.
