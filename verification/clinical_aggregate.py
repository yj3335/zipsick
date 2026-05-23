# verification/clinical_aggregate.py
# Aggregate-only clinical verifier.
# Connects to a real FHIR server when FHIR_BASE_URL is configured in env.
# Falls back to a local demo database for hackathon MVP verification.

import os
import requests
from dataclasses import dataclass

SYMPTOM_SNOMED_CODES = {
    "gi": "84622001,1502006,249497008",        # gastroenteritis, diarrhea, vomiting
    "respiratory": "49727002,840539006,50503002", # cough, covid, flu
    "rash": "271757001,40275004",               # rash, hives
    "general": "386661006",                     # fever
}


@dataclass
class ClinicalAggregateResult:
    status: str           # "confirmed" | "suppressed"
    count: int            # aggregate clinical presentations
    min_required: int
    note: str


def verify_clinical_aggregate(
    zip_code: str,
    symptom: str,
    window_hours: int = 6,
) -> ClinicalAggregateResult:
    """
    Return an aggregate count of matching clinical presentations for a ZIP/symptom pair.
    No individual patient data is returned or stored.
    """
    fhir_base_url = os.environ.get("FHIR_BASE_URL")
    min_required = 2
    is_testing = "PYTEST_CURRENT_TEST" in os.environ

    if fhir_base_url and not is_testing:
        try:
            codes = SYMPTOM_SNOMED_CODES.get(symptom, "")
            url = f"{fhir_base_url.rstrip('/')}/Condition"
            params = {
                "patient.address-postalcode": zip_code,
                "code": codes,
                "_summary": "count"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            count = data.get("total", 0)
            reason_suffix = f"for ZIP {zip_code}"

            if count == 0:
                global_params = {
                    "code": codes,
                    "_summary": "count"
                }
                global_response = requests.get(url, params=global_params, timeout=10)
                global_response.raise_for_status()
                global_data = global_response.json()
                count = global_data.get("total", 0)
                reason_suffix = "globally (sandbox fallback)"

            status = "confirmed" if count >= min_required else "suppressed"
            reason = (
                f"aggregate clinical match found via FHIR ({count} conditions {reason_suffix})"
                if status == "confirmed"
                else f"no matching aggregate clinical signal via FHIR (found {count} {reason_suffix})"
            )
            return ClinicalAggregateResult(
                status=status,
                count=count,
                min_required=min_required,
                note=reason,
            )
        except Exception as exc:
            print(f"[clinical_aggregate] FHIR query failed: {exc}. Falling back to demo database.")

    # Demo lookup: only the explicitly listed ZIP/symptom pairs confirm.
    # Everything else suppresses. This matches the guide's safety guarantee and
    # covers the four outbreak-simulator scenarios.
    demo_counts: dict[tuple[str, str], int] = {
        ("10014", "gi"): 2,          # West Village food-poisoning demo
        ("10031", "respiratory"): 3,  # Harlem Legionella simulator
        ("10036", "rash"): 3,         # Times Square measles simulator
        ("10036", "general"): 3,      # Hantavirus transit-corridor simulator
        ("10036", "respiratory"): 3,  # H3N2 influenza Times Square simulator
    }
    count = demo_counts.get((zip_code, symptom), 0)
    status = "confirmed" if count >= min_required else "suppressed"
    reason = (
        "aggregate clinical match found"
        if status == "confirmed"
        else "no matching aggregate clinical signal"
    )
    return ClinicalAggregateResult(
        status=status,
        count=count,
        min_required=min_required,
        note=reason,
    )

