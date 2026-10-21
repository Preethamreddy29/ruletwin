# Phase 3 Demonstration Guide

This guide is the presenter runbook for the RuleTwin first vertical slice. The demonstration uses only the fictional NovaBill tenant and deterministic synthetic data.

## Preflight and predictable startup

From the repository root in PowerShell, start Docker Desktop and run:

```powershell
./scripts/dev.ps1 up
./scripts/dev.ps1 status
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

Open `http://127.0.0.1:8080`. Continue only when the header says **Ready** and the dataset says **100 events · seed 314159**.

Normal startup preserves prior synthetic evidence. For a guaranteed fresh demonstration, use the deliberate reset command:

```powershell
./scripts/dev.ps1 reset
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

`reset` removes only the Compose-managed RuleTwin local volumes, rebuilds the core services, migrates PostgreSQL and reruns the versioned seed. It does not require or permit manual database edits. Do not use it when local RuleTwin evidence must be retained.

## Five-to-seven-minute live script

### 0:00–0:45 — Frame the problem

Say: “A small business-rule change can alter thousands of customer outcomes. RuleTwin compares the current rule with a proposed rule before release and produces evidence a separate approver can review.”

Point out that the tenant, actors and events are synthetic. RuleTwin is a change-impact simulator, not a billing engine or rule generator.

### 0:45–2:15 — Demonstrate the safe path

1. Show the **NovaBill Sandbox** identity and **Ready** status.
2. Select **5 minor units · expected allow**.
3. Click **Run comparison**.
4. While it runs, explain that the API writes the simulation request and outbox record in one transaction, then a recoverable worker leases and executes the job.
5. When evidence appears, show the changed-event count, maximum delta, net delta, result checksum and immutable evidence identifiers.
6. Click **Approve evidence** and show the **allow** release gate.

Say: “The approval is not a loose yes/no. It is bound to this result checksum, dataset, policy, engine and rule versions.”

### 2:15–3:45 — Demonstrate the blocked path

1. Select **10 minor units · expected block**.
2. Click **Run comparison**.
3. Show that the same 100 events are replayed with the same engine and policy.
4. Show the larger maximum delta and **block** policy result.
5. Click **Approve evidence** and show that approval does not override policy: the release gate remains **block**.

Say: “Human review records the evidence decision; it cannot bypass the deterministic risk gate.”

### 3:45–5:15 — Explain determinism and recovery

- Money is represented as integer USD minor units.
- The dataset is versioned and generated from seed `314159`.
- Canonical JSON and SHA-256 checksums bind rules, dataset, policy and results.
- Duplicate simulation requests are idempotent.
- An expired worker lease can be reclaimed; redelivery after a committed result does not create a second result.
- Protected transitions append audit events.

### 5:15–6:30 — Close with the boundary

Say: “This slice proves the architecture with one tenant, one rounding-rule family and bounded synthetic evidence. It deliberately does not claim production authentication, broad multi-tenant authorization, deployment signing or a complete rules portfolio.”

## Architecture and request/data flow

```text
Browser
  -> Nginx web container (/api reverse proxy)
    -> FastAPI
      -> PostgreSQL transaction: simulation + outbox + audit
        -> Worker lease/recovery loop
          -> Pure rounding engine replays baseline and candidate
            -> outcomes + impact + versioned risk decision + checksum
              -> separate approver validates ETag/evidence tuple
                -> immutable allow/block release gate + audit event
```

The API owns validation, tenant/role checks and transactional writes. PostgreSQL is the durable system of record and outbox. The worker performs deterministic computation outside the request path and commits results idempotently. The browser polls simulation state, displays the evidence tuple, and submits the separate approver’s decision. A release gate is created only when the simulation, approval, checksum and policy identifiers agree.

## Reset, inspection and troubleshooting

```powershell
# Service state
./scripts/dev.ps1 status

# Recent application logs
docker compose --profile core logs --tail 100 api worker web

# Repeat the deterministic seed without deleting evidence
./scripts/dev.ps1 seed

# Stop while retaining volumes
./scripts/dev.ps1 down

# Delete only local RuleTwin volumes and recreate the complete demo
./scripts/dev.ps1 reset
```

Common recovery:

- **Docker API unavailable:** start Docker Desktop, wait for the engine to report running, then rerun `./scripts/dev.ps1 up`.
- **UI says Unavailable:** check `http://127.0.0.1:8000/health/ready`, then inspect API and worker logs.
- **Port 8000, 8080 or 5432 is occupied:** stop the conflicting local process before starting RuleTwin; do not change demo URLs immediately before presenting.
- **Simulation remains queued:** inspect worker logs. Restarting the worker is safe because expired leases are reclaimable.
- **Unexpected prior evidence:** run `./scripts/dev.ps1 reset`; no SQL editing is necessary.

## Honest pilot limitations

- Development uses fixed synthetic actors and a fixed tenant rather than production identity and generalized RBAC.
- Only the declarative rounding family and USD integer-minor-unit events are implemented.
- The scenario is a bounded 100-event synthetic dataset, not production traffic or customer data.
- Results are stored relationally; large artifact offload and retention policy are future work.
- Approval and gating demonstrate separation of duties and evidence binding, not production-grade cryptographic signing or deployment authorization.
- The application has local metrics and structured logs, but no production SLO, alerting, backup or disaster-recovery claim.
- Security scans and tests are engineering evidence, not a penetration test, compliance certification or production-readiness guarantee.

## Fallback plan

1. **Browser-only failure, services healthy:** run `pnpm e2e`. Show the two named Chromium cases—allow and block—and use `docs/validation/phase3-validation.md` to explain the already validated flow.
2. **Web container failure, API healthy:** open `http://127.0.0.1:8000/docs` and present the request sequence alongside the architecture flow above. Do not improvise database writes.
3. **Docker failure:** present this guide, `docs/phase3-exit-audit.md`, ADR-009 and the validation record. State clearly that the live environment is unavailable; do not describe the fallback as a live run.
4. **Time pressure:** demonstrate only the allow path live, then cite the named Playwright block-path test and explain the policy threshold. Never claim a live block result that was not shown.

## Final presenter check

Run this before the session, not while the audience is waiting:

```powershell
./scripts/check.ps1 -Integration
pnpm e2e
git status --short
```

Expected result: all checks pass, both Playwright paths pass, and only intentional demo-readiness changes appear in Git status until the user performs the reserved Git operations.
