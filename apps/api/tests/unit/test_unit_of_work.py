from unittest.mock import AsyncMock, MagicMock

import pytest

from ruletwin.db.unit_of_work import UnitOfWork


async def test_unit_of_work_commits_and_closes() -> None:
    session = AsyncMock()
    sessions = MagicMock(return_value=session)
    async with UnitOfWork(sessions) as unit:
        assert unit.session is session
    session.begin.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()


async def test_unit_of_work_rolls_back_on_error() -> None:
    session = AsyncMock()
    sessions = MagicMock(return_value=session)
    with pytest.raises(RuntimeError):
        async with UnitOfWork(sessions):
            raise RuntimeError("controlled failure")
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
    session.close.assert_awaited_once()
