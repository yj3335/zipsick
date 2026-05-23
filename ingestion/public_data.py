# ingestion/public_data.py
# NYC Open Data / 311 collector — reliable public-data ingestion lane.

import requests
from config.sources import NYC_311_ENDPOINT, NYC_311_LIMIT, NYC_311_FIELDS


def fetch_nyc_311_records(limit: int = NYC_311_LIMIT) -> list[dict]:
    """
    Query NYC Open Data for the most recent 311 complaint records.
    Returns an empty list on network failures so the ingestion loop keeps running.
    """
    params = {
        "$limit": limit,
        "$order": "created_date DESC",
        "$select": ",".join(NYC_311_FIELDS),
    }
    try:
        response = requests.get(NYC_311_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001
        # Non-blocking: 311 is a backup lane; do not crash the orchestrator.
        print(f"[public_data] NYC 311 fetch failed (non-blocking): {exc}")
        return []


def record_to_text(record: dict) -> tuple[str, str | None]:
    """
    Concatenate useful text fields from a 311 record into a single string
    and return the incident ZIP code separately for fallback use.
    """
    zip_code = record.get("incident_zip")
    text = " ".join(
        str(record.get(k, ""))
        for k in ["complaint_type", "descriptor", "borough", "location_type"]
    )
    return text, zip_code
