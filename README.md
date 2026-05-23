# zipsick: Autonomous Public-Health Signal Agent

An autonomous early-warning agent that spots community illness outbreaks by watching the open web, verifying spikes via aggregate clinical data, and exposing confirmed alert packages behind developer payment rails.

---

## 💡 The Value Proposition: Complementing Official Surveillance

Official public-health surveillance is highly reliable but has built-in delays. Systems like the CDC National Syndromic Surveillance Program (NSSP) and BioSense platform track Emergency Department (ED) visits. This only logs an event after a patient decides to go to the hospital.

**zipsick** complements official systems by monitoring public open-web signals first. When people start getting sick:
1. They search for symptoms or post on local community forums (Reddit, Yelp).
2. They file civic complaints (like NYC 311 rodent or unsanitary condition reports).
3. They check health advisory pages.

By capturing and structuring these pre-hospital signals, zipsick gives public health teams early lead time to prepare.

---

## 🛠️ E2E Autonomous Pipeline Flow

The agent runs a complete, closed-loop pipeline without requiring human intervention:

```
[Ingest: Nimble & Socrata] 
  ➜ [Extract: LLM Symptom/ZIP Parsing] 
  ➜ [Store: ClickHouse DB] 
  ➜ [Score: Historical Z-Score Math] 
  ➜ [Verify: Live FHIR Aggregate Check] 
  ➜ [Act: Slack Alerts & Datadog Metrics] 
  ➜ [Publish: Senso/Cited.md Advisories] 
  ➜ [Monetize: x402 Paid Alert Gate]
```

1. **Ingest**: Queries Socrata for live Manhattan 311 complaints, polls local subreddits (Reddit API via Nimble), scrapes local Yelp reviews, and checks official health topic pages.
2. **Extract**: Standardizes unstructured texts into structured records with location (ZIP code), symptom class, confidence, and timestamp.
3. **Score**: Runs standard deviation calculations against a 90-day historical baseline in ClickHouse. If a ZIP/symptom count exceeds the threshold, it triggers an anomaly.
4. **Verify**: Prevents false alarms by checking aggregate clinical counts (using SNOMED codes) via a live FHIR server (`hapi.fhir.org/baseR4`).
5. **Act**: Logs pipeline metrics in Datadog and posts alert summaries to the team's Slack channel.
6. **Publish**: Writes a cited advisory package containing original web references, publishing it to a local cited.md-compatible server.
7. **Monetize**: Restricts access to the complete confirmed alert payload behind an HTTP 402 payment gate (x402 protocol).

---

## 🔌 Sponsor Tech Integrations

We integrated five sponsor tools to power the pipeline:
* **Nimble**: Serves as our web scraping infrastructure. It manages IP rotation and captures public health pages, Reddit posts, and Yelp reviews.
* **ClickHouse**: Serves as our analytical storage. It stores over 1,000 baseline signals and executes the Z-score anomaly query.
* **Datadog**: Tracks operational health, logs ingestion metrics, and monitors pipeline events.
* **Senso**: Publishes cited outbreak advisories (cited.md format), automatically linking back to original web sources.
* **x402 / Coinbase Developer Platform (CDP)**: Secures raw outbreak data behind developer payment rails, verifying transaction proofs via Base.

---

## 🏆 Judge's Verification Guide (The 6 Proof Artifacts)

When grading the build, verify these active pipeline proofs:

### 1. Nimble/Open-Web Ingest Proof
Run the ingestion orchestrator. It retrieves live web data and inserts structured signals:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\python -m ingestion.orchestrator
```
Check the logs to verify that Nimble extracted real web content.

### 2. Autonomy & Status Proof
Visit the status page in your browser at `http://localhost:8000/status` or query it:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/status
```
It returns the agent's active run ID and a verified checklist proving ClickHouse connection, Nimble signals, clinical status, Datadog configuration, Senso publishing, and x402 payment tracking.

### 3. ClickHouse Math Proof
Query the database to inspect baseline signals and active alert entries:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\python demo/query_db.py
```
This shows the Z-score calculation (`(recent_count - baseline_avg) / baseline_stddev`) working across the database tables.

### 4. Safety & Clinical Verification Proof
Review the clinical adapter in [clinical_aggregate.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/verification/clinical_aggregate.py). It queries the live FHIR server using aggregate-only parameters (`_summary=count`), ensuring zero Patient Health Information (PHI) is retrieved or stored.

### 5. Action & Publication Proof
Verify that:
* The local Senso publisher has created cited advisories.
* Alerts have been pushed to the Slack workspace channel.
* Datadog is logging execution metrics.

### 6. Commerce/Payment Gate Proof
Query a confirmed alert endpoint. Without a payment header, it returns `402 Payment Required`:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/alerts/confirmed/<alert_id>
```
Supply the mock payment header to unlock the data:
```powershell
Invoke-RestMethod -Headers @{"x-payment"="demo-paid"} -Uri http://localhost:8000/alerts/confirmed/<alert_id>
```
The response returns `200 OK` and marks the status as `paid` in ClickHouse.

---

## 🚀 Live Outbreak & Incident Simulator

You can test how the pipeline handles real-world outbreaks using our simulation script, [test_recent_outbreaks.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/demo/test_recent_outbreaks.py). It models historical incidents like the **Harlem Legionnaires' outbreak** (ZIP `10031` at 3333 Broadway):

1. **Initialize the database schema**:
   ```powershell
   .venv\Scripts\python -m storage.init_schema
   ```

2. **Run the outbreak test**:
   ```powershell
   $env:PYTHONPATH="."
   .venv\Scripts\python demo/test_recent_outbreaks.py --outbreak legionella
   ```
   This seeds the historical baseline, injects realistic incident signals, triggers the Z-score threshold, verifies conditions on the live FHIR server, and publishes the confirmed alert.

3. **Query the resulting alert package**:
   Check the output of the simulation for the generated `<alert_id>` and fetch it:
   ```powershell
   # Unlocks the alert package
   Invoke-RestMethod -Headers @{"x-payment"="demo-paid"} -Uri http://localhost:8000/alerts/confirmed/<alert_id>
   ```

---

## ⚡ Quick Start (Local Setup)

1. **Install dependencies**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Configure environment**:
   Copy `.env.example` to `.env` and fill in your keys for ClickHouse, Nimble, Datadog, Slack, and Senso.
3. **Start the API Server**:
   ```powershell
   .venv\Scripts\python -m uvicorn app:app --port 8000
   ```

---

## 📂 Core Code Symbols

* **API & Gating**: [app.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/app.py) handles the status control panel and x402 payment gate.
* **Orchestration**: [orchestrator.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/ingestion/orchestrator.py) coordinates the ingestion lanes.
* **Clinical Verification**: [clinical_aggregate.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/verification/clinical_aggregate.py) handles FHIR condition queries.
* **Anomaly Detection**: [engine.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/anomaly/engine.py) reads the [anomaly.sql](file:///c:/Users/yesjan/Documents/New%20project/zipsick/storage/anomaly.sql) query to flag outbreaks.
* **Simulation tool**: [test_recent_outbreaks.py](file:///c:/Users/yesjan/Documents/New%20project/zipsick/demo/test_recent_outbreaks.py) runs the incident simulator.
