# anomaly/engine.py
# Runs the anomaly SQL against ClickHouse and routes each hit to the alert orchestrator.

import argparse
import os
import pathlib
from storage.clickhouse import client
from actions.orchestrator import handle_anomaly

ANOMALY_SQL = (pathlib.Path(__file__).parent.parent / "storage" / "anomaly.sql").read_text(encoding="utf-8")


_SENTINEL_Z = "z_score >= 2.5"
_SENTINEL_N = "recent.recent_count >= 5"


def run_once(demo: bool = False) -> list:
    """
    Execute the anomaly query with the appropriate thresholds.
    demo=True uses lower thresholds so the controlled spike always triggers.
    """
    if _SENTINEL_Z not in ANOMALY_SQL or _SENTINEL_N not in ANOMALY_SQL:
        raise RuntimeError(
            "anomaly.sql is missing expected threshold sentinels — "
            f"expected '{_SENTINEL_Z}' and '{_SENTINEL_N}'. "
            "Check that storage/anomaly.sql has not been hand-edited."
        )

    z_threshold = os.environ.get("DEMO_Z_THRESHOLD" if demo else "ANOMALY_Z_THRESHOLD", "2.5")
    min_count = os.environ.get("DEMO_MIN_COUNT" if demo else "ANOMALY_MIN_COUNT", "5")

    sql = ANOMALY_SQL.replace(_SENTINEL_Z, f"z_score >= {z_threshold}").replace(
        _SENTINEL_N, f"recent.recent_count >= {min_count}"
    )
    sql = sql.strip().rstrip(";")

    rows = client().query(sql).named_results()
    return [handle_anomaly(row) for row in rows]


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run anomaly detection once.")
    parser.add_argument("--demo", action="store_true", help="Use demo thresholds.")
    args = parser.parse_args()
    results = run_once(args.demo)
    print(f"[anomaly.engine] processed {len(results)} anomalies.")
