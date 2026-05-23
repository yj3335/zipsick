# ingestion/yelp.py
# Ingestion lane for public Yelp search results (NYC food poisoning).

import os
from ingestion.nimble_client import fetch_public_page
from config.sources import YELP_SEARCH_URL


def fetch_yelp_reviews() -> str:
    """
    Fetch Yelp search results page for food poisoning in NYC.
    Returns the raw HTML string (or mock data).
    """
    mode = os.environ.get("NIMBLE_MODE", "mock")

    if mode == "mock":
        return (
            "<html><body>"
            "<h3>Reviews for NYC restaurants</h3>"
            "<div>"
            "<p>Had terrible food poisoning and diarrhea from a diner in 10014. "
            "Felt super sick and was vomiting all night long.</p>"
            "<p>Nausea and stomach bug after eating at a burger place in 10014.</p>"
            "</div>"
            "</body></html>"
        )

    # Real open-web fetch via Nimble proxy/crawling
    try:
        return fetch_public_page(YELP_SEARCH_URL)
    except Exception as exc:
        print(f"[yelp] Failed to fetch Yelp search results via Nimble: {exc}")
        return ""
