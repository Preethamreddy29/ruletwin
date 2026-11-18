# Pilot Release Evidence Runbook

## Purpose

This runbook creates checksum-bound supply-chain evidence for a RuleTwin pilot preflight candidate. It does not publish a GitHub release, push a container image, sign an artifact, or authorize an externally hosted pilot.

## Protected pull-request evidence

The `Compose and container evidence` CI job:

1. builds the API and web images from the reviewed commit;
2. asserts both images run as non-root users;
3. generates SPDX JSON SBOMs for both images;
4. records JSON Trivy reports for high and critical vulnerabilities;
5. records the complete local image inspection output, including immutable image IDs;
6. creates and re-verifies `artifacts/release/manifest.json`; and
7. uploads the evidence directory as a 30-day GitHub Actions artifact.

The job fails if either image contains an unfixed-policy-eligible high or critical vulnerability. A failure is not an accepted risk. Any exception requires a separately reviewed risk record; this repository contains no standing exception.

## Main-branch preflight evidence

After the change is merged and the protected `main` workflow passes:

1. Open **Actions → Pilot release candidate evidence → Run workflow**.
2. Select `main`.
3. Enter a preflight version matching `0.4.0-pilot.preflight.N`.
4. Run the workflow.
5. Verify that **Build immutable candidate evidence** passes.
6. Download the `ruletwin-<version>-<commit>` artifact.
7. Verify it locally:

   ```powershell
   python scripts/release_evidence.py verify-manifest --manifest <downloaded-folder>/manifest.json
   ```

8. Record the workflow URL, commit, artifact name, retention deadline, and verification result in the validation record.

The workflow only runs from `main` and rejects the official `0.4.0-pilot.N` form while other pilot gates remain open.

## Evidence contents

| File | Purpose |
|---|---|
| `api-image.spdx.json` | API image SPDX SBOM |
| `web-image.spdx.json` | Web image SPDX SBOM |
| `api-image-trivy.json` | API high/critical vulnerability report |
| `web-image-trivy.json` | Web high/critical vulnerability report |
| `api-image-inspect.json` | API image metadata and immutable local ID |
| `web-image-inspect.json` | Web image metadata and immutable local ID |
| `manifest.json` | Commit/version binding plus SHA-256 and size for every evidence file |

## Release boundary

Do not create `v0.4.0-pilot.1`, a GitHub Release, a public package, or a deployment approval until every controlled-pilot release gate passes. Registry digests, provenance signing, the selected host, and final release retention are still required for the official release candidate.
