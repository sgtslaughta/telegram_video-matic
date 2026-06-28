import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import fs


def _client(media_root):
    app = FastAPI()
    app.include_router(fs.router)
    return TestClient(app)


def test_lists_immediate_subdirs(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))
    (tmp_path / "Movies").mkdir()
    (tmp_path / "TV").mkdir()
    (tmp_path / ".partial").mkdir()  # hidden — must be omitted
    (tmp_path / "note.txt").write_text("x")  # file — must be omitted

    r = _client(tmp_path).get("/api/fs/dirs")
    assert r.status_code == 200
    body = r.json()
    assert body["dirs"] == ["Movies", "TV"]
    assert body["parent"] is None  # at root
    assert body["path"] == str(tmp_path.resolve())


def test_descends_into_subdir(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))
    (tmp_path / "TV" / "Drama").mkdir(parents=True)

    r = _client(tmp_path).get("/api/fs/dirs", params={"path": str(tmp_path / "TV")})
    assert r.status_code == 200
    body = r.json()
    assert body["dirs"] == ["Drama"]
    assert body["parent"] == str(tmp_path.resolve())  # parent links back up


def test_rejects_traversal_outside_root(monkeypatch, tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    monkeypatch.setenv("MEDIA_ROOT", str(root))
    r = _client(root).get("/api/fs/dirs", params={"path": str(root / ".." / "..")})
    assert r.status_code == 400


def test_rejects_symlink_escape(monkeypatch, tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    outside = tmp_path / "secret"
    outside.mkdir()
    (root / "link").symlink_to(outside)
    monkeypatch.setenv("MEDIA_ROOT", str(root))
    # The symlink resolves outside the sandbox → rejected.
    r = _client(root).get("/api/fs/dirs", params={"path": str(root / "link")})
    assert r.status_code == 400


def test_missing_dir_404(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))
    r = _client(tmp_path).get("/api/fs/dirs", params={"path": str(tmp_path / "nope")})
    assert r.status_code == 404
