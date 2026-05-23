# Zipsick Dashboard

Live Next.js dashboard that connects to the Zipsick FastAPI backend.

## Setup

```bash
cd dashboard
npm install
npm run dev
```

The dashboard proxies API calls to `http://localhost:8000` (the FastAPI backend). Make sure the backend is running first:

```bash
# From the project root
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Tabs

- **/status** — Live agent status, sponsor proof strip, signal counts, latest alerts
- **Alerts** — Latest decision detail, all alerts from ClickHouse, published alert viewer
- **Heatmap** — ZIP code map of Lower Manhattan with severity indicators
- **x402 Payment** — Interactive payment flow demo (402 → pay → 200)

## Architecture

All data comes from the backend `/status` endpoint which queries ClickHouse in real time. No mock data.
