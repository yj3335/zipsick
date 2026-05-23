# tests/test_new_sources.py
# Tests the Reddit and Yelp ingestion lanes.

import os
import pytest
import unittest.mock as mock
from ingestion.reddit import fetch_reddit_posts
from ingestion.yelp import fetch_yelp_reviews
from ingestion.extractor import extract_signals
from ingestion.orchestrator import ingest_once

os.environ["NIMBLE_MODE"] = "mock"


def test_reddit_mock_returns_valid_data():
    posts = fetch_reddit_posts("nyc")
    assert isinstance(posts, list)
    assert len(posts) > 0
    assert "title" in posts[0]
    assert "selftext" in posts[0]
    assert "url" in posts[0]


def test_reddit_signals_extracted():
    posts = fetch_reddit_posts("nyc")
    post = posts[0]
    content = f"{post['title']}\n{post['selftext']}"

    signals = extract_signals(
        content,
        source_type="reddit_scrape",
        source_url=post["url"],
        fallback_zip="10014"
    )

    assert len(signals) >= 1
    assert signals[0].symptom == "gi"
    assert signals[0].zip == "10014"
    assert signals[0].source_type == "reddit_scrape"


def test_yelp_mock_returns_html():
    html = fetch_yelp_reviews()
    assert isinstance(html, str)
    assert "<html>" in html
    assert "food poisoning" in html.lower()


def test_yelp_signals_extracted():
    html = fetch_yelp_reviews()
    signals = extract_signals(
        html,
        source_type="yelp_scrape",
        source_url="http://example.com/yelp",
        fallback_zip="10014"
    )
    assert len(signals) >= 1
    assert any(s.symptom == "gi" for s in signals)
    assert any(s.zip == "10014" for s in signals)


@mock.patch("ingestion.orchestrator.insert_signals")
@mock.patch("ingestion.orchestrator.fetch_nyc_311_records", return_value=[])
@mock.patch("ingestion.orchestrator.fetch_public_page", return_value="mock page 10014 stomach bug")
def test_orchestrator_runs_all_lanes(mock_fetch_page, mock_fetch_311, mock_insert):
    signals = ingest_once(run_id="test_run")

    # Check that signals were collected from multiple sources
    source_types = {s.source_type for s in signals}
    assert "nimble_open_web" in source_types
    assert "reddit_scrape" in source_types
    assert "yelp_scrape" in source_types

    # Check that insert was called
    mock_insert.assert_called_once()
