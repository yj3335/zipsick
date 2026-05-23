# tests/test_extractor.py

import pytest
from ingestion.extractor import extract_signals


def test_gi_and_zip_extracted():
    signals = extract_signals("food poisoning in 10014", "test", "http://example.com")
    assert len(signals) == 1
    s = signals[0]
    assert s.symptom == "gi"
    assert s.zip == "10014"
    assert s.synthetic is False


def test_no_signal_without_zip_or_fallback():
    signals = extract_signals("stomach bug and vomiting everywhere", "test", None)
    assert signals == []


def test_fallback_zip_used_when_no_zip_in_text():
    signals = extract_signals("vomiting on the block", "test", None, fallback_zip="10001")
    assert len(signals) == 1
    assert signals[0].zip == "10001"


def test_multiple_symptoms_in_one_text():
    text = "fever and cough in 10014"
    signals = extract_signals(text, "test", None)
    symptoms = {s.symptom for s in signals}
    assert "respiratory" in symptoms
    assert "general" in symptoms


def test_nimble_mock_returns_extractable_signal():
    from ingestion.nimble_client import fetch_public_page
    import os
    os.environ["NIMBLE_MODE"] = "mock"
    text = fetch_public_page("https://example.com")
    signals = extract_signals(text, "nimble_open_web", "https://example.com", fallback_zip="10014")
    assert len(signals) >= 1
    assert signals[0].symptom == "gi"


def test_311_empty_records_no_crash():
    from ingestion.public_data import record_to_text
    text, zip_code = record_to_text({})
    assert isinstance(text, str)
    assert zip_code is None
