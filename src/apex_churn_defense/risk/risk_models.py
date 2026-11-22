"""Pydantic models for deterministic risk profiling and scoring."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from apex_churn_defense.payment.payment_models import Money

Severity = Literal["critical", "major", "minor"]
ActionTier = Literal["aggressive", "moderate", "standard"]
Confidence = Literal["high", "medium", "low"]
SourceStatus = Literal["ok", "unavailable"]


class SubscriberRiskProfile(BaseModel):
    """Deterministic metrics assembled from TMF676, TMF677, TMF635 and TMF621."""

    party_id: str
    evaluated_at: datetime
    failed_payments_90d: int = 0
    tenure_months: int = 0
    total_revenue: Money
    avg_monthly_revenue: Money
    usage_trend_pct: Optional[float] = None
    bucket_remaining_pct: Optional[float] = None
    usage_events_30d: int = 0
    usage_events_prev_30d: int = 0
    usage_event_trend_pct: Optional[float] = None
    failed_usage_events: int = 0
    grievance_count_90d: int = 0
    grievance_max_severity: Optional[Severity] = None
    sources: dict[str, SourceStatus] = Field(default_factory=dict)
    data_gaps: list[str] = Field(default_factory=list)


class RiskScore(BaseModel):
    """Rubric-derived score and audit trail."""

    churn_risk: int
    subscriber_value: int
    priority: int
    action_tier: ActionTier
    confidence: Confidence
    rubric_breakdown: dict[str, int] = Field(default_factory=dict)
