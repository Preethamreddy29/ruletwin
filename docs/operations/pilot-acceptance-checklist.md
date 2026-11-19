# Pilot Operator Acceptance Checklist

Use this checklist for the final operator-led rehearsal of the synthetic RuleTwin pilot. Complete it against the exact release candidate and retain the signed copy with the release evidence. Automated browser evidence supports this checklist but does not replace the named operator's observation.

## Rehearsal record

| Field | Value |
|---|---|
| Date and timezone | Pending operator rehearsal |
| Operator name | Pending |
| Candidate commit | Pending |
| Environment and URL | Pending |
| Browser and version | Pending |
| Synthetic tenant/persona set | NovaBill and Brightline pilot personas |

## Required observations

- [ ] Sign in through the configured pilot identity provider and confirm the expected tenant and role.
- [ ] Create or select baseline and candidate rounding rules using synthetic data only.
- [ ] Start a comparison and confirm the queued/running state is understandable.
- [ ] Confirm the completed impact and risk result is understandable without database or API inspection.
- [ ] Exercise both an allowed and a blocked release decision.
- [ ] Confirm a reviewer cannot self-approve and a wrong-tenant identity cannot discover the object.
- [ ] Export the completed evidence bundle and verify the downloaded checksum-bound JSON is readable.
- [ ] Browse at least two audit pages and confirm no event is duplicated between pages.
- [ ] Trigger one recoverable failure and confirm the message explains the problem and exposes a working retry action.
- [ ] Complete the primary flow using keyboard navigation at desktop width.
- [ ] Repeat identity selection and the primary action at a 390-by-844 mobile viewport.
- [ ] Confirm no real customer, employer, payment, or production data appears anywhere in the rehearsal.

## Automated evidence to attach

- Protected CI URL and commit: Pending merged branch evidence.
- Main usability workflow URL and artifact: Pending merged `main` evidence.
- Playwright allow/block result: Pending retained workflow artifact.
- Accessibility scan result: Pending retained workflow artifact.
- Mobile keyboard result: Pending retained workflow artifact.

## Findings

Record every finding with severity, owner, and disposition. Any open S0, S1, or S2 defect blocks acceptance.

| Finding | Severity | Owner | Disposition |
|---|---|---|---|
| None recorded yet; rehearsal pending | — | — | — |

## Acceptance

- [ ] I observed the required workflow on the candidate recorded above.
- [ ] All blocking findings are resolved or the candidate is rejected.
- [ ] I approve this candidate for the invitation-only synthetic-data pilot scope only.

**Operator name:** Pending

**Signature or approved account:** Pending

**Date and timezone:** Pending

The checklist is intentionally unsigned until a person performs the rehearsal. Repository maintainers and automation must not pre-fill acceptance.
