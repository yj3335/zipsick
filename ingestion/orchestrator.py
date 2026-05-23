# ingestion/orchestrator.py
# Top-level ingestion run: Nimble open-web lane + NYC 311 public-data lane.

import os
from ingestion.extractor import extract_signals
from ingestion.nimble_client import fetch_public_page
from ingestion.public_data import fetch_nyc_311_records, record_to_text
from observability.datadog import log_event, emit_metric
from storage.clickhouse import insert_signals
from config.sources import NIMBLE_TARGET_URL


def ingest_once(run_id: str | None = None) -> list:
    """
    Run one full ingestion cycle.
    1. Nimble / open-web lane (sponsor proof).
    2. NYC 311 public-data lane (reliable fallback).
    Returns the list of OutbreakSignal objects inserted.
    """
    signals = []

    # --- Sponsor/open-web proof lane ---
    nimble_text = fetch_public_page(NIMBLE_TARGET_URL)
    signals.extend(
        extract_signals(
            nimble_text,
            source_type="nimble_open_web",
            source_url=NIMBLE_TARGET_URL,
            fallback_zip="10014",
            run_id=run_id,
        )
    )

    # --- Reliable public-data lane ---
    for record in fetch_nyc_311_records():
        text, zip_code = record_to_text(record)
        signals.extend(
            extract_signals(
                text,
                source_type="nyc_311_public_data",
                source_url=None,
                fallback_zip=zip_code,
                run_id=run_id,
            )
        )

    insert_signals(signals)
    emit_metric("outbreak.events_ingested", len(signals), tags=[f"run_id:{run_id}"])
    log_event("ingestion_complete", {"run_id": run_id, "signals": len(signals)})
    return signals


if __name__ == "__main__":
    ingest_once(os.environ.get("DEMO_RUN_ID", "run_demo"))
