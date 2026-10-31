"""1.6.0: notifications API stores URLs encrypted and never returns them."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.test_integration_api import test_app  # noqa: F401 — reuse fixture


def test_targets_roundtrip_masked(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        r = c.put("/api/notifications/targets", json=[
            {"name": "Phone", "url": "pover://user@token", "triggers": ["download_failed", "telegram"]}])
        assert r.status_code == 200, r.text
        tid = r.json()[0]["id"]
        body = c.get("/api/notifications").json()
        t = body["targets"][0]
        assert t["url_masked"] == "pover://••••" and "token" not in str(body)
        # Edit without URL keeps the stored secret.
        r = c.put("/api/notifications/targets", json=[{"id": tid, "name": "Phone 2", "triggers": ["telegram"]}])
        assert r.status_code == 200 and r.json()[0]["name"] == "Phone 2"
        assert test_app.state.notifier.targets[0].url == "pover://user@token"
        # Encrypted blob never leaks through the generic settings list.
        keys = {s["key"] for s in c.get("/api/settings").json()}
        assert "notify_targets" not in keys


def test_rejects_unknown_trigger_and_missing_url(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        assert c.put("/api/notifications/targets", json=[
            {"name": "x", "url": "json://h", "triggers": ["nope"]}]).status_code == 422
        assert c.put("/api/notifications/targets", json=[{"name": "x", "triggers": []}]).status_code == 422


def test_send_test_uses_apprise(test_app):  # noqa: F811
    with TestClient(test_app) as c, patch("app.api.routers.notifications.apprise_send", return_value=True) as s:
        assert c.post("/api/notifications/test", json={"url": "json://h"}).status_code == 200
        s.assert_awaited_once()


def test_jellyfin_key_write_only(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        r = c.put("/api/notifications/jellyfin", json={"url": "http://jf:8096", "api_key": "secret"})
        assert r.json()["api_key_set"] is True
        assert "secret" not in c.get("/api/notifications").text
        assert test_app.state.jellyfin.api_key == "secret"


def test_jellyfin_key_dropped_when_origin_changes(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        c.put("/api/notifications/jellyfin", json={"url": "http://jf:8096", "api_key": "secret"})
        r = c.put("/api/notifications/jellyfin", json={"url": "http://jf:8096/", "library_id": "x"})
        assert r.json()["api_key_set"] is True  # same origin keeps key
        r = c.put("/api/notifications/jellyfin", json={"url": "http://evil:80"})
        assert r.json()["api_key_set"] is False
