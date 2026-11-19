# Pilot Resource-Safety Evidence

## Purpose

This procedure proves that RuleTwin fails safely when its per-tenant simulation queue is full and that bounded worker timeouts recover through the outbox retry path. It uses synthetic data only and records observed container measurements; it is not a production capacity benchmark.

## Automated profiles

- Pull requests run a bounded five-item smoke profile as part of Compose/container evidence and retain the JSON report for 30 days.
- The main-only `Resource safety evidence` workflow runs the same proof after merge and retains its JSON report for 90 days.
- Each report is bound to the Git commit, named profile, platform, deterministic result checksum, retry outcome, and API/worker container statistics.

## Local run

Start the core stack with a queue limit of 5, a one-second worker timeout, a 0.1-second poll interval, and a one-second retry base. Set `RULETWIN_RESOURCE_DATABASE_URL` to the local application-role database URL, then run:

```powershell
python scripts/resource_safety.py `
  --compose-env-file .env `
  --profile-name local-docker-resource-v1 `
  --saturation-limit 5 `
  --output artifacts/resource-safety/local-report.json
```

The script temporarily stops and starts the worker. A `finally` guard restarts it if an assertion fails. It does not delete application data.

## Required assertions

The evidence is valid only when all of these conditions hold:

1. Exactly the configured number of simulations is accepted while the worker is stopped.
2. The next request fails with HTTP 429 and `queue-capacity-exceeded`.
3. Reusing an accepted idempotency key returns the original simulation identifier.
4. All accepted simulations complete after the worker restarts and their deterministic checksums agree.
5. A database row lock causes the bounded worker execution to record `TimeoutError`.
6. After the lock is released, the same outbox item completes on a later attempt.
7. The report contains the commit, profile, timings, result checksums, final states, and container measurements.

Do not raise limits or suppress an assertion to make the workflow pass. Investigate queue admission, worker logs, outbox state, or container health and repeat the complete profile after a fix.
