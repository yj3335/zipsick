# tests/test_payment.py
# Tests the x402 payment gate behaviour of the FastAPI app.

import os
import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("CH_HOST", "localhost")
os.environ.setdefault("CH_USER", "default")
os.environ.setdefault("CH_PASSWORD", "")
os.environ["X402_ENABLED"] = "true"

# Patch get_alert and mark_alert_paid so tests run without ClickHouse.
import unittest.mock as mock

FAKE_ALERT = {
    "alert_id": "alert_abc123",
    "run_id": "run_demo",
    "created_at": "2024-01-01T00:00:00",
    "zip": "10014",
    "symptom": "gi",
    "recent_count": 15,
    "baseline_avg": 2.0,
    "baseline_stddev": 1.0,
    "z_score": 13.0,
    "clinical_status": "confirmed",
    "clinical_aggregate_count": 2,
    "source_count": 15,
    "source_diversity": 3,
    "source_urls": [],
    "decision_reason": "aggregate clinical match found",
    "datadog_trace_id": None,
    "senso_url": None,
    "payment_status": "unpaid",
}


FAKE_SNAPSHOT = {
    "counts": {
        "total_signals": 15,
        "real_signals": 1,
        "nimble_real_signals": 1,
        "synthetic_signals": 14,
        "latest_signal_at": "2024-01-01T00:00:00",
    },
    "latest_alerts": [FAKE_ALERT],
}


@pytest.fixture()
def client():
    with (
        mock.patch("storage.clickhouse.get_alert", return_value=FAKE_ALERT),
        mock.patch("storage.clickhouse.mark_alert_paid", return_value={**FAKE_ALERT, "payment_status": "paid"}),
        mock.patch("storage.clickhouse.get_control_panel_snapshot", return_value=FAKE_SNAPSHOT),
        mock.patch("app.get_control_panel_snapshot", return_value=FAKE_SNAPSHOT),
    ):
        from app import app
        return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_status(client):
    r = client.get("/status")
    assert r.status_code == 200
    assert "run_id" in r.json()


def test_alert_returns_402_without_payment(client):
    r = client.get("/alerts/confirmed/alert_abc123")
    assert r.status_code == 402
    body = r.json()["detail"]
    assert body["payment_protocol"] == "x402"


def test_alert_returns_200_with_payment_header(client):
    r = client.get("/alerts/confirmed/alert_abc123", headers={"x-payment": "demo-paid"})
    assert r.status_code == 200
    assert r.json()["payment_status"] == "paid"


def test_alert_404_for_unknown_id():
    from app import app
    with mock.patch("app.get_alert", return_value=None):
        tc = TestClient(app)
        r = tc.get("/alerts/confirmed/nonexistent")
        assert r.status_code == 404


def test_alert_403_for_suppressed_status():
    from app import app
    suppressed = {**FAKE_ALERT, "clinical_status": "suppressed"}
    with mock.patch("app.get_alert", return_value=suppressed):
        tc = TestClient(app)
        r = tc.get("/alerts/confirmed/alert_abc123")
        assert r.status_code == 403


def test_x402_disabled_bypasses_payment_gate():
    from app import app
    paid = {**FAKE_ALERT, "payment_status": "paid"}
    with (
        mock.patch("app.get_alert", return_value=FAKE_ALERT),
        mock.patch("app.mark_alert_paid", return_value=paid),
        mock.patch.dict(os.environ, {"X402_ENABLED": "false"}),
    ):
        tc = TestClient(app)
        r = tc.get("/alerts/confirmed/alert_abc123")
        assert r.status_code == 200
        assert r.json()["payment_status"] == "paid"
