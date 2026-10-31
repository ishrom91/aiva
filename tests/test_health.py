"""Application readiness endpoint tests."""

import pytest

from src import main


@pytest.mark.asyncio
async def test_health_returns_503_when_database_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "engine", None)
    monkeypatch.setattr(main.settings, "REDIS_URL", "")

    response = await main.health_check()

    assert response.status_code == 503
    assert response.body is not None
    assert b'"database":"failed"' in response.body
    assert b"uptime_seconds" in response.body
