# Pilot Performance Evidence

## Purpose

Measure RuleTwin's approved synthetic pilot profile without weakening tenant isolation, fail-closed policy, queue limits, worker timeouts, or deterministic evidence. This is a controlled-pilot measurement, not a production SLA.

## Profiles

- Pull requests run a five-sample acknowledgement and one 1,000-event replay smoke profile inside the existing protected container check.
- The manual main-only workflow runs 30 acknowledgement samples and three 10,000-event replays and retains the JSON report for 90 days.
- A named local reference run may be recorded for development comparison, but it does not replace protected clean-runner evidence.

## Run locally

Start the core Docker profile, then run:

```powershell
python scripts/performance.py `
  --profile-name <named-machine-profile> `
  --acceptance-samples 30 `
  --acceptance-p95-target-ms 750 `
  --replay-events 10000 `
  --replay-samples 3 `
  --output artifacts/performance/report.json
```

The script uses only the fictional NovaBill development identity and deterministic generated events. It does not write tokens to the report.

## Evidence contents

The JSON report records the exact Git commit, UTC time, OS/CPU/Python profile, synthetic tenant, dataset seeds/counts/checksums, every acknowledgement sample, nearest-rank P95, every replay duration and result checksum, and pass/fail assertions.

## Interpretation

- Acceptance measures only the API transaction/outbox acknowledgement, not worker execution.
- Replay measures end-to-end time until the worker marks the simulation complete.
- P95 above 750 ms fails the gate.
- Non-identical replay checksums fail the gate.
- No replay latency threshold is promoted from hypothesis until the protected main reference run is reviewed.
- The 100,000-event Phase 1 scale hypothesis remains outside the current 10,000-event pilot limit.
