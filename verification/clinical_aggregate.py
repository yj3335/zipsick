# verification/clinical_aggregate.py
# Aggregate-only clinical verifier.
# In production this adapter runs inside a secure clinical environment.
# For the MVP, it uses a fixed demo table that proves the safety contract:
#   - 10014/gi returns aggregate count=2 (confirmed)
#   - all other ZIP/symptom pairs return count=0 (suppressed)

from dataclasses import dataclass


@dataclass
class ClinicalAggregateResult:
    status: str           # "confirmed" | "suppressed"
    count: int            # aggregate clinical presentations (never individual records)
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
    # Demo lookup: simulates a real aggregate query into an anonymised clinical DB.
    demo_counts: dict[tuple[str, str], int] = {
        ("10014", "gi"): 2,
    }
    count = demo_counts.get((zip_code, symptom), 0)
    min_required = 2
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
