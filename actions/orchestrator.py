# actions/orchestrator.py
# Receives an anomaly row from the anomaly engine, builds an AlertPackage,
# runs clinical verification, and routes confirmed alerts to all action lanes.

import os
from datetime import datetime, timezone
from uuid import uuid4
from ingestion.models import AlertPackage
from verification.clinical_aggregate import verify_clinical_aggregate
from actions.slack_alerts import send_slack_alert
from actions.senso_publish import publish_cited_alert
from observability.datadog import log_event, emit_metric
from storage.clickhouse import insert_alert


def handle_anomaly(row: dict) -> AlertPackage:
    """
    Full lifecycle for one anomaly hit:
    detect → verify → publish → alert → store.
    """
    run_id = os.environ.get("DEMO_RUN_ID", "run_demo")
    alert_id = f"alert_{uuid4().hex[:8]}"
    log_event("anomaly_detected", {"run_id": run_id, **row})

    clinical = verify_clinical_aggregate(row["zip"], row["symptom"])

    package = AlertPackage(
        alert_id=alert_id,
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        zip=row["zip"],
        symptom=row["symptom"],
        recent_count=int(row["recent_count"]),
        baseline_avg=float(row["baseline_avg"]),
        baseline_stddev=float(row["baseline_stddev"]),
        z_score=float(row["z_score"]),
        clinical_status=clinical.status,
        clinical_aggregate_count=clinical.count,
        source_count=int(row.get("source_count", row["recent_count"])),
        source_diversity=int(row.get("source_diversity", 1)),
        source_urls=[u for u in row.get("source_urls", []) if u],
        decision_reason=clinical.note,
    )

    if package.clinical_status == "confirmed":
        package.senso_url = publish_cited_alert(package)
        send_slack_alert(package)
        emit_metric(
            "outbreak.alert.confirmed",
            1,
            tags=[f"zip:{package.zip}", f"symptom:{package.symptom}"],
        )
    else:
        emit_metric(
            "outbreak.alert.suppressed",
            1,
            tags=[f"zip:{package.zip}", f"symptom:{package.symptom}"],
        )

    insert_alert(package)
    log_event(f"alert_{package.clinical_status}", package.model_dump())
    return package
