"""1.8.0: overview + since-last-visit summary."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routers.overview import _incidents
from tests.test_integration_api import test_app  # noqa: F401


def test_overview_shape(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        r = c.get("/api/overview?hours=24")
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(body) == {"telegram", "subscriptions", "recent", "attention", "last_24h"}
        assert body["attention"]["failed"] == 0 and body["attention"]["needs_review"] == 0


def test_summary_hidden_on_first_visit_then_marks_seen(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        assert c.get("/api/summary").json()["show"] is False
        assert c.post("/api/summary/seen").status_code == 200
        assert c.get("/api/summary").json()["show"] is False  # just visited


def test_incidents_merge_consecutive_down_hours():
    now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
    h = lambda k: now.replace(minute=0) - timedelta(hours=k)  # noqa: E731
    rows = [SimpleNamespace(hour=h(k), down=1) for k in (30, 29, 28)] + [SimpleNamespace(hour=h(1), down=2)]
    out = _incidents(rows, now)
    assert [(i["hours"], i["ended"] is None) for i in out] == [(3, False), (1, True)]
