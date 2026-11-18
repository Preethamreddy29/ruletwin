# Pilot Performance Validation

**Date:** 2026-11-18

**Scope:** Repository mechanism and local reference evidence for PILOT-09

**Branch:** `codex/pilot-performance-evidence`

## Implemented evidence

- `scripts/performance.py` creates deterministic one-event and 10,000-event synthetic data sets through the tenant-scoped API.
- API acknowledgement latency is recorded independently from worker execution.
- Repeat replay samples record end-to-end duration and must produce one identical result checksum.
- Reports bind raw samples, data checksums, machine profile, measurement time, and exact Git commit.
- Pull-request smoke evidence is part of the protected container check.
- `.github/workflows/performance-evidence.yml` provides the main-only 90-day reference artifact.

## Local reference result

| Item | Result |
|---|---|
| Commit | `d9b1fa9d8fc68d81a4fcff8d5e9f3c2a5823d32e` |
| Named profile | `sunny-windows-docker-reference-v1` |
| Machine | Windows 11 / Docker Desktop / 12 logical CPUs |
| Acceptance samples | 30 one-event simulation acknowledgements |
| Acceptance P95 | 87.457 ms; passed the 750 ms target |
| Acceptance range | 15.808–89.852 ms |
| Replay samples | Three independent 10,000-event simulations |
| Replay durations | 8.894 s, 8.409 s, and 8.695 s |
| Replay determinism | Passed; all result checksums identical |

## Exit assessment

The repository mechanism and named local baseline pass. PILOT-09 closes only after the branch's protected workflow and the merged `main` performance-evidence workflow pass with retained artifacts. The measurements do not establish a production SLA, hosted capacity, three-tenant concurrency, or the Phase 1 100,000-event scale hypothesis.
