# zipsick

An autonomous public health signal agent that spots early community illness outbreaks before they hit official databases. 

## What is zipsick?

zipsick is a tool that monitors public web pages, search results, and civic datasets to detect local symptom spikes. When the agent detects an unusual symptom cluster in a specific ZIP code, it runs a privacy-safe check against aggregate clinical counts. If both signals match, the agent alerts health teams, publishes a cited advisory page, and protects detailed outbreak packages behind a payment gate.

It doesn't give medical advice or track individuals. It simply flags early signs of community illness.

## Why is it here?

Official health surveillance is excellent. But it takes time. Systems like the CDC NSSP and BioSense platform track emergency department visits. That only helps after patients show up at the hospital. 

zipsick complements these systems by watching the open web first. When people feel sick, they often talk about it online. Or they file civic complaints before they go to a doctor. By capturing these open-web signals early, we give public health teams crucial extra lead time to react. 

We built this to prove that autonomous web collection, real-time math, and privacy-preserving clinical checks can work together. It works.

## How it works

The agent runs a complete signal pipeline without requiring manual decisions:

1. **Ingest**: The agent checks open web pages using browser extraction. It also queries public civic complaint data (like NYC 311).
2. **Extract**: It parses incoming text to extract specific symptoms (like stomach issues or fever) and ZIP codes.
3. **Score**: It compares current symptom counts against a 90-day historical baseline in ClickHouse. If the counts exceed the standard deviation threshold, it triggers an anomaly.
4. **Verify**: To prevent false alarms, it queries an aggregate clinical database. It requires at least two matching clinical cases in the same ZIP code to proceed.
5. **Act**: The agent sends structured metrics, logs a trace, and posts an alert to the team's Slack channel.
6. **Publish**: It publishes a citeable markdown summary (a cited.md page) with references linking back to the web sources.
7. **Monetize**: It packages the full, verified outbreak alert and gates it behind a standard HTTP 402 payment protocol.

## Safety and Boundaries

We designed zipsick with strict public safety and privacy constraints:
- **No PHI**: The agent never tracks individuals or collects patient-level medical records.
- **Aggregate Verification**: Clinical checks only return total counts (like "2 presentations"). This keeps all individual data private.
- **No Medical Advice**: It doesn't diagnose users or recommend treatments.
- **Review Loop**: Public advisory text is drafted as a proposal for human health officials to review before release.

## Sponsor Integrations

We use five sponsor technologies to power the pipeline:
- **Nimble**: Fetches public web content and search results dynamically.
- **ClickHouse**: Stores signals, calculates standard deviations, and manages z-scores.
- **Datadog**: Tracks health metrics and pipeline events.
- **Senso**: Generates cited advisory pages with source links.
- **x402 / CDP**: Gates completed alerts behind developer payment rails.

## Quick Start

### 1. Set up your environment
Create a virtual environment and install the dependencies:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```
*(Make sure to update the `.env` file with your credentials.)*

### 2. Prepare the database
Initialize the schema and seed 90 days of low-count historical baseline data:
```bash
python -m storage.init_schema
python -m demo.seed_baseline --zip 10014 --symptom gi --days 90 --avg-per-day 2
```

### 3. Run the live demo
Open four terminal windows to run the agent pipeline:

- **Terminal 1 (Web Server)**: Start the status dashboard and payment gate.
  ```bash
  uvicorn app:app --reload --port 8000
  ```
- **Terminal 2 (Ingest)**: Run a poll of public web data.
  ```bash
  python -m ingestion.orchestrator
  ```
- **Terminal 3 (Spike)**: Inject a demo symptom spike to trigger the threshold.
  ```bash
  python -m demo.inject_spike --zip 10014 --symptom gi --count 15
  ```
- **Terminal 4 (Score)**: Run the anomaly detector to analyze and process the alert.
  ```bash
  python -m anomaly.engine --demo
  ```

### 4. Verify the payment gate
You can check the gated endpoint with these commands:

```bash
# Returns 402 Payment Required
curl -i http://localhost:8000/alerts/confirmed/<YOUR_ALERT_ID>

# Returns 200 OK after mock payment proof
curl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/<YOUR_ALERT_ID>
```
