# Neighborhood Outbreak Early Warning - Verified One-Stop Implementation Guide

> **Purpose**: This is the build spec for the hackathon project. A developer should be able to implement, demo, and submit from this document alone.
>
> **Project**: An autonomous public-health signal agent that monitors verified public/open-web sources, detects ZIP-level symptom anomalies, verifies them through an aggregate-only clinical adapter, notifies operators, publishes citeable context, and exposes confirmed alert packages behind payment rails.
>
> **Safety line**: This is public-good outbreak awareness, not diagnosis, not individual surveillance, and not automated medical advice.

---

## 0. What Must Be True For Judges

| Rubric | What The Build Must Prove |
|---|---|
| **Idea** | Earlier public-health awareness that complements official surveillance by adding public/open-web signal. |
| **Autonomy** | The agent runs `observe -> extract -> store -> score -> verify -> act -> publish -> monetize` without manual decisions. |
| **Technical Implementation** | Real ingestion, anomaly math, aggregate verification, audit trail, Slack action, publication, and paid alert access all work. |
| **Tool Use** | Show at least 3 sponsor tools. Target: Nimble, ClickHouse, Datadog, Senso/cited.md, x402/CDP. |
| **Presentation** | A 3-minute demo starts on the working agent, not slides. |

### Six Proof Artifacts

The demo must visibly show:

1. **Nimble/open-web proof**: one real public page/search result becomes a structured signal.
2. **Autonomy proof**: `/status` shows a run ID and timeline advancing.
3. **Math proof**: ClickHouse shows `recent_count`, `baseline_avg`, `baseline_stddev`, `z_score`.
4. **Safety proof**: clinical verification returns aggregate count only.
5. **Action proof**: Slack, Datadog, and Senso/cited.md update automatically.
6. **Commerce proof**: confirmed alert endpoint returns `402 Payment Required`, then `200 OK` after demo payment.

---

## 1. Verified External Assumptions

Use this table to avoid brittle or overclaimed integrations.

| Area | Verified Build Decision |
|---|---|
| **CDC claim** | Do not say "CDC takes 2-6 weeks" or "CDC publishes monthly." Say CDC NSSP/BioSense supports near-real-time ED surveillance for participating facilities, and this project complements official systems with earlier public/open-web signals. |
| **Nimble** | Use Nimble as the sponsor open-web collection layer. Current Nimble docs emphasize API-key/SDK style flows; do not hard-code only the older `api.webit.live` Basic Auth path unless your hackathon credentials specifically use it. Build an adapter with `NIMBLE_MODE=http|mock`, and add SDK mode only if the sponsor gives SDK credentials during the event. |
| **ClickHouse** | Use ClickHouse for event storage, baseline aggregation, and anomaly SQL. This is the most defensible core infra choice. |
| **Datadog** | Use structured logs and metrics with one `run_id`/`alert_id` across the full pipeline. If full Datadog API setup is slow, ship JSON logs and a dashboard/log view. |
| **Senso/cited.md** | Treat Senso publishing as a real integration when credentials exist. If unavailable, use a local cited.md-compatible markdown fallback and clearly say it is the fallback. |
| **x402/CDP** | Implement the HTTP payment pattern: `402 Payment Required -> payment/demo header -> 200 OK`. Use real SDK/testnet verification if available, otherwise label it as a demo/test payment gate. |
| **Yelp** | Do not rely on scraping Yelp as a core MVP dependency. Yelp's official API returns limited review excerpts, and scraping may be brittle. Use Yelp as prior-art context or optional source only. |
| **Nextdoor** | Do not rely on Nextdoor for MVP. Public access is inconsistent and often auth/JS-dependent. Keep it optional. |
| **Reddit** | Use public subreddit JSON/API or Nimble-fetched public pages only. Add a user-agent if using Reddit endpoints. |
| **NYC 311 / NYC Open Data** | Use as reliable public-data input for demo seeding and real public complaints. This is safer than depending on live social content. |
| **Clinical data** | For hackathon MVP, use an aggregate-only clinical verifier mock/adapter. Do not claim real EHR or ED note access unless actually integrated. |

---

## 2. Data Sources

### MVP Sources

| Source | Purpose | Implementation | Reliability |
|---|---|---|---|
| **Nimble open-web page/search** | Sponsor/open-web proof. | Fetch one public page/search result and extract symptom/location evidence. | Required for demo proof. |
| **NYC 311 public complaints** | Reliable public civic signal. | Query NYC Open Data/Socrata for complaint records and text fields, then map to ZIP/symptom when relevant. | Reliable fallback. |
| **Synthetic controlled spike** | Deterministic live demo trigger. | Insert through the same `insert_signals()` path with `synthetic=true`. | Required for 3-minute demo. |
| **Clinical aggregate mock** | Safety/confirmation proof. | `10014/gi -> count=2`, unrelated ZIPs -> `count=0`. | Required unless real partner exists. |

### Optional Sources

| Source | When To Use |
|---|---|
| Reddit public subreddit JSON/pages | Good if accessible during demo. Mark rate-limit failures as non-blocking. |
| Yelp Fusion API | Optional business/review excerpt context only. Do not make it the sole outbreak signal. |
| School attendance data | Good public-health context if you can map school/location to ZIP. Keep optional unless implemented. |
| Local news pages | Optional open-web evidence through Nimble. |

---

## 3. End-To-End Architecture

```text
Sources
  -> Nimble collector / public-data collector
  -> Extractor and normalizer
  -> ClickHouse outbreak_signals
  -> ClickHouse anomaly query
  -> Clinical aggregate verifier
  -> Alert orchestrator
  -> Datadog logs/metrics + Slack alert
  -> Senso/cited.md publisher
  -> x402 paid alert endpoint
  -> Agent control panel /status
```

### Runtime Processes

| Process | Command | Responsibility |
|---|---|---|
| API/control panel | `uvicorn app:app --reload --port 8000` | `/status`, `/alerts/confirmed/{id}`, payment gate. |
| Ingestion | `python -m ingestion.orchestrator` | Nimble/public-data polling and ClickHouse inserts. |
| Anomaly engine | `python -m anomaly.engine --demo` | Runs anomaly query and calls orchestrator. |
| Demo spike | `python demo/inject_spike.py --zip 10014 --symptom gi --count 15` | Controlled spike through real write path. |

---

## 4. Environment

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn requests clickhouse-connect pydantic python-dotenv slack-sdk datadog-api-client apscheduler
```

Optional:

```bash
pip install cdp-sdk
```

### `.env.example`

```dotenv
APP_ENV=demo

# Nimble
NIMBLE_MODE=mock
NIMBLE_API_KEY=
NIMBLE_USERNAME=
NIMBLE_PASSWORD=
NIMBLE_API_URL=

# ClickHouse
CH_HOST=
CH_PORT=8443
CH_USER=default
CH_PASSWORD=
CH_DATABASE=outbreak

# Datadog
DD_API_KEY=
DD_APP_KEY=
DD_SITE=datadoghq.com

# Slack
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=

# Senso / cited.md
SENSO_API_KEY=
SENSO_PUBLISH_URL=

# x402 / payment
X402_ENABLED=true
DEMO_PRICE_USD=0.25
SERVICE_WALLET_ADDRESS=

# Demo
DEMO_RUN_ID=run_demo
ANOMALY_Z_THRESHOLD=2.5
ANOMALY_MIN_COUNT=5
DEMO_Z_THRESHOLD=1.8
DEMO_MIN_COUNT=3
```

---

## 5. Project Structure

```text
outbreak-early-warning/
  .env.example
  README.md
  requirements.txt
  app.py
  config/
    sources.py
    thresholds.py
  ingestion/
    models.py
    extractor.py
    nimble_client.py
    public_data.py
    orchestrator.py
  storage/
    clickhouse.py
    schema.sql
    init_schema.py
  anomaly/
    engine.py
  verification/
    clinical_aggregate.py
  actions/
    orchestrator.py
    slack_alerts.py
    senso_publish.py
  observability/
    datadog.py
  demo/
    seed_baseline.py
    inject_spike.py
  tests/
    test_extractor.py
    test_anomaly.py
    test_payment.py
```

---

## 6. Data Contracts

### Pydantic Models

```python
# ingestion/models.py

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Symptom = Literal["gi", "respiratory", "neuro", "rash", "general"]
ClinicalStatus = Literal["candidate", "confirmed", "suppressed"]


class OutbreakSignal(BaseModel):
    event_id: str
    run_id: str | None = None
    timestamp: datetime
    zip: str = Field(pattern=r"^\d{5}$")
    symptom: Symptom
    source_type: str
    source_url: str | None = None
    evidence_text: str = Field(max_length=600)
    confidence: float = Field(ge=0, le=1)
    synthetic: bool = False


class AlertPackage(BaseModel):
    alert_id: str
    run_id: str
    created_at: datetime
    zip: str
    symptom: Symptom
    recent_count: int
    baseline_avg: float
    baseline_stddev: float
    z_score: float
    clinical_status: ClinicalStatus
    clinical_aggregate_count: int
    source_count: int
    source_diversity: int
    source_urls: list[str]
    decision_reason: str
    datadog_trace_id: str | None = None
    senso_url: str | None = None
    payment_status: str = "unpaid"
```

### ClickHouse Schema

```sql
CREATE DATABASE IF NOT EXISTS outbreak;

CREATE TABLE IF NOT EXISTS outbreak.outbreak_signals
(
    event_id String,
    run_id Nullable(String),
    timestamp DateTime,
    zip LowCardinality(String),
    symptom LowCardinality(String),
    source_type LowCardinality(String),
    source_url Nullable(String),
    evidence_text String,
    confidence Float32,
    synthetic Bool,
    hour DateTime MATERIALIZED toStartOfHour(timestamp),
    day Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (zip, symptom, timestamp)
TTL timestamp + INTERVAL 180 DAY;

CREATE TABLE IF NOT EXISTS outbreak.alerts
(
    alert_id String,
    run_id String,
    created_at DateTime,
    zip LowCardinality(String),
    symptom LowCardinality(String),
    recent_count UInt32,
    baseline_avg Float32,
    baseline_stddev Float32,
    z_score Float32,
    clinical_status LowCardinality(String),
    clinical_aggregate_count UInt32,
    source_count UInt32,
    source_diversity UInt32,
    source_urls Array(String),
    decision_reason String,
    datadog_trace_id Nullable(String),
    senso_url Nullable(String),
    payment_status LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (created_at, zip, symptom);
```

---

## 7. Storage Client

```python
# storage/clickhouse.py

import os
import clickhouse_connect


def client():
    return clickhouse_connect.get_client(
        host=os.environ["CH_HOST"],
        port=int(os.environ.get("CH_PORT", "8443")),
        username=os.environ["CH_USER"],
        password=os.environ["CH_PASSWORD"],
        database=os.environ.get("CH_DATABASE", "outbreak"),
        secure=True,
    )


def insert_signals(signals):
    rows = [[
        s.event_id,
        s.run_id,
        s.timestamp,
        s.zip,
        s.symptom,
        s.source_type,
        s.source_url,
        s.evidence_text,
        s.confidence,
        s.synthetic,
    ] for s in signals]

    if rows:
        client().insert(
            "outbreak_signals",
            rows,
            column_names=[
                "event_id", "run_id", "timestamp", "zip", "symptom",
                "source_type", "source_url", "evidence_text",
                "confidence", "synthetic",
            ],
        )


def insert_alert(package):
    client().insert("alerts", [[
        package.alert_id,
        package.run_id,
        package.created_at,
        package.zip,
        package.symptom,
        package.recent_count,
        package.baseline_avg,
        package.baseline_stddev,
        package.z_score,
        package.clinical_status,
        package.clinical_aggregate_count,
        package.source_count,
        package.source_diversity,
        package.source_urls,
        package.decision_reason,
        package.datadog_trace_id,
        package.senso_url,
        package.payment_status,
    ]], column_names=[
        "alert_id", "run_id", "created_at", "zip", "symptom",
        "recent_count", "baseline_avg", "baseline_stddev", "z_score",
        "clinical_status", "clinical_aggregate_count", "source_count",
        "source_diversity", "source_urls", "decision_reason",
        "datadog_trace_id", "senso_url", "payment_status",
    ])


def get_alert(alert_id: str):
    rows = client().query(
        """
        SELECT *
        FROM alerts
        WHERE alert_id = {alert_id:String}
        ORDER BY created_at DESC
        LIMIT 1
        """,
        parameters={"alert_id": alert_id},
    ).named_results()
    return rows[0] if rows else None


def mark_alert_paid(alert_id: str):
    # Hackathon-safe implementation: insert an updated copy in an append-only table.
    # Production should use a ReplacingMergeTree or dedicated payment_events table.
    alert = get_alert(alert_id)
    if not alert:
        return None
    alert["payment_status"] = "paid"
    client().insert(
        "alerts",
        [[alert[c] for c in alert.keys()]],
        column_names=list(alert.keys()),
    )
    return alert
```

---

## 8. Extractor

```python
# ingestion/extractor.py

import hashlib
import re
from datetime import datetime, timezone
from ingestion.models import OutbreakSignal

SYMPTOMS = {
    "gi": [r"food poisoning", r"vomit", r"nausea", r"diarrhea", r"stomach bug", r"norovirus", r"gastro"],
    "respiratory": [r"cough", r"sore throat", r"flu", r"covid", r"rsv", r"shortness of breath"],
    "rash": [r"rash", r"hives", r"itching"],
    "general": [r"fever", r"chills", r"body aches", r"outbreak", r"cluster"],
}

NYC_ZIP = re.compile(r"\b(10[0-2]\d{2}|103\d{2}|104\d{2}|11[1-6]\d{2})\b")


def extract_signals(text: str, source_type: str, source_url: str | None, fallback_zip: str | None = None, run_id: str | None = None):
    low = text.lower()
    zip_match = NYC_ZIP.search(text)
    zip_code = zip_match.group(1) if zip_match else fallback_zip
    if not zip_code:
        return []

    signals = []
    for symptom, patterns in SYMPTOMS.items():
        if any(re.search(pattern, low) for pattern in patterns):
            evidence = " ".join(text.split())[:600]
            event_id = hashlib.sha256(f"{source_url}|{symptom}|{evidence}".encode()).hexdigest()[:24]
            signals.append(OutbreakSignal(
                event_id=event_id,
                run_id=run_id,
                timestamp=datetime.now(timezone.utc),
                zip=zip_code,
                symptom=symptom,
                source_type=source_type,
                source_url=source_url,
                evidence_text=evidence,
                confidence=0.75,
                synthetic=False,
            ))
    return signals
```

---

## 9. Nimble Collector

Build the Nimble adapter to support real credentials, HTTP fallback, and mock mode. This prevents the project from breaking if sponsor credentials differ from public docs.

```python
# ingestion/nimble_client.py

import base64
import os
import requests


def fetch_public_page(url: str) -> str:
    mode = os.environ.get("NIMBLE_MODE", "mock")

    if mode == "mock":
        return "Food poisoning reports near West Village 10014. Multiple people mention vomiting and stomach bug."

    if mode == "http":
        api_url = os.environ["NIMBLE_API_URL"]
        headers = {"Content-Type": "application/json"}
        if os.environ.get("NIMBLE_API_KEY"):
            headers["Authorization"] = f"Bearer {os.environ['NIMBLE_API_KEY']}"
        elif os.environ.get("NIMBLE_USERNAME") and os.environ.get("NIMBLE_PASSWORD"):
            token = base64.b64encode(
                f"{os.environ['NIMBLE_USERNAME']}:{os.environ['NIMBLE_PASSWORD']}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {token}"

        response = requests.post(
            api_url,
            headers=headers,
            json={"url": url, "render": True, "country": "US", "locale": "en"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("html_content") or data.get("content") or data.get("body") or ""

    raise ValueError(f"Unsupported NIMBLE_MODE={mode}")
```

---

## 10. Public Data Collector

Use public-data collection as the reliable non-sponsor lane. Keep the implementation simple: fetch records, concatenate useful text fields, then run the same extractor.

```python
# ingestion/public_data.py

import requests


def fetch_nyc_311_records(limit: int = 25):
    url = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
    params = {
        "$limit": limit,
        "$order": "created_date DESC",
        "$select": "created_date,complaint_type,descriptor,incident_zip,borough,location_type",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def record_to_text(record: dict) -> tuple[str, str | None]:
    zip_code = record.get("incident_zip")
    text = " ".join(str(record.get(k, "")) for k in ["complaint_type", "descriptor", "borough", "location_type"])
    return text, zip_code
```

Note: 311 is not guaranteed to contain outbreak language at demo time. Treat it as reliable public-data plumbing, not the sole trigger.

---

## 11. Ingestion Orchestrator

```python
# ingestion/orchestrator.py

import os
from ingestion.extractor import extract_signals
from ingestion.nimble_client import fetch_public_page
from ingestion.public_data import fetch_nyc_311_records, record_to_text
from observability.datadog import log_event, emit_metric
from storage.clickhouse import insert_signals


def ingest_once(run_id: str | None = None):
    signals = []

    # Sponsor/open-web proof.
    nimble_url = "https://www.nyc.gov/site/doh/health/health-topics/food-poisoning.page"
    nimble_text = fetch_public_page(nimble_url)
    signals.extend(extract_signals(nimble_text, "nimble_open_web", nimble_url, fallback_zip="10014", run_id=run_id))

    # Reliable public-data lane.
    for record in fetch_nyc_311_records(limit=25):
        text, zip_code = record_to_text(record)
        signals.extend(extract_signals(text, "nyc_311_public_data", None, fallback_zip=zip_code, run_id=run_id))

    insert_signals(signals)
    emit_metric("outbreak.events_ingested", len(signals), tags=[f"run_id:{run_id}"])
    log_event("ingestion_complete", {"run_id": run_id, "signals": len(signals)})
    return signals


if __name__ == "__main__":
    ingest_once(os.environ.get("DEMO_RUN_ID", "run_demo"))
```

---

## 12. Anomaly Detection

### Query

```sql
WITH
recent AS
(
    SELECT
        zip,
        symptom,
        count() AS recent_count,
        count() AS source_count,
        uniqExact(source_type) AS source_diversity,
        groupArrayDistinct(ifNull(source_url, '')) AS source_urls
    FROM outbreak.outbreak_signals
    WHERE timestamp > now() - INTERVAL 6 HOUR
    GROUP BY zip, symptom
),
baseline AS
(
    SELECT
        zip,
        symptom,
        avg(cnt) AS baseline_avg,
        stddevPop(cnt) AS baseline_stddev
    FROM
    (
        SELECT zip, symptom, toStartOfHour(timestamp) AS hour, count() AS cnt
        FROM outbreak.outbreak_signals
        WHERE timestamp BETWEEN now() - INTERVAL 90 DAY AND now() - INTERVAL 6 HOUR
        GROUP BY zip, symptom, hour
    )
    GROUP BY zip, symptom
)
SELECT
    recent.zip,
    recent.symptom,
    recent.recent_count,
    recent.source_count,
    recent.source_diversity,
    recent.source_urls,
    baseline.baseline_avg,
    greatest(baseline.baseline_stddev, 1.0) AS baseline_stddev,
    round((recent.recent_count - baseline.baseline_avg) / greatest(baseline.baseline_stddev, 1.0), 2) AS z_score
FROM recent
INNER JOIN baseline USING (zip, symptom)
WHERE recent.recent_count >= 5
  AND z_score >= 2.5
ORDER BY z_score DESC;
```

### Engine Skeleton

```python
# anomaly/engine.py

import argparse
import os
from storage.clickhouse import client
from actions.orchestrator import handle_anomaly

ANOMALY_SQL = open("storage/anomaly.sql", "r", encoding="utf-8").read()


def run_once(demo: bool = False):
    threshold = os.environ.get("DEMO_Z_THRESHOLD" if demo else "ANOMALY_Z_THRESHOLD", "2.5")
    min_count = os.environ.get("DEMO_MIN_COUNT" if demo else "ANOMALY_MIN_COUNT", "5")
    sql = ANOMALY_SQL.replace("z_score >= 2.5", f"z_score >= {threshold}").replace("recent.recent_count >= 5", f"recent.recent_count >= {min_count}")
    rows = client().query(sql).named_results()
    return [handle_anomaly(row) for row in rows]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    run_once(args.demo)
```

---

## 13. Clinical Aggregate Verification

This is a boundary, not a fake claim. The production version would run inside a hospital environment; the MVP demonstrates the contract.

```python
# verification/clinical_aggregate.py

from dataclasses import dataclass


@dataclass
class ClinicalAggregateResult:
    status: str
    count: int
    min_required: int
    note: str


def verify_clinical_aggregate(zip_code: str, symptom: str, window_hours: int = 6) -> ClinicalAggregateResult:
    demo_counts = {
        ("10014", "gi"): 2,
    }
    count = demo_counts.get((zip_code, symptom), 0)
    min_required = 2
    status = "confirmed" if count >= min_required else "suppressed"
    reason = "aggregate clinical match found" if status == "confirmed" else "no matching aggregate clinical signal"
    return ClinicalAggregateResult(status=status, count=count, min_required=min_required, note=reason)
```

---

## 14. Alert Orchestrator

```python
# actions/orchestrator.py

import os
from datetime import datetime, timezone
from uuid import uuid4
from ingestion.models import AlertPackage
from verification.clinical_aggregate import verify_clinical_aggregate
from actions.slack_alerts import send_slack_alert
from actions.senso_publish import publish_cited_alert
from observability.datadog import log_event, emit_metric
from storage.clickhouse import insert_alert


def handle_anomaly(row):
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
        emit_metric("outbreak.alert.confirmed", 1, tags=[f"zip:{package.zip}", f"symptom:{package.symptom}"])
    else:
        emit_metric("outbreak.alert.suppressed", 1, tags=[f"zip:{package.zip}", f"symptom:{package.symptom}"])

    insert_alert(package)
    log_event(f"alert_{package.clinical_status}", package.model_dump())
    return package
```

---

## 15. Slack Alert

```python
# actions/slack_alerts.py

import os
from slack_sdk import WebClient


def send_slack_alert(package):
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        return

    text = (
        "*OUTBREAK SIGNAL CONFIRMED*\n"
        f"*Alert*: `{package.alert_id}`\n"
        f"*ZIP*: {package.zip}\n"
        f"*Symptom*: {package.symptom}\n"
        f"*Z-score*: {package.z_score:.2f}\n"
        f"*Clinical aggregate*: {package.clinical_aggregate_count} matching presentations\n"
        f"*Sources*: {package.source_count}\n"
        f"*Source diversity*: {package.source_diversity}\n"
        f"*Citeable summary*: {package.senso_url or 'pending'}\n"
        "_Public-facing advisory is drafted for authorized review._"
    )
    WebClient(token=token).chat_postMessage(channel=channel, text=text)
```

---

## 16. Datadog Observability

### Required Events/Metrics

- `ingestion_complete`
- `anomaly_detected`
- `alert_confirmed`
- `alert_suppressed`
- `outbreak.events_ingested`
- `outbreak.alert.confirmed`
- `outbreak.alert.suppressed`
- `outbreak.payment.required`
- `outbreak.payment.completed`
- `outbreak.publisher.senso.success`

```python
# observability/datadog.py

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbreak-agent")


def log_event(event_name: str, payload: dict):
    logger.info(json.dumps({"event": event_name, **payload}, default=str))


def emit_metric(name: str, value: float, tags: list[str] | None = None):
    logger.info(json.dumps({"metric": name, "value": value, "tags": tags or []}))
```

For the demo, structured logs visible in Datadog are acceptable. Full metric ingestion is better but not required for the project story.

---

## 17. Senso / cited.md Publisher

```python
# actions/senso_publish.py

import os
import pathlib
import requests
from observability.datadog import emit_metric, log_event


def publish_cited_alert(package) -> str | None:
    url = os.environ.get("SENSO_PUBLISH_URL")
    api_key = os.environ.get("SENSO_API_KEY")
    payload = {
        "title": f"Confirmed community illness signal in ZIP {package.zip}",
        "summary": (
            f"Elevated {package.symptom} activity detected in ZIP {package.zip}. "
            f"Recent count={package.recent_count}, baseline={package.baseline_avg:.2f}, "
            f"z={package.z_score:.2f}, aggregate clinical count={package.clinical_aggregate_count}."
        ),
        "citations": package.source_urls,
        "metadata": package.model_dump(),
    }

    if url and api_key:
        response = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=30)
        response.raise_for_status()
        published = response.json().get("url")
        emit_metric("outbreak.publisher.senso.success", 1, tags=[f"alert_id:{package.alert_id}"])
        return published

    pathlib.Path("public/alerts").mkdir(parents=True, exist_ok=True)
    path = pathlib.Path(f"public/alerts/{package.alert_id}.md")
    path.write_text(
        f"# {payload['title']}\n\n{payload['summary']}\n\nSources:\n" +
        "\n".join(f"- {u}" for u in package.source_urls),
        encoding="utf-8",
    )
    log_event("senso_fallback_written", {"alert_id": package.alert_id, "path": str(path)})
    return str(path)
```

Do not claim Senso was used if only the fallback file was written. In the demo, say "Senso path if credentials are live; local cited fallback otherwise."

---

## 18. API, Control Panel, And x402 Gate

```python
# app.py

import os
from fastapi import FastAPI, Header, HTTPException
from storage.clickhouse import get_alert, mark_alert_paid

app = FastAPI(title="Neighborhood Outbreak Early Warning")

RUN_STATE = {
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


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/status")
def status():
    return RUN_STATE


@app.get("/")
def control_panel():
    return RUN_STATE


@app.get("/alerts/confirmed/{alert_id}")
def get_confirmed_alert(alert_id: str, x_payment: str | None = Header(default=None)):
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    if alert["clinical_status"] != "confirmed":
        raise HTTPException(status_code=403, detail="only confirmed alerts are available")

    if os.environ.get("X402_ENABLED", "true").lower() == "true" and not x_payment:
        raise HTTPException(
            status_code=402,
            detail={
                "payment_protocol": "x402",
                "amount_usd": os.environ.get("DEMO_PRICE_USD", "0.25"),
                "resource": f"/alerts/confirmed/{alert_id}",
                "description": "Confirmed outbreak alert package",
            },
        )

    return mark_alert_paid(alert_id)
```

### Payment Demo

```bash
# Before payment/demo header
curl -i http://localhost:8000/alerts/confirmed/alert_abc123

# After payment/demo header
curl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/alert_abc123
```

---

## 19. Demo Scripts

### Controlled Spike

```python
# demo/inject_spike.py

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


def inject(zip_code: str, symptom: str, count: int):
    now = datetime.now(timezone.utc)
    run_id = os.environ.get("DEMO_RUN_ID", "run_demo")
    signals = []
    for _ in range(count):
        signals.append(OutbreakSignal(
            event_id=f"demo_{uuid4().hex[:16]}",
            run_id=run_id,
            timestamp=now - timedelta(minutes=random.randint(0, 120)),
            zip=zip_code,
            symptom=symptom,
            source_type=random.choice(["nimble_demo", "reddit_demo", "nyc_311_demo"]),
            source_url="https://example.com/demo-public-source",
            evidence_text=random.choice(TEXTS),
            confidence=0.9,
            synthetic=True,
        ))
    insert_signals(signals)
    print(f"Injected {count} controlled demo signals for ZIP {zip_code}, symptom={symptom}, run_id={run_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default="10014")
    parser.add_argument("--symptom", default="gi")
    parser.add_argument("--count", type=int, default=15)
    args = parser.parse_args()
    inject(args.zip, args.symptom, args.count)
```

### Baseline Seed

Seed low historical counts for ZIP 10014 so the anomaly query has a baseline. Keep these records `synthetic=true` and old timestamps.

```bash
python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2
```

---

## 20. Evidence Ledger Queries

### Live vs Controlled Data

```sql
SELECT
    ifNull(run_id, 'none') AS run_id,
    synthetic,
    source_type,
    count() AS events,
    groupArrayDistinct(ifNull(source_url, '')) AS example_urls
FROM outbreak.outbreak_signals
WHERE timestamp > now() - INTERVAL 6 HOUR
GROUP BY run_id, synthetic, source_type
ORDER BY synthetic ASC, events DESC;
```

### Latest Alerts

```sql
SELECT
    alert_id,
    zip,
    symptom,
    recent_count,
    baseline_avg,
    baseline_stddev,
    z_score,
    clinical_status,
    clinical_aggregate_count,
    source_diversity,
    payment_status
FROM outbreak.alerts
ORDER BY created_at DESC
LIMIT 10;
```

---

## 21. Demo Runbook

### One-Time Setup

```bash
python -m storage.init_schema
python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2
```

### Live Demo

```bash
# Terminal 1
uvicorn app:app --reload --port 8000

# Terminal 2
python -m ingestion.orchestrator

# Terminal 3
python demo/inject_spike.py --zip 10014 --symptom gi --count 15

# Terminal 4
python -m anomaly.engine --demo
```

### Browser Tabs

1. `http://localhost:8000/status`
2. ClickHouse query console with anomaly and evidence-ledger queries.
3. Datadog logs filtered to `outbreak-agent` or `run_id:run_demo`.
4. Slack channel.
5. Senso/cited.md page or local cited fallback file.
6. `http://localhost:8000/alerts/confirmed/{alert_id}`.

---

## 22. Tests

Minimum acceptance tests:

- Extractor maps "food poisoning in 10014" to `symptom=gi`, `zip=10014`.
- Extractor returns no signal when no ZIP and no fallback ZIP exist.
- Nimble mock returns one extractable signal.
- NYC 311 collector handles empty or irrelevant records without crashing.
- ClickHouse insert writes one `synthetic=false` signal.
- Spike injector writes `synthetic=true` signals.
- Evidence ledger query shows both real and controlled signals.
- Anomaly query returns `10014/gi` after baseline + spike.
- Clinical verifier confirms `10014/gi` and suppresses `10012/gi`.
- Alert orchestrator writes confirmed and suppressed alerts.
- Slack function no-ops safely without token.
- Senso publisher returns real URL or writes fallback.
- x402 endpoint returns 402 without payment header and 200 with `x-payment`.

---

## 23. Devpost Checklist

- [ ] Public GitHub repo.
- [ ] README has architecture diagram, sponsor-tool table, safety guardrails, and CDC language.
- [ ] 3-minute demo video opens on `/status`.
- [ ] Video shows one `synthetic=false` Nimble/open-web signal.
- [ ] Video shows controlled spike marked `synthetic=true`.
- [ ] Video shows ClickHouse anomaly math.
- [ ] Video shows aggregate clinical confirmation.
- [ ] Video shows Slack and Datadog action.
- [ ] Video shows Senso/cited.md publication or clearly labeled fallback.
- [ ] Video shows x402 `402 -> payment -> 200`.
- [ ] Devpost description names Nimble, ClickHouse, Datadog, Senso/cited.md, and x402/CDP.

---

## 24. Devpost Summary

> Neighborhood Outbreak Early Warning is an autonomous public-health signal agent. It watches public/open-web signals for abnormal symptom clusters, verifies anomalies against privacy-preserving aggregate clinical counts, and routes confirmed alerts to epidemiology teams. We use Nimble for open-web collection, ClickHouse for real-time anomaly detection, Datadog for observability, Senso/cited.md for grounded publication, and x402/CDP for agent-to-agent payment access to confirmed alert packages. The system complements official surveillance: no diagnosis, no patient-level PHI, and public-facing health language is drafted for authorized review.

---

## 25. Source References

- CDC NSSP/BioSense: https://www.cdc.gov/nssp/php/about/about-nssp-and-the-biosense-platform.html
- CDC NNDSS infectious disease tables: https://www.cdc.gov/nndss/infectious-disease/
- CDC FoodCORE Yelp outbreak example: https://archive.cdc.gov/www_cdc_gov/foodcore/successes/nyc-yelp.html
- NYC Open Data 311 endpoint: https://data.cityofnewyork.us/resource/erm2-nwe9.json
- ClickHouse docs: https://clickhouse.com/docs
- Datadog docs: https://docs.datadoghq.com/
- Slack `chat.postMessage`: https://api.slack.com/methods/chat.postMessage
- x402: https://www.x402.org/
- Nimble docs: https://docs.nimbleway.com/
- Senso docs: https://docs.senso.ai/
