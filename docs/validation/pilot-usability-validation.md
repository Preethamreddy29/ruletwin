# Pilot Usability and Accessibility Validation

**Date:** 2026-11-19

**Scope:** Completed repository technical evidence for PILOT-10

**Branch:** `codex/pilot-usability-acceptance`

## Implemented evidence

- Audit events use opaque, tenant-scoped keyset pagination with stable `(created_at, id)` boundaries and invalid-cursor rejection.
- The web workflow renders audit events, loads subsequent pages without replacing earlier evidence, and exposes clear loading state.
- Failure messages receive focus and provide explicit comparison or connection retry actions.
- Completed and failed result panels receive focus so keyboard and assistive-technology users reach the outcome.
- Visible focus indicators and mobile identity/action access are preserved.
- Playwright runs allow and block workflows, an axe serious/critical accessibility scan, and a 390-by-844 keyboard/mobile check.
- `.github/workflows/usability-evidence.yml` creates a main-only, 90-day browser evidence artifact.
- `operations/pilot-acceptance-checklist.md` defines the final human rehearsal without fabricating approval.

## Local result

| Check | Result |
|---|---|
| Allow release workflow | Passed in Chromium |
| Block release workflow | Passed in Chromium |
| Serious/critical axe violations | Zero after correcting the RuleTwin home-link accessible name |
| Mobile identity and primary action | Visible and keyboard focusable at 390 by 844 |
| Web lint, typing, tests and build | Passed; 8 component tests, 84.91% statement coverage, production build |
| Python unit suite | Passed on clean Linux; 89 tests, 81.13% coverage |
| Migration and tenant-pagination integration | Reversible migration/zero-drift cycle passed; focused integration test passed |
| Contract and repository safety | OpenAPI, Ruff, mypy, secret scan, changed-file formatting, and diff hygiene passed |

## Exit assessment

PR #33 passed all five protected checks in run `44443944501` and squash-merged as `52ee56f6a5d797d8d6042aecaa9bdefebd524499`. Main workflow run `44444505199` passed and retained artifact `14493046072`, named `ruletwin-usability-52ee56f6a5d797d8d6042aecaa9bdefebd524499`, until 2027-02-17.

The PILOT-10 repository technical evidence is complete. PILOT-10 as a whole remains open until a named operator performs and signs the acceptance checklist. Automation cannot manufacture that human observation.
