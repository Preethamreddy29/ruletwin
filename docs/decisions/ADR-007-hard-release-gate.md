# ADR-007: Fail-Closed Hard Release Gate

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** A risk-policy block, error, stale result, missing evidence or invalid checksum prevents an allow outcome. Warnings may add context but cannot bypass hard conditions.
**Why:** A false-safe decision is the product's primary dangerous failure mode.
**Alternatives:** Warning-only advisory; manual override of any result.
**Consequences:** Availability failures can delay release; policy reasons and evidence must be explicit and reproducible.
**Revisit when:** Only through an accepted governance ADR with equivalent safety evidence; never to improve a demo.
