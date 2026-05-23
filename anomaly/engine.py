# anomaly/engine.py
# Runs the anomaly SQL against ClickHouse and routes each hit to the alert orchestrator.

import argparse
import os
import pathlib
from storage.clickhouse import client
from actions.orchestrator import handle_anomaly

ANOMALY_SQL = (pathlib.Path(__file__).parent.parent / "storage" / "anomaly.sql").read_text(encoding="utf-8")


def run_once(demo: bool = False) -> list:
    """
    Execute the anomaly query with the appropriate thresholds.
    demo=True uses lower thresholds so the controlled spike always triggers.
    """
    z_threshold = os.environ.get("DEMO_Z_THRESHOLD" if demo else "ANOMALY_Z_THRESHOLD", "2.5")
    min_count = os.environ.get("DEMO_MIN_COUNT" if demo else "ANOMALY_MIN_COUNT", "5")

    sql = ANOMALY_SQL.replace("z_score >= 2.5", f"z_score >= {z_threshold}").replace(
        "recent.recent_count >= 5", f"recent.recent_count >= {min_count}"
    )

    rows = client().query(sql).named_results()
    return [handle_anomaly(row) for row in rows]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run anomaly detection once.")
    parser.add_argument("--demo", action="store_true", help="Use demo thresholds.")
    args = parser.parse_args()
    results = run_once(args.demo)
    print(f"[anomaly.engine] processed {len(results)} anomalies.")
