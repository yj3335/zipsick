# zipsick — Autonomous Public-Health Signal Agent

Early ZIP-level outbreak detection that complements official surveillance by watching public open-web signals before patients reach the hospital.

---

## The Problem

Official systems like the CDC NSSP/BioSense platform track Emergency Department visits — reliable, but downstream of when people actually get sick. **zipsick** captures the upstream signal: community posts, civic complaints, and public health pages — structured, anomaly-scored, and clinically verified — giving public-health teams earlier lead time to prepare.

> **Language note**: This project complements official systems. It does not claim to replace CDC NSSP or BioSense, and does not say "CDC takes 2–6 weeks." We say: CDC surveillance is reliable; zipsick adds earlier open-web signal.

---

## Autonomous Pipeline

The agent runs the full `observe → extract → store → score → verify → act → publish → monetize` loop without manual decisions. A single `run_id` traces every step in Datadog.

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

| Tool | Role in Pipeline |
|---|---|
| **Nimble** | Open-web collection layer. Fetches public health pages and community sources with IP rotation. Supports Bearer auth, Basic auth, and `NIMBLE_MODE=mock` for offline demo. |
| **ClickHouse** | Signal store and anomaly engine. Holds 90-day baseline; runs the Z-score SQL (`recent_count`, `baseline_avg`, `baseline_stddev`, `z_score`) in real time. |
| **Datadog** | Structured logs and metrics across every stage. All events carry `run_id` and `alert_id` for full distributed trace. Events: `ingestion_complete`, `anomaly_detected`, `alert_confirmed`, `alert_suppressed`. Metrics: `outbreak.events_ingested`, `outbreak.alert.confirmed`, `outbreak.payment.completed`. |
| **Senso / cited.md** | Publishes confirmed alerts as citable markdown documents with source links. Falls back to a local `public/alerts/{alert_id}.md` file when API credentials are absent; clearly labelled in logs either way. |
| **x402 / Coinbase Developer Platform** | HTTP 402 payment gate on the confirmed-alert endpoint. Returns structured payment instructions without a header; unlocks full alert package with `x-payment` proof. |

---

## Safety Guardrails

- **No diagnosis.** No patient-level data is accessed, stored, or returned at any point.
- **Aggregate-only clinical verification.** The FHIR adapter queries `Condition?_summary=count` — it receives an integer count, nothing else. No patient IDs, no names, no clinical notes.
- **Public-good framing.** All public-facing health language is drafted for authorized review before distribution. The system flags anomalies; humans decide action.
- **Synthetic signals are always labelled.** Demo spikes set `synthetic=true` and a distinct `source_type`. The evidence-ledger query lets judges see exactly which signals are real vs. controlled.
- **CDC language.** The CDC NSSP/BioSense platform supports near-real-time ED surveillance for participating facilities. zipsick **complements** that system with earlier public/open-web signals.

---

## Demo: Six Judge Proof Artifacts

| # | Proof | What to Show |
|---|---|---|
| 1 | **Nimble / open-web** | One real public page becomes a structured signal. Logs show `source_type=nimble_open_web`. |
| 2 | **Autonomy** | `GET /status` returns `run_id`, advancing `stage`, and a proof checklist that updates automatically. |
| 3 | **Math** | ClickHouse returns `recent_count`, `baseline_avg`, `baseline_stddev`, `z_score` from the anomaly query. |
| 4 | **Safety** | Clinical verifier calls FHIR `_summary=count` — aggregate integer only, no PHI. |
| 5 | **Action** | Slack message and Datadog log appear automatically on confirmed alert. Senso URL or local cited.md file written. |
| 6 | **Commerce** | `GET /alerts/confirmed/{id}` → `402 Payment Required` → add `x-payment: demo-paid` → `200 OK`, `payment_status: paid`. |

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
| `SLACK_BOT_TOKEN` | Optional | Slack bot token for alert posts |
| `SLACK_CHANNEL_ID` | Optional | Target Slack channel |
| `DD_API_KEY` | Optional | Datadog API key |
| `SENSO_API_KEY` | Optional | Senso publisher key; falls back to local file |
| `X402_ENABLED` | Optional | `true` (default) to enforce payment gate |
| `FHIR_BASE_URL` | Optional | FHIR base URL; falls back to demo lookup |

### 3. Initialize the database

```powershell
$env:PYTHONPATH="."
.venv\Scripts\python -m storage.init_schema
.venv\Scripts\python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2
```

### 4. Live demo (4 terminals)

```powershell
# Terminal 1 — API server
$env:PYTHONPATH="."
.venv\Scripts\python -m uvicorn app:app --reload --port 8000

# Terminal 2 — Ingestion (Nimble + 311 + Reddit)
$env:PYTHONPATH="."
.venv\Scripts\python -m ingestion.orchestrator

# Terminal 3 — Controlled spike (marks synthetic=true)
$env:PYTHONPATH="."
.venv\Scripts\python demo/inject_spike.py --zip 10014 --symptom gi --count 15

# Terminal 4 — Anomaly engine
$env:PYTHONPATH="."
.venv\Scripts\python -m anomaly.engine --demo
```

**Browser tabs to have open:**

1. `http://localhost:8000/status` — proof checklist
2. ClickHouse console → run `storage/anomaly.sql`
3. Datadog → filter logs to `run_id:run_demo`
4. Slack channel
5. `public/alerts/` folder or Senso URL
6. `http://localhost:8000/alerts/confirmed/{alert_id}` — 402 → pay → 200

**Payment demo (curl):**

```bash
# Step 1 — shows 402
curl -i http://localhost:8000/alerts/confirmed/<alert_id>

# Step 2 — shows 200
curl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/<alert_id>
```

---

## Incident Simulator

Simulate real NYC outbreaks (Legionella, Measles, Hantavirus, H3N2) end-to-end through the full pipeline:

```powershell
$env:PYTHONPATH="."
.venv\Scripts\python demo/test_recent_outbreaks.py --outbreak legionella
```

Available scenarios: `legionella` (ZIP 10031), `measles` (10036), `hantavirus` (10036), `influenza` (10036).

The simulator seeds a 90-day baseline, injects incident signals with real evidence text, runs the anomaly engine, and prints the confirmed alert ID ready for the payment-gate demo.

---

## Demo Hygiene

Repeated spike injections accumulate in the 6-hour window and inflate Z-scores. Before the final presentation, use a fresh `DEMO_RUN_ID`:

```powershell
$env:DEMO_RUN_ID="run_final"
.venv\Scripts\python demo/inject_spike.py --zip 10013 --symptom gi --count 15
```

Or delete only recent synthetic rows:

```sql
ALTER TABLE outbreak.outbreak_signals
DELETE
WHERE synthetic = true
  AND timestamp > now() - INTERVAL 6 HOUR
  AND source_type IN ('nimble_demo', 'reddit_demo', 'nyc_311_demo');
```

---

## Codebase Map

| File | Role |
|---|---|
| [app.py](app.py) | FastAPI server — `/status` proof checklist, `/alerts/confirmed/{id}` x402 gate |
| [ingestion/orchestrator.py](ingestion/orchestrator.py) | Ingestion coordinator: Nimble, NYC 311, Reddit, Yelp |
| [ingestion/extractor.py](ingestion/extractor.py) | Regex-based ZIP + symptom parser |
| [ingestion/nimble_client.py](ingestion/nimble_client.py) | Nimble open-web adapter (mock / http / SDK-ready) |
| [ingestion/public_data.py](ingestion/public_data.py) | NYC 311 Socrata API client |
| [storage/clickhouse.py](storage/clickhouse.py) | ClickHouse client and CRUD helpers |
| [storage/schema.sql](storage/schema.sql) | DDL: `outbreak_signals` and `alerts` tables |
| [storage/anomaly.sql](storage/anomaly.sql) | Z-score anomaly query (90-day baseline, 6-hour window) |
| [anomaly/engine.py](anomaly/engine.py) | Anomaly runner with demo/prod threshold switching |
| [verification/clinical_aggregate.py](verification/clinical_aggregate.py) | FHIR `_summary=count` verifier — aggregate only, no PHI |
| [actions/orchestrator.py](actions/orchestrator.py) | Alert lifecycle: verify → publish → notify → store |
| [actions/slack_alerts.py](actions/slack_alerts.py) | Slack confirmed-alert message sender |
| [actions/senso_publish.py](actions/senso_publish.py) | Senso / cited.md publisher with local fallback |
| [observability/datadog.py](observability/datadog.py) | Structured JSON logs and metrics |
| [demo/inject_spike.py](demo/inject_spike.py) | Controlled demo spike (`synthetic=true`) |
| [demo/seed_baseline.py](demo/seed_baseline.py) | 90-day historical baseline seeder |
| [demo/test_recent_outbreaks.py](demo/test_recent_outbreaks.py) | Real-incident outbreak end-to-end simulator |

---

## Running Tests

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
