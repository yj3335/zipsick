# Zipsick: Autonomous Public-Health Signal Agent

Catches ZIP-level illness outbreaks early by watching open-web signals before people reach the hospital.

---

## The Problem

Official systems like the CDC NSSP/BioSense platform track Emergency Department visits. That data is solid, but it's downstream. People get sick, then they search, post, and complain online. Then they go to the hospital.

**zipsick** watches the online step. It picks up community posts, civic complaints, and public health pages, turns them into structured signals, scores anomalies against a 90-day baseline, and verifies spikes against aggregate clinical data. Public-health teams get earlier warning.

**On CDC language:** zipsick doesn't replace CDC NSSP or BioSense. CDC surveillance is reliable. This project adds earlier open-web signal alongside it. We don't claim "CDC takes 2-6 weeks."

---

## How It Works

The agent runs the full `observe → extract → store → score → verify → act → publish → monetize` loop on its own. A single `run_id` ties every step together in Datadog.

```
[Nimble open-web + NYC 311 + Reddit]
        │
        ▼
[Extractor: regex ZIP + symptom parser]
        │
        ▼
[ClickHouse: outbreak_signals table]
        │
        ▼
[Anomaly Engine: Z-score SQL]
  (recent_count − baseline_avg) / baseline_stddev
        │
        ▼
[Clinical Verifier: FHIR _summary=count, aggregate only, zero PHI]
        │
       / \
 confirmed  suppressed
      │           │
      ▼           ▼
[Slack + Datadog] [Datadog only]
      │
      ▼
[Senso / cited.md publisher]
      │
      ▼
[x402 Payment Gate → /alerts/confirmed/{id}]
      │
      ▼
[/status: real-time proof checklist]
```

---

## Sponsor Integrations

| Tool | What it does |
|---|---|
| **Nimble** | Fetches public health pages and community sources. Handles IP rotation. Supports Bearer auth, Basic auth, and `NIMBLE_MODE=mock` for offline demos. |
| **ClickHouse** | Stores signals and runs the anomaly query. Holds a 90-day baseline and returns `recent_count`, `baseline_avg`, `baseline_stddev`, and `z_score` in real time. |
| **Datadog** | Logs and metrics for every pipeline stage. Every event carries `run_id` and `alert_id`. Key events: `ingestion_complete`, `anomaly_detected`, `alert_confirmed`, `alert_suppressed`. Key metrics: `outbreak.events_ingested`, `outbreak.alert.confirmed`, `outbreak.payment.completed`. |
| **Senso / cited.md** | Publishes confirmed alerts as citable markdown documents with source links. Falls back to a local `public/alerts/{alert_id}.md` file when credentials aren't set, and labels which path was taken in the logs. |
| **x402 / Coinbase Developer Platform** | Puts a payment gate on the confirmed-alert endpoint. Without a header you get 402 with payment instructions. With `x-payment` proof you get the full alert package. |

---

## Safety

This project doesn't diagnose anything, doesn't access patient records, and doesn't give medical advice.

The FHIR adapter calls `Condition?_summary=count`. It gets back a single integer. No patient IDs, no names, no clinical notes. Just a count.

All public-facing health language is written for authorized review before it goes anywhere. The system flags anomalies. Humans decide what to do with them.

Demo spikes always set `synthetic=true` with a distinct `source_type`, so anyone reading the data can see exactly which signals are real and which are controlled.

---

## Demo: Six Proof Artifacts

| # | Proof | What to show |
|---|---|---|
| 1 | **Nimble / open-web** | One real public page becomes a structured signal. Logs show `source_type=nimble_open_web`. |
| 2 | **Autonomy** | `GET /status` returns `run_id`, an advancing `stage`, and a proof checklist that updates on its own. |
| 3 | **Math** | ClickHouse returns `recent_count`, `baseline_avg`, `baseline_stddev`, `z_score` from the anomaly query. |
| 4 | **Safety** | Clinical verifier calls FHIR `_summary=count`. Aggregate integer only, no PHI. |
| 5 | **Action** | Slack message and Datadog log appear automatically on a confirmed alert. Senso URL or local cited.md file is written. |
| 6 | **Commerce** | `GET /alerts/confirmed/{id}` gives you 402. Add `x-payment: demo-paid` and you get 200 with `payment_status: paid`. |

---

## Quick Start

### 1. Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your keys:

| Variable | Required | Description |
|---|---|---|
| `CH_HOST` | Yes | ClickHouse host (strip `https://`) |
| `CH_PASSWORD` | Yes | ClickHouse password |
| `NIMBLE_MODE` | Yes | `mock` (offline) or `http` (real API) |
| `NIMBLE_API_KEY` | http mode | Nimble Bearer token |
| `SLACK_BOT_TOKEN` | Optional | Slack bot token |
| `SLACK_CHANNEL_ID` | Optional | Target Slack channel |
| `DD_API_KEY` | Optional | Datadog API key |
| `SENSO_API_KEY` | Optional | Senso key; falls back to local file |
| `X402_ENABLED` | Optional | `true` by default |
| `FHIR_BASE_URL` | Optional | FHIR base URL; falls back to demo lookup |

### 3. Initialize the database

```powershell
$env:PYTHONPATH="."
.venv\Scripts\python -m storage.init_schema
.venv\Scripts\python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2
```

### 4. Run the demo (4 terminals)

```powershell
# Terminal 1: API server
$env:PYTHONPATH="."
.venv\Scripts\python -m uvicorn app:app --reload --port 8000

# Terminal 2: Ingestion (Nimble + 311 + Reddit)
$env:PYTHONPATH="."
.venv\Scripts\python -m ingestion.orchestrator

# Terminal 3: Controlled spike (synthetic=true)
$env:PYTHONPATH="."
.venv\Scripts\python demo/inject_spike.py --zip 10014 --symptom gi --count 15

# Terminal 4: Anomaly engine
$env:PYTHONPATH="."
.venv\Scripts\python -m anomaly.engine --demo
```

Open these six browser tabs at the same time:

1. `http://localhost:8000/status`
2. ClickHouse console running `storage/anomaly.sql`
3. Datadog filtered to `run_id:run_demo`
4. Slack channel
5. `public/alerts/` folder or Senso URL
6. `http://localhost:8000/alerts/confirmed/{alert_id}`

Payment demo:

```bash
# Without header: 402
curl -i http://localhost:8000/alerts/confirmed/<alert_id>

# With header: 200
curl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/<alert_id>
```

---

## Incident Simulator

Want a more realistic demo? `test_recent_outbreaks.py` models four real NYC outbreaks. It seeds a 90-day baseline, injects incident signals, runs the anomaly engine, and prints the alert ID ready for the payment demo.

```powershell
$env:PYTHONPATH="."
.venv\Scripts\python demo/test_recent_outbreaks.py --outbreak legionella
```

Available scenarios: `legionella` (ZIP 10031), `measles` (10036), `hantavirus` (10036), `influenza` (10036).

---

## Demo Hygiene

If you run the spike injector more than once, signals pile up in the 6-hour window and your Z-score gets unrealistically large. Before the final demo, use a fresh run ID:

```powershell
$env:DEMO_RUN_ID="run_final"
.venv\Scripts\python demo/inject_spike.py --zip 10013 --symptom gi --count 15
```

Or clean up only the recent synthetic rows:

```sql
ALTER TABLE outbreak.outbreak_signals
DELETE
WHERE synthetic = true
  AND timestamp > now() - INTERVAL 6 HOUR
  AND source_type IN ('nimble_demo', 'reddit_demo', 'nyc_311_demo');
```

Don't delete `synthetic=false` rows. Judges need to see at least one real signal.

---

## Codebase Map

| File | Role |
|---|---|
| [app.py](app.py) | FastAPI server: `/status` checklist and `/alerts/confirmed/{id}` payment gate |
| [ingestion/orchestrator.py](ingestion/orchestrator.py) | Runs all four ingestion lanes: Nimble, NYC 311, Reddit, Yelp |
| [ingestion/extractor.py](ingestion/extractor.py) | Regex ZIP and symptom parser |
| [ingestion/nimble_client.py](ingestion/nimble_client.py) | Nimble adapter (mock / http / SDK-ready) |
| [ingestion/public_data.py](ingestion/public_data.py) | NYC 311 Socrata API client |
| [storage/clickhouse.py](storage/clickhouse.py) | ClickHouse client and CRUD helpers |
| [storage/schema.sql](storage/schema.sql) | `outbreak_signals` and `alerts` table definitions |
| [storage/anomaly.sql](storage/anomaly.sql) | Z-score query (90-day baseline, 6-hour window) |
| [anomaly/engine.py](anomaly/engine.py) | Runs the anomaly query and switches between demo and prod thresholds |
| [verification/clinical_aggregate.py](verification/clinical_aggregate.py) | FHIR `_summary=count` verifier, aggregate only, no PHI |
| [actions/orchestrator.py](actions/orchestrator.py) | Alert lifecycle: verify, publish, notify, store |
| [actions/slack_alerts.py](actions/slack_alerts.py) | Slack alert sender |
| [actions/senso_publish.py](actions/senso_publish.py) | Senso publisher with local cited.md fallback |
| [observability/datadog.py](observability/datadog.py) | Structured JSON logs and metrics |
| [demo/inject_spike.py](demo/inject_spike.py) | Controlled spike injector (`synthetic=true`) |
| [demo/seed_baseline.py](demo/seed_baseline.py) | Fills in 90 days of baseline signals |
| [demo/test_recent_outbreaks.py](demo/test_recent_outbreaks.py) | End-to-end outbreak simulator |

---

## Tests

```powershell
$env:PYTHONPATH="."
.venv\Scripts\python -m pytest tests/ -v
```

---

## References

- [CDC NSSP/BioSense Platform](https://www.cdc.gov/nssp/php/about/about-nssp-and-the-biosense-platform.html)
- [NYC Open Data 311 API](https://data.cityofnewyork.us/resource/erm2-nwe9.json)
- [ClickHouse Docs](https://clickhouse.com/docs)
- [Datadog Docs](https://docs.datadoghq.com/)
- [Nimble Docs](https://docs.nimbleway.com/)
- [Senso Docs](https://docs.senso.ai/)
- [x402 Protocol](https://www.x402.org/)
