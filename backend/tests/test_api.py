import pytest
from fastapi.testclient import TestClient

from app import service
from app.main import app
from app.snapshot import save_snapshot
from tests.conftest import load_fixture


@pytest.fixture
def client(tmp_path, monkeypatch):
    save_snapshot(load_fixture("windfor_sample.json"), load_fixture("fuelhh_sample.json"), tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _clear_caches()
    yield TestClient(app)
    _clear_caches()


def _clear_caches():
    for cached in (service.snapshot, service.aligned_scope, service.accuracy_view):
        cached.cache_clear()


def test_health_reports_snapshot_time(client):
    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["data_as_of"] is not None


def test_health_without_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _clear_caches()

    assert TestClient(app).get("/api/health").json() == {"status": "no_data", "data_as_of": None}
    assert TestClient(app).get("/api/accuracy").status_code == 503


def test_delivery_days_cover_decisions_made_in_january(client):
    body = client.get("/api/delivery-days").json()

    assert body["delivery_days"][0] == "2026-01-02"
    assert body["delivery_days"][-1] == "2026-02-01"
    assert len(body["delivery_days"]) == 31
    assert body["default_cutoff"] == "09:20"


def test_day_view_uses_forecast_available_at_cutoff(client):
    body = client.get("/api/day/2026-01-14", params={"cutoff": "09:50"}).json()

    assert len(body["hours"]) == 24
    assert {h["forecast_published_at"] for h in body["hours"]} == {"2026-01-13T09:30:00Z"}
    assert body["summary"]["hours_excluded"] == 0
    assert body["summary"]["mae_mw"] > 0


def test_day_without_data_shows_gaps_not_errors(client):
    body = client.get("/api/day/2026-01-20").json()

    assert len(body["hours"]) == 24
    assert body["summary"]["hours_excluded"] == 24
    assert body["summary"]["mae_mw"] is None


def test_custom_cutoff_is_accepted(client):
    assert client.get("/api/day/2026-01-14", params={"cutoff": "08:00"}).status_code == 200


@pytest.mark.parametrize("bad_cutoff", ["9:20", "24:00", "09:60", "noon"])
def test_malformed_cutoff_is_rejected(client, bad_cutoff):
    assert client.get("/api/accuracy", params={"cutoff": bad_cutoff}).status_code == 422


@pytest.mark.parametrize("day", ["2026-01-01", "2026-02-02"])
def test_day_outside_scope_is_rejected_with_reason(client, day):
    response = client.get(f"/api/day/{day}")

    assert response.status_code == 422
    assert "between 2026-01-02 and 2026-02-01" in response.json()["detail"]


def test_accuracy_has_headline_and_breakdowns(client):
    body = client.get("/api/accuracy").json()

    assert body["headline"].startswith("Across January, the 09:20 forecast missed by")
    assert body["metrics"]["hours_used"] == 24
    assert body["metrics"]["buffer_mw"] > 0
    assert len(body["by_hour"]) == 24
    assert sum(bin_["count"] for bin_ in body["histogram"]) == 24
    assert len(body["points"]) == 24


def test_snapshot_round_trip_keeps_utc_timestamps(tmp_path):
    from app.snapshot import load_snapshot

    forecasts = load_fixture("windfor_sample.json")
    save_snapshot(forecasts, load_fixture("fuelhh_sample.json"), tmp_path)

    loaded = load_snapshot(tmp_path).forecasts

    assert str(loaded["publish_time"].dt.tz) == "UTC"
    assert loaded["publish_time"].equals(forecasts["publish_time"])
