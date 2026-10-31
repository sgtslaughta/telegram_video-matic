"""1.7.0 storage API: untracked files are listed, never auto-deleted, and
deletion is confined to the media root."""
from fastapi.testclient import TestClient

from tests.test_integration_api import test_app  # noqa: F401


def _root(app, tmp_path):
    app.state.media_root = str(tmp_path)
    return tmp_path


def test_untracked_listing_and_safe_delete(test_app, tmp_path):  # noqa: F811
    root = _root(test_app, tmp_path)
    (root / "League").mkdir()
    (root / "League" / "orphan.mkv").write_bytes(b"xx")
    (root / "notes.txt").write_text("not a video")
    outside = tmp_path.parent / "outside.mkv"
    outside.write_bytes(b"x")
    with TestClient(test_app) as c:
        test_app.state.media_root = str(root)
        body = c.get("/api/storage").json()
        paths = [u["path"] for u in body["untracked"]["items"]]
        assert paths == ["League/orphan.mkv"]
        assert "preview" in body and "disk" in body
        assert c.request("DELETE", "/api/storage/untracked", json={"path": "../outside.mkv"}).status_code == 400
        assert outside.exists()
        assert c.request("DELETE", "/api/storage/untracked", json={"path": "League/orphan.mkv"}).status_code == 200
        assert not (root / "League" / "orphan.mkv").exists()


def test_keep_pin_on_media_404(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        assert c.patch("/api/media/999/keep", json={"keep": True}).status_code == 404


def test_confirm_with_nothing_pending(test_app, tmp_path):  # noqa: F811
    with TestClient(test_app) as c:
        test_app.state.media_root = str(tmp_path)
        r = c.post("/api/storage/prune/confirm")
        assert r.status_code == 200 and r.json()["pruned"] == 0
