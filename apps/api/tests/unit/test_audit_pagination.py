import uuid
from datetime import UTC, datetime

import pytest

from ruletwin.api.problems import ProblemError
from ruletwin.api.vertical_slice import _decode_audit_cursor, _encode_audit_cursor


def test_audit_cursor_round_trips_keyset_boundary() -> None:
    created_at = datetime(2026, 11, 19, 12, 30, 45, 123456, tzinfo=UTC)
    event_id = uuid.UUID("11111111-2222-3333-4444-555555555555")

    cursor = _encode_audit_cursor(created_at, event_id)

    assert _decode_audit_cursor(cursor) == (created_at, event_id)


@pytest.mark.parametrize(
    "cursor",
    ["not-base64", "W10", "WyIyMDI2LTExLTE5VDEyOjMwOjQ1Iiwibm90LWEtdXVpZCJd"],
)
def test_audit_cursor_rejects_invalid_or_ambiguous_values(cursor: str) -> None:
    with pytest.raises(ProblemError, match="cursor is invalid") as error:
        _decode_audit_cursor(cursor)

    assert error.value.status == 422
    assert error.value.code == "validation-failed"
