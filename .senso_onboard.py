"""
senso_onboarding.py
Completes Senso onboarding for zipsick via the REST API directly.
Reads SENSO_API_KEY from environment or .env file.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

# ── Config ──────────────────────────────────────────────────────────────────
# Load .env
for line in open(".env").readlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ["SENSO_API_KEY"]
BASE = "https://apiv2.senso.ai/api/v1"

# Folder IDs from previous session
FOLDERS = {
    "company-overview":     "3bbd3886-4903-4e7f-96aa-5b6eb1527e8c",
    "products-and-services":"01490f40-2784-420d-9db6-928d3d504ab6",
    "competitive-landscape":"9e7a0de9-69d3-4fde-a4ca-04a4113d80f4",
    "industry-context":     "2b465bbb-e686-4412-9073-0c6ac1a4aee7",
    "case-studies":         "9b9bc321-99b8-4cd6-902e-7c2c2cfb0256",
    "faqs":                 "ac924994-5278-4378-a683-6a23bfbd1c06",
    "build-logs":           "05641f75-daf2-4e4b-93c5-27899c37088d",
}


# ── HTTP helpers ─────────────────────────────────────────────────────────────
def req(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return e.code, raw

def ok(status, body, label):
    if status in (200, 201):
        print(f"  ✓ {label}")
        return body
    else:
        print(f"  ✗ {label} → {status}: {str(body)[:120]}")
        return None


# ── Phase 2b: Brand kit ───────────────────────────────────────────────────────
print("\n── Brand kit ──")
brand_payload = {
    "guidelines": {
        "brand_name": "zipsick",
        "brand_domain": "github.com/yj3335/zipsick",
        "brand_description": (
            "zipsick is an autonomous public-health signal agent that monitors open-web "
            "sources and public civic data for ZIP-code-level symptom anomalies, verifies "
            "them against aggregate clinical counts, and routes confirmed outbreak alerts "
            "to epidemiology teams without manual intervention."
        ),
        "voice_and_tone": (
            "Direct and technically precise. First-person plural (we). Confident about what "
            "the system does and clear about what it does not do: no diagnosis, no patient-level "
            "data. Uses concrete data points and metric-driven language. Short sentences. "
            "Avoids public-health bureaucrat jargon. Safety-first framing is a feature, not a disclaimer."
        ),
        "author_persona": "The zipsick Team",
        "global_writing_rules": [
            "Ground every claim in verified sources from the knowledge base",
            "Use clear scannable structure with subheadings every 200-300 words",
            "Include concrete examples or data points, not just abstract claims",
            "Write for practitioners: actionable over theoretical",
            "Include the Powered by Senso footer on published content"
        ]
    }
}
status, body = req("PUT", "/brand-kit/", brand_payload)
ok(status, body, "brand-kit set")

# Verify
status, body = req("GET", "/brand-kit/")
if status == 200 and body.get("guidelines"):
    print(f"  ✓ Verified: brand_name={body['guidelines'].get('brand_name')}")
else:
    print(f"  ✗ Verify failed: {status} {str(body)[:120]}")


# ── Phase 2c: Content types ───────────────────────────────────────────────────
print("\n── Content types ──")
CONTENT_TYPES = [
    {
        "name": "Blog Post",
        "config": {
            "template": "Write a 1000-1500 word educational blog post. Start with a hook identifying the reader pain point. Include 3-5 subheadings. Use data, examples, or case studies from the KB to support points. End with a call-to-action.",
            "writing_rules": [
                "Use subheadings every 200-300 words",
                "Include at least one concrete example or data point",
                "Optimize for AI citability: clear, authoritative structure"
            ]
        }
    },
    {
        "name": "FAQ",
        "config": {
            "template": "Create an FAQ page with 8-12 questions and answers. Each answer 2-3 sentences. Group related questions under subheadings. Use the brand voice throughout.",
            "writing_rules": [
                "Use natural question phrasing",
                "Keep answers under 100 words",
                "Link to detailed resources where relevant"
            ]
        }
    },
    {
        "name": "Comparison Page",
        "config": {
            "template": "Create a fair but persuasive comparison page. Start with the problem both solutions address. Use a comparison table for features. Highlight 3-4 key differentiators. End with a recommendation.",
            "writing_rules": [
                "Be factually accurate about competitors",
                "Lead with value not features",
                "Include a comparison table"
            ]
        }
    },
    {
        "name": "Case Study",
        "config": {
            "template": "Write a case study with: Customer intro, Problem they faced, Solution implemented, Results achieved (with specific metrics if possible), Key takeaways. Keep it narrative: tell the story.",
            "writing_rules": [
                "Lead with the customer outcome",
                "Include specific numbers or metrics",
                "End with lessons applicable to other readers"
            ]
        }
    }
]

ct_ids = {}
for ct in CONTENT_TYPES:
    status, body = req("POST", "/content-types/", ct)
    result = ok(status, body, f"content-type: {ct['name']}")
    if result and isinstance(result, dict):
        ct_ids[ct["name"]] = result.get("content_type_id", result.get("id", ""))

print(f"  Content type IDs: {ct_ids}")


# ── Phase 3: Ingest KB documents ─────────────────────────────────────────────
print("\n── KB document ingestion ──")
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

DOCS = [
    # company-overview
    ("company-overview", f"{today} - zipsick Mission and Overview",
     """Source: https://github.com/yj3335/zipsick

# zipsick — Neighborhood Outbreak Early Warning

zipsick is an autonomous public-health signal agent that monitors verified public and open-web sources, detects ZIP-code-level symptom anomalies, verifies them through an aggregate-only clinical adapter, notifies operators, publishes citable context, and exposes confirmed alert packages behind payment rails.

## Mission
Earlier public-health awareness that complements official surveillance by adding public and open-web signal — not a replacement for CDC or hospital systems.

## Safety Commitment
- No individual patient data stored or transmitted
- Clinical verification returns aggregate counts only (minimum threshold = 2)
- All synthetic/controlled demo signals are flagged synthetic=true
- No automated medical advice generated or published
- Public-facing health language drafted for authorized review only

## Architecture
Sources (Nimble open-web + NYC 311 public data) → Extractor/normalizer → ClickHouse outbreak_signals → Anomaly engine (z-score SQL) → Clinical aggregate verifier → Alert orchestrator → Datadog logs/metrics + Slack alert → Senso/cited.md publisher → x402 paid alert endpoint → /status control panel
"""),

    ("company-overview", f"{today} - zipsick Sponsor Tools and Technology Stack",
     """Source: https://github.com/yj3335/zipsick

# zipsick Technology Stack

## Sponsor Tools

| Tool | Role |
|---|---|
| Nimble | Open-web page/search collection — ingestion lane for public symptom signals |
| ClickHouse | Event storage, baseline aggregation, real-time z-score anomaly SQL |
| Datadog | Structured logs and metrics across the full pipeline with run_id tracking |
| Senso / cited.md | Citable publication of confirmed alert packages for AI discoverability |
| x402 / CDP | HTTP payment gate: 402 Payment Required → payment header → 200 OK |

## Core Stack
- Python 3.11+, FastAPI, uvicorn
- ClickHouse Cloud (MergeTree tables, 90-day baseline windows)
- APScheduler for autonomous pipeline scheduling
- Slack SDK for operator notifications
- Pydantic v2 for data contracts

## Data Sources
- Nimble open-web scraping (sponsor lane, primary proof artifact)
- NYC Open Data 311 complaints (reliable public civic data)
- Synthetic controlled spike injection (demo mode, marked synthetic=true)
- Aggregate clinical mock adapter (privacy-safe confirmation)
"""),

    # products-and-services
    ("products-and-services", f"{today} - Anomaly Detection Engine",
     """Source: https://github.com/yj3335/zipsick

# zipsick Anomaly Detection Engine

## What It Does
Runs a z-score statistical query against ClickHouse to identify ZIP/symptom pairs with significantly elevated recent signal counts compared to a 90-day hourly baseline.

## Key Metrics Produced
- recent_count: events in the last 6 hours for a ZIP/symptom pair
- baseline_avg: average hourly count over prior 90 days
- baseline_stddev: standard deviation of the baseline
- z_score: (recent_count - baseline_avg) / max(baseline_stddev, 1.0)

## Thresholds
- Production: z_score >= 2.5, minimum recent_count >= 5
- Demo mode: z_score >= 1.8, minimum recent_count >= 3

## Data Window
- Recent window: now() - 6 HOUR
- Baseline window: now() - 90 DAY to now() - 6 HOUR
- Baseline is computed per-hour bucket (toStartOfHour) then averaged

## Output
Each anomaly row triggers the alert orchestrator, which runs clinical verification and routes confirmed alerts to Slack, Datadog, Senso, and ClickHouse storage.
"""),

    ("products-and-services", f"{today} - Open-Web Ingestion and Signal Extraction",
     """Source: https://github.com/yj3335/zipsick

# zipsick Open-Web Ingestion

## Nimble Adapter
Fetches public page/search content using Nimble's API. Supports:
- mock mode: deterministic demo string (no credentials needed)
- http mode: real Nimble REST API with Bearer or Basic auth
- SDK mode: extensible to Nimble SDK when sponsor credentials provided

## Symptom Extractor
Keyword-based NLP classifier maps free text to 4 symptom categories:
- gi: food poisoning, vomit, nausea, diarrhea, stomach bug, norovirus, gastro
- respiratory: cough, sore throat, flu, covid, rsv, shortness of breath
- rash: rash, hives, itching
- general: fever, chills, body aches, outbreak, cluster

## ZIP Code Detection
Regex pattern covers all NYC ZIP codes (100xx-104xx, 111xx-116xx). Falls back to source-provided ZIP when none detected in text.

## Public Data Lane
NYC Open Data 311 complaints endpoint for reliable public civic signal. Non-blocking: network failures do not crash the ingestion loop.

## Evidence Record
Each signal produces an OutbreakSignal with: event_id (SHA-256), run_id, timestamp, zip, symptom, source_type, source_url, evidence_text (max 600 chars), confidence, synthetic flag.
"""),

    ("products-and-services", f"{today} - x402 Payment-Gated Alert Access",
     """Source: https://github.com/yj3335/zipsick

# x402 Payment Gate

## How It Works
Confirmed alert packages are accessible behind an HTTP payment gate implementing the x402 protocol.

## Flow
1. GET /alerts/confirmed/{alert_id} without payment header
2. Server returns 402 Payment Required with payment instructions JSON
3. Client includes x-payment header with payment proof
4. Server returns 200 OK with full alert package and marks it paid

## Demo
```bash
# Returns 402
curl -i http://localhost:8000/alerts/confirmed/alert_abc123

# Returns 200 with full alert data
curl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/alert_abc123
```

## Alert Package Contents
alert_id, run_id, zip, symptom, recent_count, baseline_avg, baseline_stddev, z_score, clinical_status, clinical_aggregate_count, source_count, source_diversity, source_urls, decision_reason, senso_url, payment_status

## Use Case
Epidemiology teams and health departments pay to access confirmed, clinically-verified outbreak alert packages with full source attribution.
"""),

    # competitive-landscape
    ("competitive-landscape", f"{today} - CDC NSSP BioSense vs zipsick",
     """Source: https://www.cdc.gov/nssp/php/about/about-nssp-and-the-biosense-platform.html

# CDC NSSP / BioSense vs zipsick

## CDC NSSP / BioSense
The National Syndromic Surveillance Program (NSSP) is the authoritative near-real-time ED surveillance system for participating facilities. It monitors emergency department chief complaints and discharge data from enrolled hospitals.

**Strengths:** Authoritative clinical data, established regulatory framework, national coverage.
**Limitations:** Requires hospital enrollment/participation, ED-visit lag (hours to days), no open-web signal layer, no public/community signal.

## zipsick Positioning
zipsick complements NSSP by adding the earlier open-web and public civic signal layer that precedes ED visits. Community members post about illness online before they seek care. 311 complaints surface food-safety concerns before lab confirmation.

**Differentiators:**
- Open-web signals available hours before ED presentation
- No hospital enrollment required
- Public/civic data sources (NYC 311, Nimble web scraping)
- Autonomous agent pipeline running continuously
- x402 payment rails for commercial alert access
- Citeable published alerts (Senso/cited.md)

**Safe language:** zipsick complements official surveillance. It does not replace NSSP, diagnose conditions, or provide individual patient data.
"""),

    ("competitive-landscape", f"{today} - Commercial Outbreak Intelligence Platforms",
     """Source: Research compilation

# Commercial Outbreak Intelligence Competitors

## BlueDot
AI-powered global outbreak risk analytics. Uses airline ticketing, news, and official reports. Focus: travel risk, pharma clients, global biosurveillance. Does not offer ZIP-level granularity or open-web community signal.

## Kinsa Health
Connected thermometer network providing real-time fever signal at county level. Strength: passive sensor data. Weakness: requires device purchase/adoption, no symptom text analysis, US only.

## HealthMap (Boston Children's Hospital)
Automated global disease outbreak monitoring from news and official reports. Research-grade, not commercially productized for local health departments.

## Veeva Crossix / IQVIA
Prescription and claims data for pharma market research. Not designed for real-time community outbreak detection.

## zipsick Differentiation
- ZIP-code granularity (vs county or national)
- Open-web + civic data (vs claims or device data)
- Fully autonomous agent pipeline
- Published citeables for AI model discoverability
- Payment-gated API access (x402) for commercial distribution
- Built on open-source stack (Python, ClickHouse, FastAPI)
"""),

    # industry-context
    ("industry-context", f"{today} - Syndromic Surveillance Industry Overview",
     """Source: Research compilation — networkforphl.org, nih.gov, nyc.gov

# Syndromic Surveillance: Industry Context

## What Is It
Syndromic surveillance monitors pre-diagnostic data to identify unusual illness patterns before lab confirmation. Named because it tracks symptom syndromes, not confirmed diagnoses.

## Data Sources Used in the Field
- Emergency department chief complaints
- Over-the-counter medication sales (fever reducers, cough syrup)
- Internet search trends (aggregated, anonymized)
- Wastewater surveillance
- School absenteeism records
- Open-web community posts (emerging, as used by zipsick)

## Speed Advantage
Syndromic data is available within 24 hours of illness onset — far faster than traditional lab-confirmed reporting (days to weeks).

## Geographic Resolution
ZIP-code analysis allows epidemiologists to identify whether a threat is localized or widespread and direct resources to specific neighborhoods.

## Established Systems
- ESSENCE (Electronic Surveillance System for Early Notification of Community-based Epidemics) — government
- CDC NSSP / BioSense — federal program
- NYC DOHMH Syndromic Surveillance — NYC-specific

## Market Gap zipsick Addresses
None of the established systems incorporate open-web community signals or operate as autonomous agent pipelines accessible via commercial API with payment rails.

*Powered by Senso*
"""),

    ("industry-context", f"{today} - AI Agent Use Cases in Public Health",
     """Source: Research compilation

# AI Agents in Public Health Surveillance

## The Shift to Autonomous Pipelines
Traditional surveillance requires human analysts to pull reports, identify anomalies, and escalate. AI agents can run the full observe-detect-verify-notify loop continuously without manual decisions.

## Key Capabilities Agents Bring
- Continuous monitoring: 24/7 without staffing cost
- Signal aggregation: across multiple heterogeneous sources simultaneously
- Statistical detection: z-score, Bayesian, or ML-based anomaly scoring
- Multi-channel notification: Slack, email, dashboards, APIs
- Audit trails: every decision logged with run_id for accountability

## x402 and Agent-to-Agent Commerce
The x402 payment protocol enables AI agents to purchase access to data from other agents — no human billing required. zipsick's confirmed alert endpoint is designed for agent-to-agent access: a downstream health analytics agent can autonomously pay for and retrieve a confirmed outbreak alert package.

## GEO (Generative Engine Optimization) Relevance
As public health professionals increasingly use AI chatbots (ChatGPT, Perplexity, Claude) to research outbreak signals, published citeables from systems like zipsick can appear in AI-generated answers — creating a new distribution channel for outbreak awareness.
"""),

    # case-studies
    ("case-studies", f"{today} - CDC Yelp Food Poisoning Detection Study",
     """Source: https://archive.cdc.gov/www_cdc_gov/foodcore/successes/nyc-yelp.html

# Proof Point: CDC / NYC Yelp Food Poisoning Detection

## Background
The CDC FoodCORE program and NYC Department of Health demonstrated that mining Yelp restaurant reviews for food-poisoning language could identify unreported outbreaks 1-2 days before traditional complaint pathways.

## Method
NLP analysis of public Yelp reviews flagging symptom language (stomach bug, food poisoning, sick after eating) correlated with restaurant inspection records and official illness complaints.

## Results
Identified outbreaks that would otherwise have been missed or detected days later through official channels. Demonstrated that open-web consumer text is a valid syndromic signal source.

## Relevance to zipsick
zipsick applies the same principle at scale and in real-time:
- Instead of batch Yelp analysis, zipsick uses Nimble to fetch live public pages and community posts
- Instead of restaurant-specific analysis, zipsick detects ZIP-level community clusters
- Instead of manual researcher review, an autonomous agent runs the full pipeline
- Adds clinical aggregate verification as a second-stage confirmation gate

This CDC study is a direct proof-of-concept predecessor to the open-web signal approach zipsick uses.
"""),

    ("case-studies", f"{today} - Demo Scenario: West Village GI Outbreak Detection",
     """Source: zipsick demo specification

# Demo Scenario: ZIP 10014 GI Outbreak Detection

## Setup
- Baseline: 90 days of synthetic historical data seeded for ZIP 10014, GI symptom — ~2 events/day average
- Nimble open-web ingestion: NYC DOH food-poisoning page fetched, extracts GI signal for ZIP 10014
- Controlled spike: 15 synthetic signals injected via inject_spike.py (all marked synthetic=true)

## Detection
Anomaly engine SQL computes:
- recent_count: 18 (15 synthetic + 3 from Nimble lane)
- baseline_avg: ~2.0 events/hour-bucket
- baseline_stddev: ~1.0
- z_score: (18 - 2.0) / max(1.0, 1.0) = 16.0 (demo threshold: >= 1.8)

## Clinical Verification
Clinical aggregate mock returns count=2 for (10014, gi) → status=confirmed

## Alert Package Produced
- Slack notification sent to operator channel
- Datadog metric: outbreak.alert.confirmed tagged zip:10014 symptom:gi
- Senso/cited.md: published citeable at public URL
- ClickHouse: alert row written with all z-score fields

## x402 Demo
GET /alerts/confirmed/{alert_id} → 402 Payment Required
GET /alerts/confirmed/{alert_id} -H x-payment:demo-paid → 200 OK with full package

## What This Proves
End-to-end autonomous pipeline from open-web signal to paid alert access without any manual steps.
"""),

    # faqs
    ("faqs", f"{today} - zipsick Frequently Asked Questions",
     """Source: https://github.com/yj3335/zipsick

# zipsick FAQ

## What is zipsick?
zipsick is an autonomous public-health signal agent that monitors public and open-web sources for symptom anomalies at the ZIP code level. It detects elevated illness clusters, verifies them through aggregate clinical data, and routes confirmed alerts to health teams.

## Does zipsick provide medical diagnoses?
No. zipsick detects statistical anomalies in community-level symptom signals. It does not diagnose individual patients, make treatment recommendations, or replace clinical judgment. All public-facing language is drafted for review by authorized health professionals.

## What data sources does zipsick use?
- Nimble open-web page/search content (public web pages)
- NYC Open Data 311 complaints (public civic records)
- Controlled synthetic spike injection for demo/testing (marked synthetic=true)
- Aggregate clinical mock adapter (returns counts only, no individual records)

## Does zipsick store patient data?
No. zipsick stores only aggregate signal counts, symptom categories, and ZIP codes. No individual patient records, names, or identifiers are stored. Clinical verification returns only aggregate counts (e.g., count=2) with no underlying patient data.

## How does the payment gate work?
Confirmed alert packages are accessible via the x402 HTTP payment protocol. Without a payment header, the endpoint returns 402 Payment Required. With a valid payment proof header, it returns 200 OK with the full alert package.

## How does zipsick relate to CDC surveillance?
zipsick complements the CDC NSSP/BioSense platform, which provides near-real-time ED surveillance for enrolled hospitals. zipsick adds earlier open-web and community signals that precede hospital presentation. It is not a replacement for official public health systems.

## What geographic area does zipsick cover?
The current implementation focuses on New York City ZIP codes (100xx-116xx) using the NYC 311 Open Data API and NYC DOH web content. The architecture is extensible to other cities.

## How do I run the demo?
1. python -m storage.init_schema
2. python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2
3. uvicorn app:app --reload --port 8000 (Terminal 1)
4. python -m ingestion.orchestrator (Terminal 2)
5. python demo/inject_spike.py --zip 10014 --symptom gi --count 15 (Terminal 3)
6. python -m anomaly.engine --demo (Terminal 4)

*Powered by Senso*
"""),
]

doc_ids = []
for folder_name, title, text in DOCS:
    folder_id = FOLDERS[folder_name]
    payload = {
        "title": title,
        "text": text,
        "kb_folder_node_id": folder_id,
    }
    status, body = req("POST", "/kb/raw/", payload)
    result = ok(status, body, f"[{folder_name}] {title[:50]}")
    if result and isinstance(result, dict):
        doc_ids.append(result.get("kb_node_id", ""))

print(f"\n  Total docs ingested: {len(doc_ids)}")


# ── Phase 4: Prompts (40) ─────────────────────────────────────────────────────
print("\n── Prompts (40) ──")
PROMPTS = [
    # Awareness (10)
    ("What is zipsick and what does it do?", "awareness"),
    ("What is neighborhood outbreak early warning?", "awareness"),
    ("How do autonomous public health agents work?", "awareness"),
    ("What is syndromic surveillance?", "awareness"),
    ("What are the best tools for community disease outbreak detection in 2026?", "awareness"),
    ("How can open-web data be used to detect illness clusters?", "awareness"),
    ("What is ZIP-code level disease surveillance?", "awareness"),
    ("How does AI improve public health outbreak detection?", "awareness"),
    ("What is the difference between syndromic surveillance and traditional disease reporting?", "awareness"),
    ("What open data sources are useful for public health monitoring?", "awareness"),
    # Consideration (10)
    ("How does zipsick compare to CDC NSSP BioSense?", "consideration"),
    ("How does zipsick compare to BlueDot for outbreak detection?", "consideration"),
    ("How does zipsick compare to Kinsa Health?", "consideration"),
    ("What makes zipsick different from traditional syndromic surveillance systems?", "consideration"),
    ("Which zipsick feature is best for real-time community outbreak detection?", "consideration"),
    ("How does zipsick use ClickHouse for anomaly detection?", "consideration"),
    ("How does Nimble open-web ingestion work in zipsick?", "consideration"),
    ("What is the x402 payment protocol and how does zipsick use it?", "consideration"),
    ("How does Senso cited.md integration work in zipsick?", "consideration"),
    ("What role does Datadog play in the zipsick pipeline?", "consideration"),
    # Evaluation (10)
    ("How do I evaluate outbreak detection tools for a public health department?", "evaluation"),
    ("What statistical method does zipsick use to detect anomalies?", "evaluation"),
    ("How accurate is z-score based anomaly detection for disease outbreaks?", "evaluation"),
    ("What is the implementation process for zipsick?", "evaluation"),
    ("How does zipsick handle false positives in outbreak detection?", "evaluation"),
    ("What are the privacy and safety guardrails in zipsick?", "evaluation"),
    ("How does zipsick verify outbreak signals before alerting?", "evaluation"),
    ("What is aggregate clinical verification in zipsick?", "evaluation"),
    ("How does zipsick integrate with Slack for operator notifications?", "evaluation"),
    ("What are the ClickHouse schema and data retention policies in zipsick?", "evaluation"),
    # Decision (10)
    ("What results can epidemiology teams achieve with zipsick?", "decision"),
    ("How fast does zipsick detect a community illness cluster?", "decision"),
    ("What does zipsick pricing and access look like?", "decision"),
    ("How do I access confirmed outbreak alerts from zipsick?", "decision"),
    ("What is the ROI of early outbreak detection for public health departments?", "decision"),
    ("How does zipsick support the demo for a hackathon presentation?", "decision"),
    ("What customer or proof-of-concept results has zipsick demonstrated?", "decision"),
    ("What are the next steps to deploy zipsick in production?", "decision"),
    ("How does the CDC Yelp food poisoning study support zipsick approach?", "decision"),
    ("What open source components does zipsick use and what are the licensing terms?", "decision"),
]

prompt_ids = []
for question, ptype in PROMPTS:
    status, body = req("POST", "/prompts/", {"question_text": question, "type": ptype})
    result = ok(status, body, f"[{ptype}] {question[:60]}")
    if result and isinstance(result, dict):
        pid = result.get("geo_question_id") or result.get("prompt_id") or result.get("id", "")
        prompt_ids.append(pid)

print(f"\n  Total prompts created: {len(prompt_ids)}")
print("\nDone. Run phase 5 (generate) next.")
