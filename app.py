# app.py
# FastAPI control panel, /status, and x402-gated confirmed-alert endpoint.

import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from storage.clickhouse import get_alert, mark_alert_paid

app = FastAPI(
    title="Neighborhood Outbreak Early Warning",
    description=(
        "Autonomous public-health signal agent. "
        "Monitors open-web sources for ZIP-level symptom anomalies, "
        "verifies via aggregate clinical adapter, and exposes confirmed "
        "alert packages behind x402 payment rails."
    ),
    version="1.0.0",
)

# Mutable run state — updated by the ingestion and anomaly processes.
RUN_STATE: dict = {
    "run_id": os.environ.get("DEMO_RUN_ID", "run_demo"),
    "stage": "waiting",
    "proof": {
        "nimble": "pending",
        "clickhouse": "pending",
        "clinical": "pending",
        "datadog": "pending",
        "senso": "pending",
        "x402": "pending",
    },
    "latest_decision": None,
}


@app.get("/health", summary="Health check")
def health():
    return {"ok": True}


@app.get("/status", summary="Agent run state and proof checklist")
def status():
    # Dynamically check database records to update the checklist status.
    proof = RUN_STATE["proof"].copy()
    try:
        from storage.clickhouse import client
        ch = client()
        
        # Check clickhouse connectivity
        ch_count = ch.query("SELECT count() FROM outbreak_signals").result_rows[0][0]
        proof["clickhouse"] = "success" if ch_count > 0 else "pending"
        
        # Check nimble signals
        nimble_count = ch.query("SELECT count() FROM outbreak_signals WHERE source_type = 'nimble_open_web'").result_rows[0][0]
        proof["nimble"] = "success" if nimble_count > 0 else "pending"
        
        # Check clinical verification / alerts
        alert_rows = ch.query("SELECT clinical_status, payment_status, senso_url FROM alerts").result_rows
        if alert_rows:
            proof["clinical"] = "success"
            
            # Check if any alert is paid or has returned 402
            any_paid = any(r[1] == "paid" for r in alert_rows)
            if any_paid:
                proof["x402"] = "paid"
            elif RUN_STATE["proof"]["x402"] != "pending":
                proof["x402"] = RUN_STATE["proof"]["x402"]
            
            # Check if any alert has senso_url set
            any_published = any(r[2] is not None for r in alert_rows)
            if any_published or PUBLISHED_ALERTS:
                proof["senso"] = "published"
        
        # Datadog key presence
        if os.environ.get("DD_API_KEY"):
            proof["datadog"] = "success"
            
    except Exception as e:
        print(f"Error dynamically updating status: {e}")
        pass

    RUN_STATE["proof"].update(proof)
    return RUN_STATE


@app.get("/", include_in_schema=False)
def root():
    return status()


@app.get(
    "/alerts/confirmed/{alert_id}",
    summary="Retrieve a confirmed alert package (x402 payment gate)",
)
def get_confirmed_alert(
    alert_id: str,
    x_payment: str | None = Header(default=None),
):
    """
    Returns a confirmed alert package.

    Without an `x-payment` header: **402 Payment Required** with payment instructions.
    With `x-payment: demo-paid` (or a real payment proof): **200 OK** with full alert data.
    """
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")

    if alert["clinical_status"] != "confirmed":
        raise HTTPException(status_code=403, detail="only confirmed alerts are available")

    x402_enabled = os.environ.get("X402_ENABLED", "true").lower() == "true"
    if x402_enabled and not x_payment:
        RUN_STATE["proof"]["x402"] = "402_returned"
        raise HTTPException(
            status_code=402,
            detail={
                "payment_protocol": "x402",
                "amount_usd": os.environ.get("DEMO_PRICE_USD", "0.25"),
                "resource": f"/alerts/confirmed/{alert_id}",
                "description": "Confirmed outbreak alert package",
                "instructions": "Include header: x-payment: <proof> to unlock.",
            },
        )

    RUN_STATE["proof"]["x402"] = "paid"
    return mark_alert_paid(alert_id)


class PublishedAlertPayload(BaseModel):
    title: str
    summary: str
    citations: list[str]
    metadata: dict


PUBLISHED_ALERTS: dict = {}


@app.post("/alerts/publish", summary="Receive a published alert package (local publisher)")
def publish_alert(payload: PublishedAlertPayload):
    alert_id = payload.metadata.get("alert_id")
    if not alert_id:
        raise HTTPException(status_code=422, detail="alert_id missing in metadata")
    
    PUBLISHED_ALERTS[alert_id] = payload
    RUN_STATE["proof"]["senso"] = "published"
    
    return {
        "status": "success",
        "url": f"http://localhost:8000/alerts/published/{alert_id}"
    }


@app.get("/alerts/published/{alert_id}", summary="View a published cited.md alert package")
def get_published_alert(alert_id: str):
    if alert_id not in PUBLISHED_ALERTS:
        raise HTTPException(status_code=404, detail="alert not found")
    return PUBLISHED_ALERTS[alert_id]
