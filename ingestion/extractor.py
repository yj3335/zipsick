# ingestion/extractor.py

from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone
from ingestion.models import OutbreakSignal

SYMPTOMS = {
    "gi": [r"food poisoning", r"vomit", r"nausea", r"diarrhea", r"stomach bug", r"norovirus", r"gastro"],
    "respiratory": [r"cough", r"sore throat", r"flu", r"covid", r"rsv", r"shortness of breath"],
    "rash": [r"rash", r"hives", r"itching"],
    "general": [r"fever", r"chills", r"body aches", r"outbreak", r"cluster"],
}

NYC_ZIP = re.compile(r"\b(10[0-2]\d{2}|103\d{2}|104\d{2}|11[1-6]\d{2})\b")


def extract_signals(
    text: str,
    source_type: str,
    source_url: str | None,
    fallback_zip: str | None = None,
    run_id: str | None = None,
    synthetic: bool = False,
) -> list[OutbreakSignal]:
    """
    Parse free text for NYC ZIP codes and symptom keywords.
    Returns one OutbreakSignal per (zip, symptom) match.
    """
    low = text.lower()
    zip_match = NYC_ZIP.search(text)
    zip_code = zip_match.group(1) if zip_match else fallback_zip
    if not zip_code:
        return []

    signals = []
    for symptom, patterns in SYMPTOMS.items():
        if any(re.search(pattern, low) for pattern in patterns):
            evidence = " ".join(text.split())[:600]
            event_id = hashlib.sha256(f"{source_url}|{symptom}|{evidence}".encode()).hexdigest()[:24]
            signals.append(
                OutbreakSignal(
                    event_id=event_id,
                    run_id=run_id,
                    timestamp=datetime.now(timezone.utc),
                    zip=zip_code,
                    symptom=symptom,
                    source_type=source_type,
                    source_url=source_url,
                    evidence_text=evidence,
                    confidence=0.75,
                    synthetic=synthetic,
                )
            )
    return signals
