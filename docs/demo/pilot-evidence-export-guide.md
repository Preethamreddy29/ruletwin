# Pilot Evidence Export Demo Guide

## Purpose

Show that a completed RuleTwin decision can be downloaded as a portable, checksum-bound JSON evidence bundle without weakening tenant or role boundaries. All identities and data are fictional and development-only.

## Start

From the repository root:

```powershell
./scripts/dev.ps1 up
```

Open `http://localhost:8080`.

## Demonstration flow

1. Sign in as **NovaBill Analyst**, create the proposed rounding rule, and run the simulation.
2. Inspect the deterministic impact and risk result.
3. Sign in as **NovaBill QA Reviewer**, approve the completed evidence, and select **Download evidence JSON**.
4. Open the downloaded file and point out the schema version, tenant and simulation identifiers, immutable input checksums, result checksum, impact and risk evidence, approval, release gate when present, and top-level export checksum.
5. Download the unchanged simulation again and show that the displayed export checksum is unchanged.
6. Sign in as **NovaBill Auditor** and inspect the tenant audit trail. Show the `evidence.exported` event.
7. Explain that analysts cannot export and that a Brightline role cannot use a NovaBill simulation identifier; both object authorization and tenant scoping are enforced by the API.

## Honest limitations

- Export is implemented; importing or automatically reproducing an export is not.
- The bundle is downloaded by the browser and is not stored in an artifact service.
- Development personas are not production authentication.
- This increment is one part of controlled-pilot readiness and does not authorize real data or public deployment.
