# storage/clickhouse.py
# ClickHouse client and CRUD helpers for outbreak_signals and alerts tables.

from __future__ import annotations
import os
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()


def client():
    """Return a connected ClickHouse client using environment credentials."""
    host = os.environ["CH_HOST"].replace("https://", "").replace("http://", "").rstrip("/")
    return clickhouse_connect.get_client(
        host=host,
        port=int(os.environ.get("CH_PORT", "8443")),
        username=os.environ["CH_USER"],
        password=os.environ["CH_PASSWORD"],
        database=os.environ.get("CH_DATABASE", "outbreak"),
        secure=True,
    )


def insert_signals(signals: list) -> None:
    """Batch-insert OutbreakSignal records into outbreak_signals."""
    rows = [
        [
            s.event_id,
            s.run_id,
            s.timestamp,
            s.zip,
            s.symptom,
            s.source_type,
            s.source_url,
            s.evidence_text,
            s.confidence,
            s.synthetic,
        ]
        for s in signals
    ]
    if rows:
        client().insert(
            "outbreak_signals",
            rows,
            column_names=[
                "event_id", "run_id", "timestamp", "zip", "symptom",
                "source_type", "source_url", "evidence_text",
                "confidence", "synthetic",
            ],
        )


def insert_alert(package) -> None:
    """Insert an AlertPackage into the alerts table."""
    client().insert(
        "alerts",
        [[
            package.alert_id,
            package.run_id,
            package.created_at,
            package.zip,
            package.symptom,
            package.recent_count,
            package.baseline_avg,
            package.baseline_stddev,
            package.z_score,
            package.clinical_status,
            package.clinical_aggregate_count,
            package.source_count,
            package.source_diversity,
            package.source_urls,
            package.decision_reason,
            package.datadog_trace_id,
            package.senso_url,
            package.payment_status,
        ]],
        column_names=[
            "alert_id", "run_id", "created_at", "zip", "symptom",
            "recent_count", "baseline_avg", "baseline_stddev", "z_score",
            "clinical_status", "clinical_aggregate_count", "source_count",
            "source_diversity", "source_urls", "decision_reason",
            "datadog_trace_id", "senso_url", "payment_status",
        ],
    )


def get_alert(alert_id: str) -> dict | None:
    """Fetch the most recent row for a given alert_id."""
    rows = list(client().query(
        """
        SELECT *
        FROM alerts
        WHERE alert_id = {alert_id:String}
        ORDER BY created_at DESC
        LIMIT 1
        """,
        parameters={"alert_id": alert_id},
    ).named_results())
    return rows[0] if rows else None


def mark_alert_paid(alert_id: str) -> dict | None:
    """
    Mark an alert as paid by inserting an updated copy.
    Safe for MergeTree (append-only) tables; production should use ReplacingMergeTree.
    """
    alert = get_alert(alert_id)
    if not alert:
        return None
    alert["payment_status"] = "paid"
    client().insert(
        "alerts",
        [[alert[c] for c in alert.keys()]],
        column_names=list(alert.keys()),
    )
    return alert


def get_control_panel_snapshot() -> dict:
    """
    Return a lightweight DB-backed status snapshot for /status.
    This makes the control panel useful even when ingestion, anomaly, and API
    run as separate processes.
    """
    ch = client()
    counts = list(ch.query(
        """
        SELECT
            count() AS total_signals,
            countIf(synthetic = false) AS real_signals,
            countIf(synthetic = false AND source_type = 'nimble_open_web') AS nimble_real_signals,
            countIf(synthetic = true) AS synthetic_signals,
            max(timestamp) AS latest_signal_at
        FROM outbreak_signals
        """
    ).named_results())[0]
    latest_alerts = list(ch.query(
        """
        SELECT
            alert_id,
            run_id,
            created_at,
            zip,
            symptom,
            recent_count,
            z_score,
            clinical_status,
            clinical_aggregate_count,
            source_count,
            source_diversity,
            senso_url,
            payment_status
        FROM alerts
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).named_results())
    return {"counts": counts, "latest_alerts": latest_alerts}
