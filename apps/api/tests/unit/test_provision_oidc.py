import pytest

from ruletwin.provision_oidc import _subject_digest, _validated_subject


def test_oidc_subject_validation_and_redacted_digest() -> None:
    subject = "auth0|pilot-user-123"
    assert _validated_subject(subject) == subject
    digest = _subject_digest(subject)
    assert digest.startswith("sha256:")
    assert subject not in digest


@pytest.mark.parametrize("subject", ["", " leading", "trailing ", "embedded space"])
def test_invalid_oidc_subjects_fail_closed(subject: str) -> None:
    with pytest.raises(ValueError, match="OIDC subject"):
        _validated_subject(subject)
