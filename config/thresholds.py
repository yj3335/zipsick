# config/thresholds.py
# Anomaly detection thresholds; overridden by environment variables.

import os

ANOMALY_Z_THRESHOLD: float = float(os.environ.get("ANOMALY_Z_THRESHOLD", "2.5"))
ANOMALY_MIN_COUNT: int = int(os.environ.get("ANOMALY_MIN_COUNT", "5"))

DEMO_Z_THRESHOLD: float = float(os.environ.get("DEMO_Z_THRESHOLD", "1.8"))
DEMO_MIN_COUNT: int = int(os.environ.get("DEMO_MIN_COUNT", "3"))

CLINICAL_MIN_AGGREGATE: int = 2
SIGNAL_WINDOW_HOURS: int = 6
BASELINE_DAYS: int = 90
