# Pilot Operations Baseline Validation

## Scope

This increment establishes the executable PILOT-07 operations baseline. It extends the existing structured logs, correlation IDs, readiness probes, and HTTP metrics with database-backed queue/worker signals, actionable Prometheus alert rules, configuration validation, and an incident runbook.

## Implemented signals

- Operational snapshot success and last-success timestamp.
- Database reachability during the operational snapshot.
- Ready, delayed, actively leased, and permanently failed outbox counts.
- Age of the oldest ready outbox event.
- Running simulation and stale simulation-run counts.
- Existing bounded HTTP request count and duration metrics.

Metric labels contain no tenant, user, token, object, or payload values. The database-backed snapshot is intentionally aggregate across the pilot deployment.

## Implemented alerts

- API scrape unavailable.
- Database-backed operational snapshot failed or stale.
- Ready outbox work stalled.
- Permanent outbox failure.
- Stale simulation run.
- Repeated API server errors.
- High aggregate API latency.

Each alert declares severity, service ownership, a concise description, and a matching runbook section. Prometheus rule/config syntax is checked by `promtool` in the container CI job.

## Failure behavior

If the database-backed snapshot fails or times out, `/metrics` remains scrapeable and publishes failure gauges. Previously collected queue values are not rewritten to zero, which avoids presenting a failed observation as an empty queue. API readiness remains an independent database probe.

## Local validation — 2026-11-08

- Ruff format/check: passed for the Python source and tests.
- Mypy strict type check: passed for 28 source files.
- OpenAPI validation: passed with 13 paths, 13 operations, and 136 resolved references.
- Repository secret scan: passed.
- Reversible migration and schema-drift cycle: passed.
- Python suite: 71 passed with 89.41% total coverage, including PostgreSQL-backed snapshot coverage.
- Web lint and type check: passed after synchronizing the existing lockfile dependencies.
- Web component suite: 8 passed with 84.21% statement coverage.
- Web production build: passed.
- Compose full-profile configuration: passed.
- Prometheus `promtool check config`: passed; one rule file and eight alert rules loaded.
- Deterministic `promtool test rules`: passed for all eight alert firing paths and their labels/annotations.
- Full local stack build/start: passed; API and PostgreSQL healthy, web/worker/Prometheus running.
- Live metrics smoke: snapshot/database success `1`, all queue/stale-run gauges `0` in the idle seeded stack.
- Live Prometheus smoke: API target `up`, one rule group with eight rules, and no recent API/worker/Prometheus error log match.

The repository-wide PowerShell check reached the web formatting step after all Python and database checks passed. That formatting check reports the existing CRLF checkout of eight unchanged web files on Windows; no unrelated normalization was included in this increment. The protected Linux workflow remains the authoritative clean-runner formatting gate.

## Remaining PILOT-07 evidence

The local implementation and alert-rule smoke baseline is complete, but this does not close PILOT-07. The following require the selected hosted environment and owner decisions:

- centralized log shipping, access control, retention, and redaction evidence;
- an approved Alertmanager or hosted notification receiver;
- delivered/firing/resolved notification evidence for each critical alert path;
- a timed operator-led incident rehearsal; and
- approved availability, support, escalation, and retention ownership.
