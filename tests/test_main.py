"""Smoke test for application import."""

import importlib
import sys

import pytest


def test_main_module_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "000000000:TEST_TOKEN_FOR_IMPORT")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv(
        "ENCRYPTION_KEY", "dGVzdC1rZXktdGVzdC1rZXktdGVzdC1rZXktdGVzdGtleTE="
    )
    monkeypatch.delenv("WEBHOOK_URL", raising=False)

    for module_name in ("src.config", "src.database", "src.main"):
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    import src.main as main_module

    assert main_module.app.title == "FastAPI"
