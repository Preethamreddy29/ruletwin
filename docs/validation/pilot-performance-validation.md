# Pilot Performance Validation

**Date:** 2026-11-18

**Scope:** Closed repository and reference evidence for PILOT-09

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

## Protected and main evidence

- PR #32 passed all five protected checks and merged as `67006a9e269bdc8f918759c836645b80eb0ac47e`.
- Main workflow run `44353040583` passed on the merged commit.
- Artifact `ruletwin-performance-67006a9e269bdc8f918759c836645b80eb0ac47e` is retained until 2027-02-16.
- The GitHub runner reported 4 CPUs, 30 acknowledgement samples at 8.199 ms P95, and three deterministic 10,000-event replays in 4.488–4.790 seconds.

## Exit assessment

PILOT-09 is closed. The named local result and independent protected/main clean-runner results pass with retained raw evidence. These measurements do not establish a production SLA, hosted capacity, three-tenant concurrency, or the Phase 1 100,000-event scale hypothesis.
