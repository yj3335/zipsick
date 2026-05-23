# actions/senso_publish.py
# Publish confirmed alerts via Senso/cited.md API.
# Falls back to a local cited.md-compatible markdown file when credentials are absent.

from __future__ import annotationsimport os
import pathlib
import requests
from observability.datadog import emit_metric, log_event


def publish_cited_alert(package) -> str | None:
    """
    Publish a confirmed alert package.
    Returns a URL (Senso) or file path (local fallback).
    """
    url = os.environ.get("SENSO_PUBLISH_URL")
    api_key = os.environ.get("SENSO_API_KEY")

    payload = {
        "title": f"Confirmed community illness signal in ZIP {package.zip}",
        "summary": (
            f"Elevated {package.symptom} activity detected in ZIP {package.zip}. "
            f"Recent count={package.recent_count}, baseline={package.baseline_avg:.2f}, "
            f"z={package.z_score:.2f}, aggregate clinical count={package.clinical_aggregate_count}."
        ),
        "citations": package.source_urls,
        "metadata": package.model_dump(mode="json"),
    }

    is_local_publish = bool(url) and (
        url.startswith("http://localhost")
        or url.startswith("http://127.0.0.1")
        or url.startswith("http://0.0.0.0")
    )
    if url and (api_key or is_local_publish):
        try:
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            published_url = response.json().get("url")
            emit_metric("outbreak.publisher.senso.success", 1, tags=[f"alert_id:{package.alert_id}"])
            log_event("senso_published", {"alert_id": package.alert_id, "url": published_url})
            return published_url
        except Exception as exc:
            log_event("senso_publish_failed", {"alert_id": package.alert_id, "error": str(exc)})
            print(f"[senso_publish] Remote publish failed: {exc}. Falling back to local file.")

    # Local cited.md fallback — clearly labelled in logs and demo narration.
    pathlib.Path("public/alerts").mkdir(parents=True, exist_ok=True)
    path = pathlib.Path(f"public/alerts/{package.alert_id}.md")
    path.write_text(
        f"# {payload['title']}\n\n{payload['summary']}\n\nSources:\n"
        + "\n".join(f"- {u}" for u in package.source_urls),
        encoding="utf-8",
    )
    log_event("senso_fallback_written", {"alert_id": package.alert_id, "path": str(path)})
    return str(path)
