import pytest
from app.config import Settings


def test_settings_loads_from_env(monkeypatch):
    """Settings loads DATABASE_URL, poll_interval_sec from env."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("POLL_INTERVAL_SEC", "60")

    settings = Settings()

    assert settings.database_url == "sqlite+aiosqlite:////tmp/test.db"
    assert settings.tvm_secret_key == "test-secret-key"
    assert settings.poll_interval_sec == 60


def test_settings_defaults_when_env_absent(monkeypatch):
    """Settings uses defaults when env vars absent."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POLL_INTERVAL_SEC", raising=False)
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret-key")

    settings = Settings()

    assert settings.database_url == "sqlite+aiosqlite:////data/tvm.sqlite"
    assert settings.poll_interval_sec == 300


def test_settings_fails_without_tvm_secret_key(monkeypatch):
    """Settings initialization fails if TVM_SECRET_KEY unset."""
    monkeypatch.delenv("TVM_SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        Settings()
