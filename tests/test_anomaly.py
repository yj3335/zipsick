# tests/test_anomaly.py

import pytest
from verification.clinical_aggregate import verify_clinical_aggregate


def test_clinical_confirms_10014_gi():
    result = verify_clinical_aggregate("10014", "gi")
    assert result.status == "confirmed"
    assert result.count == 2


def test_clinical_suppresses_other_zip():
    result = verify_clinical_aggregate("10012", "gi")
    assert result.status == "suppressed"
    assert result.count == 0


def test_clinical_suppresses_other_symptom():
    result = verify_clinical_aggregate("10014", "respiratory")
    assert result.status == "suppressed"


def test_clinical_result_has_note():
    result = verify_clinical_aggregate("10014", "gi")
    assert len(result.note) > 0
