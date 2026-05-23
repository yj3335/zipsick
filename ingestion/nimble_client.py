# ingestion/nimble_client.py
# Adapter for Nimble open-web collection.
# Supports mock (no credentials), http (real API), with easy extension to SDK mode.

import base64
import os
import requests


def fetch_public_page(url: str) -> str:
    """
    Fetch page content via Nimble (or mock).

    NIMBLE_MODE options:
      mock — returns a deterministic demo string; safe for CI and offline work.
      http — calls the real Nimble REST API using Bearer or Basic auth.
    """
    mode = os.environ.get("NIMBLE_MODE", "mock")

    if mode == "mock":
        return (
            "Food poisoning reports near West Village 10014. "
            "Multiple people mention vomiting and stomach bug."
        )

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
            json={"url": url, "parse": True, "country": "US", "locale": "en"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        nested = data.get("data")
        if isinstance(nested, dict):
            html = nested.get("html")
            if html:
                return html
        return data.get("html_content") or data.get("content") or data.get("body") or ""

    raise ValueError(f"Unsupported NIMBLE_MODE={mode}")
