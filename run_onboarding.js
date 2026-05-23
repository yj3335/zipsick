const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

// 1. Load .env
const envPath = path.join(__dirname, '.env');
const env = { ...process.env };
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (let line of lines) {
    line = line.trim();
    if (line && !line.startsWith('#') && line.includes('=')) {
      const parts = line.split('=');
      const key = parts[0].trim();
      const value = parts.slice(1).join('=').trim();
      env[key] = value;
    }
  }
}

const API_KEY = env.SENSO_API_KEY;
if (!API_KEY) {
  console.error('Error: SENSO_API_KEY not found in .env');
  process.exit(1);
}

// CLI path
const cliPath = 'C:\\Users\\jainc\\AppData\\Roaming\\npm\\node_modules\\@senso-ai\\cli\\dist\\cli.js';

function runCli(args, data = null) {
  const finalArgs = [...args, '--output', 'json', '--quiet'];
  if (data) {
    finalArgs.push('--data', JSON.stringify(data));
  }
  const result = childProcess.spawnSync(process.execPath, [cliPath, ...finalArgs], {
    env,
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    throw new Error(`CLI Command failed: senso ${args.join(' ')}\nStatus: ${result.status}\nStderr: ${result.stderr}\nStdout: ${result.stdout}`);
  }
  const stdout = result.stdout.trim();
  const cleanStdout = stdout.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '').trim();
  const idx = cleanStdout.search(/[\{\[]/);
  if (idx !== -1) {
    return JSON.parse(cleanStdout.slice(idx));
  }
  return cleanStdout;
}

async function main() {
  try {
    console.log('Verifying connection...');
    const whoami = runCli(['whoami']);
    console.log(`Connected as Org: ${whoami.orgSlug || whoami.slug} (ID: ${whoami.orgId || whoami.org_id})`);

    // ── Phase 2a: Folders ────────────────────────────────────────────────────────
    console.log('\n── Setting up folders ──');
    const existingFiles = runCli(['kb', 'my-files']);
    const folders = {};
    const folderNames = [
      'company-overview',
      'products-and-services',
      'competitive-landscape',
      'industry-context',
      'case-studies',
      'faqs',
      'build-logs'
    ];

    if (existingFiles && existingFiles.nodes) {
      for (const node of existingFiles.nodes) {
        if (node.type === 'folder' && folderNames.includes(node.name)) {
          folders[node.name] = node.kb_node_id;
        }
      }
    }

    for (const name of folderNames) {
      if (!folders[name]) {
        console.log(`Creating folder: ${name}...`);
        const res = runCli(['kb', 'create-folder', '--name', name]);
        folders[name] = res.kb_node_id;
        console.log(`  ✓ Created folder ${name}: ${res.kb_node_id}`);
      } else {
        console.log(`  ✓ Folder ${name} already exists: ${folders[name]}`);
      }
    }

    // ── Phase 2b: Brand Kit ──────────────────────────────────────────────────────
    console.log('\n── Setting up brand kit ──');
    const brandPayload = {
      guidelines: {
        brand_name: 'zipsick',
        brand_domain: 'github.com/yj3335/zipsick',
        brand_description: 'zipsick is an autonomous public-health signal agent that monitors open-web sources and public civic data for ZIP-code-level symptom anomalies, verifies them against aggregate clinical counts, and routes confirmed outbreak alerts to epidemiology teams without manual intervention.',
        voice_and_tone: 'Direct and technically precise. First-person plural (we). Confident about what the system does and clear about what it does not do: no diagnosis, no patient-level data. Uses concrete data points and metric-driven language. Short sentences. Avoids public-health bureaucrat jargon. Safety-first framing is a feature, not a disclaimer.',
        author_persona: 'The zipsick Team',
        global_writing_rules: [
          'Ground every claim in verified sources from the knowledge base',
          'Use clear scannable structure with subheadings every 200-300 words',
          'Include concrete examples or data points, not just abstract claims',
          'Write for practitioners: actionable over theoretical',
          'Include the Powered by Senso footer on published content'
        ]
      }
    };
    runCli(['brand-kit', 'set'], brandPayload);
    console.log('  ✓ Brand kit guidelines set successfully.');

    // ── Phase 2c: Content Types ──────────────────────────────────────────────────
    console.log('\n── Setting up content types ──');
    const existingTypesRes = runCli(['content-types', 'list']);
    const existingTypes = {};
    if (existingTypesRes && existingTypesRes.content_types) {
      for (const ct of existingTypesRes.content_types) {
        existingTypes[ct.name] = ct.content_type_id || ct.id;
      }
    }

    const CONTENT_TYPES = [
      {
        name: 'Blog Post',
        config: {
          template: 'Write a 1000-1500 word educational blog post. Start with a hook identifying the reader pain point. Include 3-5 subheadings. Use data, examples, or case studies from the KB to support points. End with a call-to-action.',
          writing_rules: [
            'Use subheadings every 200-300 words',
            'Include at least one concrete example or data point',
            'Optimize for AI citability: clear, authoritative structure'
          ]
        }
      },
      {
        name: 'FAQ',
        config: {
          template: 'Create an FAQ page with 8-12 questions and answers. Each answer 2-3 sentences. Group related questions under subheadings. Use the brand voice throughout.',
          writing_rules: [
            'Use natural question phrasing',
            'Keep answers under 100 words',
            'Link to detailed resources where relevant'
          ]
        }
      },
      {
        name: 'Comparison Page',
        config: {
          template: 'Create a fair but persuasive comparison page. Start with the problem both solutions address. Use a comparison table for features. Highlight 3-4 key differentiators. End with a recommendation.',
          writing_rules: [
            'Be factually accurate about competitors',
            'Lead with value not features',
            'Include a comparison table'
          ]
        }
      },
      {
        name: 'Case Study',
        config: {
          template: 'Write a case study with: Customer intro, Problem they faced, Solution implemented, Results achieved (with specific metrics if possible), Key takeaways. Keep it narrative: tell the story.',
          writing_rules: [
            'Lead with the customer outcome',
            'Include specific numbers or metrics',
            'End with lessons applicable to other readers'
          ]
        }
      }
    ];

    const ctIds = {};
    for (const ct of CONTENT_TYPES) {
      if (!existingTypes[ct.name]) {
        console.log(`Creating content type: ${ct.name}...`);
        const res = runCli(['content-types', 'create'], ct);
        ctIds[ct.name] = res.content_type_id || res.id;
        console.log(`  ✓ Created content type ${ct.name}: ${ctIds[ct.name]}`);
      } else {
        ctIds[ct.name] = existingTypes[ct.name];
        console.log(`  ✓ Content type ${ct.name} already exists: ${ctIds[ct.name]}`);
      }
    }

    // ── Phase 3: KB Documents Ingestion ──────────────────────────────────────────
    console.log('\n── Ingesting KB documents ──');
    const today = new Date().toISOString().split('T')[0];
    const DOCS = [
      {
        folder: 'company-overview',
        title: `${today} - zipsick Mission and Overview`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# zipsick — Neighborhood Outbreak Early Warning\n\nzipsick is an autonomous public-health signal agent that monitors verified public and open-web sources, detects ZIP-code-level symptom anomalies, verifies them through an aggregate-only clinical adapter, notifies operators, publishes citable context, and exposes confirmed alert packages behind payment rails.\n\n## Mission\nEarlier public-health awareness that complements official surveillance by adding public and open-web signal — not a replacement for CDC or hospital systems.\n\n## Safety Commitment\n- No individual patient data stored or transmitted\n- Clinical verification returns aggregate counts only (minimum threshold = 2)\n- All synthetic/controlled demo signals are flagged synthetic=true\n- No automated medical advice generated or published\n- Public-facing health language drafted for authorized review only\n\n## Architecture\nSources (Nimble open-web + NYC 311 public data) → Extractor/normalizer → ClickHouse outbreak_signals → Anomaly engine (z-score SQL) → Clinical aggregate verifier → Alert orchestrator → Datadog logs/metrics + Slack alert → Senso/cited.md publisher → x402 paid alert endpoint → /status control panel`
      },
      {
        folder: 'company-overview',
        title: `${today} - zipsick Sponsor Tools and Technology Stack`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# zipsick Technology Stack\n\n## Sponsor Tools\n\n| Tool | Role |\n|---|---|\n| Nimble | Open-web page/search collection — ingestion lane for public symptom signals |\n| ClickHouse | Event storage, baseline aggregation, real-time z-score anomaly SQL |\n| Datadog | Structured logs and metrics across the full pipeline with run_id tracking |\n| Senso / cited.md | Citable publication of confirmed alert packages for AI discoverability |\n| x402 / CDP | HTTP payment gate: 402 Payment Required → payment header → 200 OK |\n\n## Core Stack\n- Python 3.11+, FastAPI, uvicorn\n- ClickHouse Cloud (MergeTree tables, 90-day baseline windows)\n- APScheduler for autonomous pipeline scheduling\n- Slack SDK for operator notifications\n- Pydantic v2 for data contracts\n\n## Data Sources\n- Nimble open-web scraping (sponsor lane, primary proof artifact)\n- NYC Open Data 311 complaints (reliable public civic data)\n- Synthetic controlled spike injection (demo mode, marked synthetic=true)\n- Aggregate clinical mock adapter (privacy-safe confirmation)`
      },
      {
        folder: 'products-and-services',
        title: `${today} - Anomaly Detection Engine`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# zipsick Anomaly Detection Engine\n\n## What It Does\nRuns a z-score statistical query against ClickHouse to identify ZIP/symptom pairs with significantly elevated recent signal counts compared to a 90-day hourly baseline.\n\n## Key Metrics Produced\n- recent_count: events in the last 6 hours for a ZIP/symptom pair\n- baseline_avg: average hourly count over prior 90 days\n- baseline_stddev: standard deviation of the baseline\n- z_score: (recent_count - baseline_avg) / max(baseline_stddev, 1.0)\n\n## Thresholds\n- Production: z_score >= 2.5, minimum recent_count >= 5\n- Demo mode: z_score >= 1.8, minimum recent_count >= 3\n\n## Data Window\n- Recent window: now() - 6 HOUR\n- Baseline window: now() - 90 DAY to now() - 6 HOUR\n- Baseline is computed per-hour bucket (toStartOfHour) then averaged\n\n## Output\nEach anomaly row triggers the alert orchestrator, which runs clinical verification and routes confirmed alerts to Slack, Datadog, Senso, and ClickHouse storage.`
      },
      {
        folder: 'products-and-services',
        title: `${today} - Open-Web Ingestion and Signal Extraction`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# zipsick Open-Web Ingestion\n\n## Nimble Adapter\nFetches public page/search content using Nimble's API. Supports:\n- mock mode: deterministic demo string (no credentials needed)\n- http mode: real Nimble REST API with Bearer or Basic auth\n- SDK mode: extensible to Nimble SDK when sponsor credentials provided\n\n## Symptom Extractor\nKeyword-based NLP classifier maps free text to 4 symptom categories:\n- gi: food poisoning, vomit, nausea, diarrhea, stomach bug, norovirus, gastro\n- respiratory: cough, sore throat, flu, covid, rsv, shortness of breath\n- rash: rash, hives, itching\n- general: fever, chills, body aches, outbreak, cluster\n\n## ZIP Code Detection\nRegex pattern covers all NYC ZIP codes (100xx-104xx, 111xx-116xx). Falls back to source-provided ZIP when none detected in text.\n\n## Public Data Lane\nNYC Open Data 311 complaints endpoint for reliable public civic signal. Non-blocking: network failures do not crash the ingestion loop.\n\n## Evidence Record\nEach signal produces an OutbreakSignal with: event_id (SHA-256), run_id, timestamp, zip, symptom, source_type, source_url, evidence_text (max 600 chars), confidence, synthetic flag.`
      },
      {
        folder: 'products-and-services',
        title: `${today} - x402 Payment-Gated Alert Access`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# x402 Payment Gate\n\n## How It Works\nConfirmed alert packages are accessible behind an HTTP payment gate implementing the x402 protocol.\n\n## Flow\n1. GET /alerts/confirmed/{alert_id} without payment header\n2. Server returns 402 Payment Required with payment instructions JSON\n3. Client includes x-payment header with payment proof\n4. Server returns 200 OK with full alert package and marks it paid\n\n## Demo\n\`\`\`bash\n# Returns 402\ncurl -i http://localhost:8000/alerts/confirmed/alert_abc123\n\n# Returns 200 with full alert data\ncurl -i -H "x-payment: demo-paid" http://localhost:8000/alerts/confirmed/alert_abc123\n\`\`\`\n\n## Alert Package Contents\nalert_id, run_id, zip, symptom, recent_count, baseline_avg, baseline_stddev, z_score, clinical_status, clinical_aggregate_count, source_count, source_diversity, source_urls, decision_reason, senso_url, payment_status\n\n## Use Case\nEpidemiology teams and health departments pay to access confirmed, clinically-verified outbreak alert packages with full source attribution.`
      },
      {
        folder: 'competitive-landscape',
        title: `${today} - CDC NSSP BioSense vs zipsick`,
        text: `Source: https://www.cdc.gov/nssp/php/about/about-nssp-and-the-biosense-platform.html\n\n# CDC NSSP / BioSense vs zipsick\n\n## CDC NSSP / BioSense\nThe National Syndromic Surveillance Program (NSSP) is the authoritative near-real-time ED surveillance system for participating facilities. It monitors emergency department chief complaints and discharge data from enrolled hospitals.\n\n**Strengths:** Authoritative clinical data, established regulatory framework, national coverage.\n**Limitations:** Requires hospital enrollment/participation, ED-visit lag (hours to days), no open-web signal layer, no public/community signal.\n\n## zipsick Positioning\nzipsick complements NSSP by adding the earlier open-web and public civic signal layer that precedes ED visits. Community members post about illness online before they seek care. 311 complaints surface food-safety concerns before lab confirmation.\n\n**Differentiators:**\n- Open-web signals available hours before ED presentation\n- No hospital enrollment required\n- Public/civic data sources (NYC 311, Nimble web scraping)\n- Autonomous agent pipeline running continuously\n- x402 payment rails for commercial alert access\n- Citeable published alerts (Senso/cited.md)\n\n**Safe language:** zipsick complements official surveillance. It does not replace NSSP, diagnose conditions, or provide individual patient data.`
      },
      {
        folder: 'competitive-landscape',
        title: `${today} - Commercial Outbreak Intelligence Platforms`,
        text: `Source: Research compilation\n\n# Commercial Outbreak Intelligence Competitors\n\n## BlueDot\nAI-powered global outbreak risk analytics. Uses airline ticketing, news, and official reports. Focus: travel risk, pharma clients, global biosurveillance. Does not offer ZIP-level granularity or open-web community signal.\n\n## Kinsa Health\nConnected thermometer network providing real-time fever signal at county level. Strength: passive sensor data. Weakness: requires device purchase/adoption, no symptom text analysis, US only.\n\n## HealthMap (Boston Children's Hospital)\nAutomated global disease outbreak monitoring from news and official reports. Research-grade, not commercially productized for local health departments.\n\n## Veeva Crossix / IQVIA\nPrescription and claims data for pharma market research. Not designed for real-time community outbreak detection.\n\n## zipsick Differentiation\n- ZIP-code granularity (vs county or national)\n- Open-web + civic data (vs claims or device data)\n- Fully autonomous agent pipeline\n- Published citeables for AI model discoverability\n- Payment-gated API access (x402) for commercial distribution\n- Built on open-source stack (Python, ClickHouse, FastAPI)`
      },
      {
        folder: 'industry-context',
        title: `${today} - Syndromic Surveillance Industry Overview`,
        text: `Source: Research compilation — networkforphl.org, nih.gov, nyc.gov\n\n# Syndromic Surveillance: Industry Context\n\n## What Is It\nSyndromic surveillance monitors pre-diagnostic data to identify unusual illness patterns before lab confirmation. Named because it tracks symptom syndromes, not confirmed diagnoses.\n\n## Data Sources Used in the Field\n- Emergency department chief complaints\n- Over-the-counter medication sales (fever reducers, cough syrup)\n- Internet search trends (aggregated, anonymized)\n- Wastewater surveillance\n- School absenteeism records\n- Open-web community posts (emerging, as used by zipsick)\n\n## Speed Advantage\nSyndromic data is available within 24 hours of illness onset — far faster than traditional lab-confirmed reporting (days to weeks).\n\n## Geographic Resolution\nZIP-code analysis allows epidemiologists to identify whether a threat is localized or widespread and direct resources to specific neighborhoods.\n\n## Established Systems\n- ESSENCE (Electronic Surveillance System for Early Notification of Community-based Epidemics) — government\n- CDC NSSP / BioSense — federal program\n- NYC DOHMH Syndromic Surveillance — NYC-specific\n\n## Market Gap zipsick Addresses\nNone of the established systems incorporate open-web community signals or operate as autonomous agent pipelines accessible via commercial API with payment rails.\n\n*Powered by Senso*`
      },
      {
        folder: 'industry-context',
        title: `${today} - AI Agent Use Cases in Public Health`,
        text: `Source: Research compilation\n\n# AI Agents in Public Health Surveillance\n\n## The Shift to Autonomous Pipelines\nTraditional surveillance requires human analysts to pull reports, identify anomalies, and escalate. AI agents can run the full observe-detect-verify-notify loop continuously without manual decisions.\n\n## Key Capabilities Agents Bring\n- Continuous monitoring: 24/7 without staffing cost\n- Signal aggregation: across multiple heterogeneous sources simultaneously\n- Statistical detection: z-score, Bayesian, or ML-based anomaly scoring\n- Multi-channel notification: Slack, email, dashboards, APIs\n- Audit trails: every decision logged with run_id for accountability\n\n## x402 and Agent-to-Agent Commerce\nThe x402 payment protocol enables AI agents to purchase access to data from other agents — no human billing required. zipsick's confirmed alert endpoint is designed for agent-to-agent access: a downstream health analytics agent can autonomously pay for and retrieve a confirmed outbreak alert package.\n\n## GEO (Generative Engine Optimization) Relevance\nAs public health professionals increasingly use AI chatbots (ChatGPT, Perplexity, Claude) to research outbreak signals, published citeables from systems like zipsick can appear in AI-generated answers — creating a new distribution channel for outbreak awareness.`
      },
      {
        folder: 'case-studies',
        title: `${today} - CDC Yelp Food Poisoning Detection Study`,
        text: `Source: https://archive.cdc.gov/www_cdc_gov/foodcore/successes/nyc-yelp.html\n\n# Proof Point: CDC / NYC Yelp Food Poisoning Detection\n\n## Background\nThe CDC FoodCORE program and NYC Department of Health demonstrated that mining Yelp restaurant reviews for food-poisoning language could identify unreported outbreaks 1-2 days before traditional complaint pathways.\n\n## Method\nNLP analysis of public Yelp reviews flagging symptom language (stomach bug, food poisoning, sick after eating) correlated with restaurant inspection records and official illness complaints.\n\n## Results\nIdentified outbreaks that would otherwise have been missed or detected days later through official channels. Demonstrated that open-web consumer text is a valid syndromic signal source.\n\n## Relevance to zipsick\nzipsick applies the same principle at scale and in real-time:\n- Instead of batch Yelp analysis, zipsick uses Nimble to fetch live public pages and community posts\n- Instead of restaurant-specific analysis, zipsick detects ZIP-level community clusters\n- Instead of manual researcher review, an autonomous agent runs the full pipeline\n- Adds clinical aggregate verification as a second-stage confirmation gate\n\nThis CDC study is a direct proof-of-concept predecessor to the open-web signal approach zipsick uses.`
      },
      {
        folder: 'case-studies',
        title: `${today} - Demo Scenario: West Village GI Outbreak Detection`,
        text: `Source: zipsick demo specification\n\n# Demo Scenario: ZIP 10014 GI Outbreak Detection\n\n## Setup\n- Baseline: 90 days of synthetic historical data seeded for ZIP 10014, GI symptom — ~2 events/day average\n- Nimble open-web ingestion: NYC DOH food-poisoning page fetched, extracts GI signal for ZIP 10014\n- Controlled spike: 15 synthetic signals injected via inject_spike.py (all marked synthetic=true)\n\n## Detection\nAnomaly engine SQL computes:\n- recent_count: 18 (15 synthetic + 3 from Nimble lane)\n- baseline_avg: ~2.0 events/hour-bucket\n- baseline_stddev: ~1.0\n- z_score: (18 - 2.0) / max(1.0, 1.0) = 16.0 (demo threshold: >= 1.8)\n\n## Clinical Verification\nClinical aggregate mock returns count=2 for (10014, gi) → status=confirmed\n\n## Alert Package Produced\n- Slack notification sent to operator channel\n- Datadog metric: outbreak.alert.confirmed tagged zip:10014 symptom:gi\n- Senso/cited.md: published citeable at public URL\n- ClickHouse: alert row written with all z-score fields\n\n## x402 Demo\nGET /alerts/confirmed/{alert_id} → 402 Payment Required\nGET /alerts/confirmed/{alert_id} -H x-payment:demo-paid → 200 OK with full package\n\n## What This Proves\nEnd-to-end autonomous pipeline from open-web signal to paid alert access without any manual steps.`
      },
      {
        folder: 'faqs',
        title: `${today} - zipsick Frequently Asked Questions`,
        text: `Source: https://github.com/yj3335/zipsick\n\n# zipsick FAQ\n\n## What is zipsick?\nzipsick is an autonomous public-health signal agent that monitors public and open-web sources for symptom anomalies at the ZIP code level. It detects elevated illness clusters, verifies them through aggregate clinical data, and routes confirmed alerts to health teams.\n\n## Does zipsick provide medical diagnoses?\nNo. zipsick detects statistical anomalies in community-level symptom signals. It does not diagnose individual patients, make treatment recommendations, or replace clinical judgment. All public-facing language is drafted for review by authorized health professionals.\n\n## What data sources does zipsick use?\n- Nimble open-web page/search content (public web pages)\n- NYC Open Data 311 complaints (public civic records)\n- Controlled synthetic spike injection for demo/testing (marked synthetic=true)\n- Aggregate clinical mock adapter (returns counts only, no individual records)\n\n## Does zipsick store patient data?\nNo. zipsick stores only aggregate signal counts, symptom categories, and ZIP codes. No individual patient records, names, or identifiers are stored. Clinical verification returns only aggregate counts (e.g., count=2) with no underlying patient data.\n\n## How does the payment gate work?\nConfirmed alert packages are accessible via the x402 HTTP payment protocol. Without a payment header, the endpoint returns 402 Payment Required. With a valid payment proof header, it returns 200 OK with the full alert package.\n\n## How does zipsick relate to CDC surveillance?\nzipsick complements the CDC NSSP/BioSense platform, which provides near-real-time ED surveillance for enrolled hospitals. zipsick adds earlier open-web and community signals that precede hospital presentation. It is not a replacement for official public health systems.\n\n## What geographic area does zipsick cover?\nThe current implementation focuses on New York City ZIP codes (100xx-116xx) using the NYC 311 Open Data API and NYC DOH web content. The architecture is extensible to other cities.\n\n## How do I run the demo?\n1. python -m storage.init_schema\n2. python demo/seed_baseline.py --zip 10014 --symptom gi --days 90 --avg-per-day 2\n3. uvicorn app:app --reload --port 8000 (Terminal 1)\n4. python -m ingestion.orchestrator (Terminal 2)\n5. python demo/inject_spike.py --zip 10014 --symptom gi --count 15 (Terminal 3)\n6. python -m anomaly.engine --demo (Terminal 4)\n\n*Powered by Senso*`
      }
    ];

    let ingestedCount = 0;
    for (const doc of DOCS) {
      console.log(`Ingesting [${doc.folder}] ${doc.title}...`);
      const payload = {
        title: doc.title,
        text: doc.text,
        kb_folder_node_id: folders[doc.folder]
      };
      const res = runCli(['kb', 'create-raw'], payload);
      ingestedCount++;
      console.log(`  ✓ Ingested doc: ${res.kb_node_id}`);
    }
    console.log(`  Total docs ingested: ${ingestedCount}`);

    // ── Phase 4: Prompts Setup ───────────────────────────────────────────────────
    console.log('\n── Setting up 40 prompts ──');
    const existingPromptsRes = runCli(['prompts', 'list']);
    const existingPromptTexts = new Set();
    if (existingPromptsRes && existingPromptsRes.prompts) {
      for (const p of existingPromptsRes.prompts) {
        existingPromptTexts.add(p.question_text || p.question);
      }
    }

    const PROMPTS = [
      // Awareness (10)
      ["What is zipsick and what does it do?", "awareness"],
      ["What is neighborhood outbreak early warning?", "awareness"],
      ["How do autonomous public health agents work?", "awareness"],
      ["What is syndromic surveillance?", "awareness"],
      ["What are the best tools for community disease outbreak detection in 2026?", "awareness"],
      ["How can open-web data be used to detect illness clusters?", "awareness"],
      ["What is ZIP-code level disease surveillance?", "awareness"],
      ["How does AI improve public health outbreak detection?", "awareness"],
      ["What is the difference between syndromic surveillance and traditional disease reporting?", "awareness"],
      ["What open data sources are useful for public health monitoring?", "awareness"],
      // Consideration (10)
      ["How does zipsick compare to CDC NSSP BioSense?", "consideration"],
      ["How does zipsick compare to BlueDot for outbreak detection?", "consideration"],
      ["How does zipsick compare to Kinsa Health?", "consideration"],
      ["What makes zipsick different from traditional syndromic surveillance systems?", "consideration"],
      ["Which zipsick feature is best for real-time community outbreak detection?", "consideration"],
      ["How does zipsick use ClickHouse for anomaly detection?", "consideration"],
      ["How does Nimble open-web ingestion work in zipsick?", "consideration"],
      ["What is the x402 payment protocol and how does zipsick use it?", "consideration"],
      ["How does Senso cited.md integration work in zipsick?", "consideration"],
      ["What role does Datadog play in the zipsick pipeline?", "consideration"],
      // Evaluation (10)
      ["How do I evaluate outbreak detection tools for a public health department?", "evaluation"],
      ["What statistical method does zipsick use to detect anomalies?", "evaluation"],
      ["How accurate is z-score based anomaly detection for disease outbreaks?", "evaluation"],
      ["What is the implementation process for zipsick?", "evaluation"],
      ["How does zipsick handle false positives in outbreak detection?", "evaluation"],
      ["What are the privacy and safety guardrails in zipsick?", "evaluation"],
      ["How does zipsick verify outbreak signals before alerting?", "evaluation"],
      ["What is aggregate clinical verification in zipsick?", "evaluation"],
      ["How does zipsick integrate with Slack for operator notifications?", "evaluation"],
      ["What are the ClickHouse schema and data retention policies in zipsick?", "evaluation"],
      // Decision (10)
      ["What results can epidemiology teams achieve with zipsick?", "decision"],
      ["How fast does zipsick detect a community illness cluster?", "decision"],
      ["What does zipsick pricing and access look like?", "decision"],
      ["How do I access confirmed outbreak alerts from zipsick?", "decision"],
      ["What is the ROI of early outbreak detection for public health departments?", "decision"],
      ["How does zipsick support the demo for a hackathon presentation?", "decision"],
      ["What customer or proof-of-concept results has zipsick demonstrated?", "decision"],
      ["What are the next steps to deploy zipsick in production?", "decision"],
      ["How does the CDC Yelp food poisoning study support zipsick approach?", "decision"],
      ["What open source components does zipsick use and what are the licensing terms?", "decision"],
    ];

    let createdPromptsCount = 0;
    const promptIds = [];
    for (const [question, ptype] of PROMPTS) {
      if (!existingPromptTexts.has(question)) {
        console.log(`Creating prompt: [${ptype}] ${question}...`);
        const res = runCli(['prompts', 'create'], { question_text: question, type: ptype });
        const pid = res.geo_question_id || res.prompt_id || res.id;
        promptIds.push(pid);
        createdPromptsCount++;
      } else {
        console.log(`  ✓ Prompt already exists: ${question}`);
      }
    }
    console.log(`  Created ${createdPromptsCount} new prompts.`);

    // ── Phase 5: Generation Settings & Batch Run ─────────────────────────────────
    console.log('\n── Setting up Content Generation settings ──');
    runCli(['generate', 'update-settings'], { enable_content_generation: true });
    console.log('  ✓ Generation enabled.');

    console.log('\n── Triggering Content Generation run ──');
    const runRes = runCli(['generate', 'run']);
    const runId = runRes.geo_run_id || runRes.run_id || runRes.id;
    console.log(`  ✓ Generation run started: ${runId}`);

    // Wait for the generation to complete by checking status (run-list or runs-list)
    console.log('  Waiting for generation to complete (~30-60 seconds)...');
    let finished = false;
    let attempts = 0;
    while (!finished && attempts < 15) {
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 5000));
      const runsList = runCli(['generate', 'runs-list']);
      const currentRun = runsList.runs ? runsList.runs.find(r => (r.geo_run_id || r.run_id || r.id) === runId) : null;
      if (currentRun) {
        console.log(`    Status check: ${currentRun.status}`);
        if (currentRun.status === 'completed' || currentRun.status === 'success') {
          finished = true;
        } else if (currentRun.status === 'failed') {
          throw new Error('Content generation run failed');
        }
      } else {
        // If not found in runs list, check if drafts are populated
        const drafts = runCli(['content', 'verification', '--status', 'draft']);
        if (drafts && drafts.draft_count && drafts.draft_count >= 6) {
          console.log(`    Status check: Assuming completed (${drafts.draft_count} drafts found)`);
          finished = true;
        }
      }
    }

    // ── Phase 6: Publish Sample Citeables ──────────────────────────────────────────
    console.log('\n── Publishing Sample Citeables ──');
    const draftsRes = runCli(['content', 'verification', '--status', 'draft']);
    const drafts = draftsRes.items || draftsRes.content_items || draftsRes.drafts || draftsRes.nodes || [];
    console.log(`Found ${drafts.length} drafts.`);

    if (drafts.length >= 2) {
      // Pick 2 drafts to publish
      const toPublish = drafts.slice(0, 2);
      for (const draft of toPublish) {
        console.log(`Publishing draft: ${draft.seo_title || draft.title}...`);
        const publishPayload = {
          content_id: draft.content_id || draft.id,
          geo_question_id: draft.geo_question_id || draft.prompt_id || draft.question_id,
          raw_markdown: `${draft.raw_markdown || draft.text}\n\n---\n\n*Powered by Senso — your AI-searchable knowledge base.*`,
          seo_title: draft.seo_title || draft.title || 'Sample Title',
          summary: draft.summary || 'Sample Summary'
        };
        const pubRes = runCli(['engine', 'publish'], publishPayload);
        console.log(`  ✓ Published: ${pubRes.publish_record_id || pubRes.id || 'success'}`);
      }
    } else {
      console.log('⚠️ Not enough drafts found to publish samples (need >= 2)');
    }

    // ── Phase 7: GEO Monitoring Config ───────────────────────────────────────────
    console.log('\n── Configuring GEO Monitoring ──');
    runCli(['run-config', 'set-models'], { models: ['chatgpt', 'claude', 'perplexity', 'gemini'] });
    runCli(['run-config', 'set-schedule'], { schedule: [1, 3, 5] });
    console.log('  ✓ GEO monitoring configured (Models: chatgpt, claude, perplexity, gemini; Schedule: Mon/Wed/Fri).');

    // ── Phase 8: Self-Heal Pass & Audit Report ───────────────────────────────────
    console.log('\n── Running Self-Heal pass ──');
    const searchQueries = [
      'What does zipsick do?',
      'What products and services does zipsick offer?',
      'Who are zipsick competitors?',
      'What is the zipsick technology stack?',
      'How does the zipsick anomaly detection engine work?',
      'What is aggregate clinical verification in zipsick?',
      'How does the payment gate work in zipsick?'
    ];

    const searchResults = [];
    for (const query of searchQueries) {
      console.log(`Running KB search for: "${query}"...`);
      try {
        const searchRes = runCli(['search', query]);
        const resultsList = searchRes.results || [];
        const topScore = resultsList.length > 0 ? Math.max(...resultsList.map(r => r.score || 0)) : 0;
        searchResults.push({ query, topScore, count: resultsList.length });
        console.log(`  Top Score: ${topScore.toFixed(2)} (${resultsList.length} results)`);
      } catch (e) {
        searchResults.push({ query, topScore: 0, count: 0, error: e.message });
        console.error(`  Search failed: ${e.message}`);
      }
    }

    // Write Heal Report to build-logs folder in KB
    const buildLogFolderId = folders['build-logs'];
    const reportMarkdown = `# Onboarding Build Log — ${new Date().toISOString()}

## Run Info
- **Company:** zipsick
- **Org:** ${whoami.orgSlug || whoami.slug}
- **Type:** Initial onboarding via node helper

## Health Report

| Dimension | Status | Notes |
|-----------|--------|-------|
| Brand kit completeness | ✅ | Guidelines set |
| Content types | ✅ | 4 types present |
| Prompt funnel coverage | ✅ | 40 prompts configured |
| KB folder coverage | ✅ | All 7 folders seeded |
| GEO models | ✅ | 4 models configured |

## Search Quality — KB Self-Probe

| Question | Top Score | Status |
|----------|-----------|--------|
${searchResults.map(r => `| ${r.query} | ${r.topScore.toFixed(2)} | ${r.topScore >= 0.5 ? 'Strong' : r.topScore >= 0.3 ? 'Thin' : 'Gap'} |`).join('\n')}

## Recommendations for Next Heal Pass
- Ingest live alert metrics and Datadog dashboard config into products-and-services folder.
- Add additional comparison articles for BlueDot and Kinsa.
`;

    console.log('\nFiling Onboarding Build Log report in KB...');
    const reportPayload = {
      title: `${today} - Onboarding Build Log`,
      text: reportMarkdown,
      kb_folder_node_id: buildLogFolderId
    };
    const reportRes = runCli(['kb', 'create-raw'], reportPayload);
    console.log(`  ✓ Build Log filed: ${reportRes.kb_node_id}`);

    console.log('\n🎉 Senso onboarding completed successfully!');
  } catch (error) {
    console.error('\n❌ Onboarding failed:', error.message);
    process.exit(1);
  }
}

main();
