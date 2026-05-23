# ingestion/models.py

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Symptom = Literal["gi", "respiratory", "neuro", "rash", "general"]
ClinicalStatus = Literal["candidate", "confirmed", "suppressed"]


class OutbreakSignal(BaseModel):
    event_id: str
    run_id: str | None = None
    timestamp: datetime
    zip: str = Field(pattern=r"^\d{5}$")
    symptom: Symptom
    source_type: str
    source_url: str | None = None
    evidence_text: str = Field(max_length=600)
    confidence: float = Field(ge=0, le=1)
    synthetic: bool = False


class AlertPackage(BaseModel):
    alert_id: str
    run_id: str
    created_at: datetime
    zip: str
    symptom: Symptom
    recent_count: int
    baseline_avg: float
    baseline_stddev: float
    z_score: float
    clinical_status: ClinicalStatus
    clinical_aggregate_count: int
    source_count: int
    source_diversity: int
    source_urls: list[str]
    decision_reason: str
    datadog_trace_id: str | None = None
    senso_url: str | None = None
    payment_status: str = "unpaid"
