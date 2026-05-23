# ingestion/orchestrator.py
# Top-level ingestion run: Nimble open-web lane + NYC 311 public-data lane + Reddit + Yelp.

import os
from ingestion.extractor import extract_signals
from ingestion.nimble_client import fetch_public_page
from ingestion.public_data import fetch_nyc_311_records, record_to_text
from ingestion.reddit import fetch_reddit_posts
from ingestion.yelp import fetch_yelp_reviews
from observability.datadog import log_event, emit_metric
from storage.clickhouse import insert_signals
from config.sources import NIMBLE_TARGET_URLS, REDDIT_SUBREDDITS, YELP_SEARCH_URL


def ingest_once(run_id: str | None = None) -> list:
    """
    Run one full ingestion cycle.
    1. Nimble / open-web lane (sponsor proof).
    2. NYC 311 public-data lane (reliable fallback).
    3. Reddit community public forums.
    4. Yelp search results for food poisoning.
    Returns the list of OutbreakSignal objects inserted.
    """
    signals = []

    # --- Sponsor/open-web proof lane ---
    for url in NIMBLE_TARGET_URLS:
        try:
            nimble_text = fetch_public_page(url)
            signals.extend(
                extract_signals(
                    nimble_text,
                    source_type="nimble_open_web",
                    source_url=url,
                    fallback_zip="10036",
                    run_id=run_id,
                )
            )
        except Exception as exc:
            print(f"[orchestrator] Nimble open-web lane failed for {url}: {exc}")

    # --- Reliable public-data lane ---
    try:
        for record in fetch_nyc_311_records():
            text, zip_code = record_to_text(record)
            signals.extend(
                extract_signals(
                    text,
                    source_type="nyc_311_public_data",
                    source_url=None,
                    fallback_zip=zip_code,
                    run_id=run_id,
                )
            )
    except Exception as exc:
        print(f"[orchestrator] NYC 311 lane failed: {exc}")

    # --- Reddit public forum lane ---
    for sub in REDDIT_SUBREDDITS:
        try:
            posts = fetch_reddit_posts(sub)
            for post in posts:
                content = f"{post['title']}\n{post['selftext']}"
                signals.extend(
                    extract_signals(
                        content,
                        source_type="reddit_scrape",
                        source_url=post["url"],
                        fallback_zip="10036",  # Default fallback for NYC subreddits
                        run_id=run_id,
                    )
                )
        except Exception as exc:
            print(f"[orchestrator] Reddit lane for r/{sub} failed: {exc}")

    # --- Yelp reviews lane ---
    try:
        yelp_html = fetch_yelp_reviews()
        if yelp_html:
            signals.extend(
                extract_signals(
                    yelp_html,
                    source_type="yelp_scrape",
                    source_url=YELP_SEARCH_URL,
                    fallback_zip="10036",
                    run_id=run_id,
                )
            )
    except Exception as exc:
        print(f"[orchestrator] Yelp lane failed: {exc}")

    insert_signals(signals)
    emit_metric("outbreak.events_ingested", len(signals), tags=[f"run_id:{run_id}"])
    log_event("ingestion_complete", {"run_id": run_id, "signals": len(signals)})
    return signals


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ingest_once(os.environ.get("DEMO_RUN_ID", "run_demo"))

