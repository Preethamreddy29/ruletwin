# Phase 3 Local Operations

## Start and verify

```powershell
./scripts/dev.ps1 up
./scripts/check.ps1 -Integration
pnpm e2e
```

Open `http://localhost:8080`. Select `5 minor units` for the allow path or `10 minor units` for the block path, run the comparison, inspect the checksum and approve the evidence. The release gate must match the policy result.

## Recovery behavior

- A claimed outbox row remains `pending` until the result transaction commits. An expired lease is reclaimed and increments the attempt number.
- If completed evidence exists but delivery is repeated, the worker only marks the outbox row processed; it does not create a second impact result.
- Domain or infrastructure exceptions roll back execution and release the lease with a short retry delay.
- Approval returns conflict for incomplete, stale, substituted or self-authored evidence. Gate evaluation blocks when evidence is not exact.

Inspect state without manual mutation:

```powershell
docker compose --profile core ps
docker compose --profile core logs --tail 100 api worker
```

No manual database changes are required or permitted for the signature path.
