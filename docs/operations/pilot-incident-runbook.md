# Pilot Operations and Incident Runbook

## Scope and safety boundary

This runbook supports the invitation-only synthetic-data pilot. It does not establish a production SLA, on-call rotation, hosted log archive, or automated paging service. Prometheus evaluates alerts locally; an approved hosted alert receiver and escalation owner are still required before external pilot deployment.

Never copy access tokens, database credentials, tenant payloads, or exported evidence into an incident ticket or chat. Use correlation IDs, timestamps, service names, alert names, and immutable object identifiers only where access policy permits.

## First response

1. Record the alert name, start time, environment, deployed commit, and image digest.
2. Stop new pilot demonstrations if an alert is critical or tenant isolation is uncertain.
3. Check service state with `docker compose --profile full ps`.
4. Check API readiness at `/health/ready` and Prometheus target health at **Status → Targets**.
5. Inspect bounded recent logs with `docker compose --profile full logs --tail 200 api worker postgres`.
6. Search logs by the correlation or trace ID from the failed request. Do not search by or expose payload contents.
7. Preserve the evidence before restarting a service. Do not delete volumes or manually rewrite business/audit rows during response.

## API unavailable

Alert: `RuleTwinApiUnavailable`

1. Check whether `api`, `postgres`, `migrate`, and `seed` are healthy or completed as expected.
2. Inspect API startup logs for configuration validation, authentication configuration, migration, or database connection failures.
3. Confirm `/health/live`; if it succeeds while `/health/ready` fails, follow the database procedure below.
4. If the deployed image repeatedly fails to start, stop pilot traffic and roll back to the last recorded healthy immutable image. Do not rebuild an image in place.
5. After recovery, require liveness, readiness, metrics, and the pilot smoke workflow to pass before resuming.

## Operational snapshot or database failure

Alerts: `RuleTwinOperationalSnapshotFailed`, `RuleTwinOperationalSnapshotStale`

1. Check `/health/ready` and the `postgres` health state.
2. Inspect API and PostgreSQL logs around the alert start time.
3. Confirm that the application role can connect and read the operational tables without changing its grants.
4. If PostgreSQL is unavailable, stop pilot writes and follow [`pilot-deployment-recovery.md`](pilot-deployment-recovery.md). Do not restore over the active database without an isolated fingerprint check and owner approval.
5. Resolve the cause before clearing the incident; a reachable `/metrics` endpoint alone is not proof that the database snapshot works.

## Ready work is stalled

Alert: `RuleTwinOutboxBacklogStalled`

1. Check that the worker container is running and its logs contain recent `worker_heartbeat` or processing events.
2. Inspect `ruletwin_outbox_ready_events`, `ruletwin_outbox_leased_events`, and `ruletwin_outbox_oldest_ready_age_seconds` in Prometheus.
3. Look for `outbox_event_processing_failed` using its event ID as the correlation/trace ID.
4. Restart only the worker if it is unhealthy. The lease/retry design permits safe reclamation after the lease expires.
5. Confirm the oldest-ready age returns below the alert threshold and that the affected simulation reaches a terminal state.

## Permanent outbox failure

Alert: `RuleTwinOutboxPermanentFailure`

1. Stop demonstrations that depend on the affected simulation.
2. Locate the failure by worker correlation ID and record the bounded error category without copying sensitive content.
3. Do not set the event back to `pending` manually. A controlled replay or repair procedure must preserve idempotency and audit evidence and requires engineering approval.
4. Correct the underlying defect, exercise the recovery in a non-pilot environment, and attach test evidence before any replay.
5. The alert remains active while failed rows exist; closure requires an approved disposition, not merely silencing the alert.

## Stale simulation run

Alert: `RuleTwinSimulationRunStale`

1. Compare worker logs, active leases, and the affected simulation status.
2. Check whether the worker was terminated during execution or exceeded the bounded execution window.
3. Allow the lease to expire and the worker to reclaim the event; do not create a duplicate simulation request.
4. Confirm the recovery produces one terminal simulation result and no duplicate evidence tuple.
5. Escalate if the stale count remains non-zero after worker recovery.

## Repeated API server errors

Alert: `RuleTwinElevatedServerErrors`

1. Group failures by route, status, correlation ID, and deployment version.
2. Check database readiness and recent API exceptions.
3. Reproduce with synthetic data only. Validate that authorization failures remain non-enumerating and are not converted into `500` responses.
4. Stop the affected workflow if errors can create ambiguous state or incomplete evidence.

## High API latency

Alert: `RuleTwinHighApiLatency`

1. Compare request duration, request volume, queue age, PostgreSQL health, and host capacity.
2. Identify the slow route from the bounded `method` and route-template labels; never add tenant or object identifiers as metric labels.
3. Preserve isolation, deterministic execution, and fail-closed decisions even if the pilot flow becomes slow.
4. Record the reference machine and data profile before changing a threshold or claiming a performance result.

## Recovery verification and closure

An incident may close only when:

- the triggering expression is healthy for at least its configured `for` duration;
- API liveness, readiness, and metrics are successful;
- no unprocessed or duplicate evidence remains for the affected workflow;
- the critical synthetic pilot workflow passes;
- the cause, actions, deployed version, and validation evidence are recorded; and
- any manual data repair or alert silence has an explicit owner approval.

## Alert smoke rehearsal

Before a hosted pilot, perform these tests in an isolated synthetic environment and save timestamps/screenshots or exported Prometheus API results:

1. Stop the API long enough to activate `RuleTwinApiUnavailable`, then restore it.
2. Block the API database connection long enough to activate the operational snapshot alert, then restore it.
3. Stop the worker, enqueue synthetic work, observe the stalled-backlog alert, then restart the worker and prove recovery.
4. Generate three controlled synthetic `5xx` responses or use an isolated test metric source; do not introduce a production defect.
5. Confirm every alert includes the expected severity, service, summary, and runbook annotation.
6. Confirm the selected alert receiver delivers and resolves notifications to the approved owner.

The repository can validate rule syntax and local Prometheus evaluation, but notification delivery and operator response require the selected hosted environment and people.
