# observability/datadog.py
# Structured logging and metrics.
# Ships JSON logs to stdout; Datadog agent or log forwarder can tail them.
# For a full Datadog integration, swap logger.info calls with the datadog-api-client SDK.

import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("outbreak-agent")

# Add file handler for Datadog Agent to tail
file_handler = logging.FileHandler("zipsick.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(file_handler)


def log_event(event_name: str, payload: dict) -> None:
    """Emit a structured JSON log line. Each log is indexed by Datadog as a log entry."""
    logger.info(json.dumps({"event": event_name, **payload}, default=str))


def emit_metric(name: str, value: float, tags: list[str] | None = None) -> None:
    """
    Emit a metric as a structured log line.
    Replace with datadog_api_client.v2.api.metrics_api calls when DD credentials are available.
    """
    logger.info(json.dumps({"metric": name, "value": value, "tags": tags or []}))
