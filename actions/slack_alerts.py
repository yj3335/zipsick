# actions/slack_alerts.py
# Sends a confirmed alert notification to a Slack channel.
# No-ops safely when SLACK_BOT_TOKEN or SLACK_CHANNEL_ID are not configured.

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from observability.datadog import log_event


def send_slack_alert(package) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        log_event("slack_skipped", {"reason": "no credentials", "alert_id": package.alert_id})
        return

    text = (
        "*OUTBREAK SIGNAL CONFIRMED*\n"
        f"*Alert*: `{package.alert_id}`\n"
        f"*ZIP*: {package.zip}\n"
        f"*Symptom*: {package.symptom}\n"
        f"*Z-score*: {package.z_score:.2f}\n"
        f"*Clinical aggregate*: {package.clinical_aggregate_count} matching presentations\n"
        f"*Sources*: {package.source_count}\n"
        f"*Source diversity*: {package.source_diversity}\n"
        f"*Citeable summary*: {package.senso_url or 'pending'}\n"
        "_Public-facing advisory is drafted for authorized review._"
    )

    try:
        WebClient(token=token).chat_postMessage(channel=channel, text=text)
        log_event("slack_sent", {"alert_id": package.alert_id, "channel": channel})
    except SlackApiError as exc:
        log_event("slack_error", {"alert_id": package.alert_id, "error": str(exc)})
