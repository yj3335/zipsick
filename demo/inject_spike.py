# demo/inject_spike.py
# Inserts a controlled set of synthetic signals for a given ZIP/symptom.
# Used during the live demo to reliably trigger the anomaly engine.
# All records are marked synthetic=True and are clearly distinguishable in queries.

import argparse
import os
import random
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from ingestion.models import OutbreakSignal
from storage.clickhouse import insert_signals

TEXTS = [
    "Everyone in my building in 10014 has a stomach bug.",
    "Four people got food poisoning after dinner near West Village 10014.",
    "Throwing up all night. Anyone else in 10014 sick?",
    "A lot of GI complaints around 10014 today.",
    "Norovirus? My whole floor is sick in 10014.",
]

SOURCE_TYPES = ["nimble_demo", "reddit_demo", "nyc_311_demo"]


def inject(zip_code: str, symptom: str, count: int) -> None:
    now = datetime.now(timezone.utc)
    run_id = os.environ.get("DEMO_RUN_ID", "run_demo")
    signals = []

    for _ in range(count):
        signals.append(
            OutbreakSignal(
                event_id=f"demo_{uuid4().hex[:16]}",
                run_id=run_id,
                timestamp=now - timedelta(minutes=random.randint(0, 120)),
                zip=zip_code,
                symptom=symptom,
                source_type=random.choice(SOURCE_TYPES),
                source_url="https://example.com/demo-public-source",
                evidence_text=random.choice(TEXTS),
                confidence=0.9,
                synthetic=True,
            )
        )

    insert_signals(signals)
    print(f"[inject_spike] Injected {count} synthetic signals — ZIP={zip_code}, symptom={symptom}, run_id={run_id}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser(description="Inject a controlled demo spike.")
    parser.add_argument("--zip", default="10014", help="Target ZIP code.")
    parser.add_argument("--symptom", default="gi", help="Symptom category.")
    parser.add_argument("--count", type=int, default=15, help="Number of signals to inject.")
    args = parser.parse_args()
    inject(args.zip, args.symptom, args.count)
