import os

import pytest

from app import preflight


def test_missing_secret_key_exits_cleanly(monkeypatch, tmp_path):
    monkeypatch.delenv("TVM_SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/tvm.sqlite")
    with pytest.raises(SystemExit) as exc:
        preflight.check()
    assert exc.value.code == 1


def test_blank_secret_key_exits_cleanly(monkeypatch, tmp_path):
    monkeypatch.setenv("TVM_SECRET_KEY", "   ")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/tvm.sqlite")
    with pytest.raises(SystemExit) as exc:
        preflight.check()
    assert exc.value.code == 1


def test_unwritable_data_dir_exits_cleanly(monkeypatch):
    monkeypatch.setenv("TVM_SECRET_KEY", "x" * 16)
    # A path under a file (never a writable dir) — mkdir + write both fail.
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:////dev/null/nope/tvm.sqlite")
    with pytest.raises(SystemExit) as exc:
        preflight.check()
    assert exc.value.code == 1


def test_happy_path_passes(monkeypatch, tmp_path):
    monkeypatch.setenv("TVM_SECRET_KEY", "x" * 16)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/sub/tvm.sqlite")
    preflight.check()  # no exit, creates the dir
    assert (tmp_path / "sub").is_dir()


def test_non_sqlite_url_skips_dir_check(monkeypatch):
    monkeypatch.setenv("TVM_SECRET_KEY", "x" * 16)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db/tvm")
    preflight.check()  # remote DB: nothing to check locally, must not exit
