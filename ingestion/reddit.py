# ingestion/reddit.py
# Ingestion lane for public Reddit posts (r/nyc, r/AskNYC, r/newyorkcity).

import json
import os
import requests
from ingestion.nimble_client import fetch_public_page
from observability.datadog import log_event


def fetch_reddit_posts(subreddit: str) -> list[dict]:
    """
    Fetch new posts from a public subreddit.
    Returns a list of dicts: [{"title": str, "selftext": str, "url": str}]
    """
    mode = os.environ.get("NIMBLE_MODE", "mock")

    if mode == "mock":
        return [
            {
                "title": "Severe stomach bug going around West Village",
                "selftext": "My family is super sick. Diarrhea and vomiting. Anyone else in 10014 dealing with this norovirus?",
                "url": f"https://www.reddit.com/r/{subreddit}/comments/mock123",
            },
            {
                "title": "Food poisoning from a spot in NYC",
                "selftext": "Had a bad fever and nausea after eating. Be careful in 10014.",
                "url": f"https://www.reddit.com/r/{subreddit}/comments/mock456",
            }
        ]

    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=100"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Try direct HTTP request first
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return _parse_reddit_json(response.json(), subreddit)
        else:
            print(f"[reddit] Direct fetch of r/{subreddit} failed with status {response.status_code}. Retrying via Nimble...")
    except Exception as exc:
        print(f"[reddit] Direct fetch of r/{subreddit} threw exception: {exc}. Retrying via Nimble...")

    # Fallback to Nimble open-web extractor
    try:
        raw_content = fetch_public_page(url)
        data = json.loads(raw_content)
        return _parse_reddit_json(data, subreddit)
    except Exception as exc:
        log_event("reddit_ingest_failed", {"subreddit": subreddit, "error": str(exc)})
        print(f"[reddit] Failed to fetch r/{subreddit} via Nimble: {exc}")
        return []


from config.sources import HEALTH_KEYWORDS

def _parse_reddit_json(data: dict, subreddit: str) -> list[dict]:
    posts = []
    keywords = [k.strip().lower() for k in HEALTH_KEYWORDS.split(" OR ")]
    try:
        children = data.get("data", {}).get("children", [])
        for child in children:
            post_data = child.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            content_lower = (title + " " + selftext).lower()
            
            # Local keyword filtering
            if any(kw in content_lower for kw in keywords):
                posts.append({
                    "title": title,
                    "selftext": selftext,
                    "url": f"https://www.reddit.com{post_data.get('permalink', '')}"
                })
    except Exception as exc:
        print(f"[reddit] Error parsing reddit JSON for r/{subreddit}: {exc}")
    return posts
