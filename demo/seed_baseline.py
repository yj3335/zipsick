# demo/seed_baseline.py
# Populates 90 days of low-count historical synthetic signals so the anomaly query
# has a meaningful baseline average/stddev to compare against the live demo spike.
# All records are marked synthetic=True.

import argparse
import os
import random
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from ingestion.models import OutbreakSignal
from storage.clickhouse import insert_signals


def seed(zip_code: str, symptom: str, days: int, avg_per_day: float) -> None:
    run_id = os.environ.get("DEMO_RUN_ID", "run_demo")
    now = datetime.now(timezone.utc)
    signals = []

    for day_offset in range(1, days + 1):
        count_today = max(0, int(random.gauss(avg_per_day, 0.5)))
        for _ in range(count_today):
            ts = now - timedelta(days=day_offset, hours=random.uniform(0, 23))
            signals.append(
                OutbreakSignal(
                    event_id=f"baseline_{uuid4().hex[:16]}",
                    run_id=run_id,
                    timestamp=ts,
                    zip=zip_code,
                    symptom=symptom,
                    source_type="baseline_seed",
                    source_url=None,
                    evidence_text=f"Baseline seed record for ZIP {zip_code} / {symptom}.",
                    confidence=0.5,
                    synthetic=True,
                )
            )

    # Insert in batches of 500 to avoid large single requests.
    batch_size = 500
    for i in range(0, len(signals), batch_size):
        insert_signals(signals[i : i + batch_size])

    print(
        f"[seed_baseline] Inserted {len(signals)} baseline signals — "
        f"ZIP={zip_code}, symptom={symptom}, days={days}, avg_per_day={avg_per_day}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed historical baseline signals.")
    parser.add_argument("--zip", default="10014", help="Target ZIP code.")
    parser.add_argument("--symptom", default="gi", help="Symptom category.")
    parser.add_argument("--days", type=int, default=90, help="Number of days to backfill.")
    parser.add_argument("--avg-per-day", type=float, default=2.0, help="Average signals per day.")
    args = parser.parse_args()
    seed(args.zip, args.symptom, args.days, args.avg_per_day)
