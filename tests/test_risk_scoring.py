"""Rubric tests for deterministic risk scoring - internal package."""
from datetime import datetime, timezone

from apex_churn_defense.payment.payment_models import Money
from apex_churn_defense.risk.risk_models import SubscriberRiskProfile
from apex_churn_defense.risk.risk_scoring_service import score_risk_profile

NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)


def _profile(**overrides):
    values = {
        "party_id": "sub-123",
        "evaluated_at": NOW,
        "total_revenue": Money(unit="CAD", value=0.0),
        "avg_monthly_revenue": Money(unit="CAD", value=0.0),
        "sources": {
            "tmf676_payment": "ok",
            "tmf677_usage": "ok",
            "tmf635_product_usage": "ok",
            "tmf621_trouble_ticket": "ok",
        },
    }
    values.update(overrides)
    return SubscriberRiskProfile(**values)


def test_high_risk_high_value_is_aggressive():
    profile = _profile(
        failed_payments_90d=1,
        grievance_count_90d=3,
        grievance_max_severity="critical",
        usage_trend_pct=-0.30,
        bucket_remaining_pct=0.05,
        usage_event_trend_pct=-0.60,
        failed_usage_events=2,
        tenure_months=30,
        avg_monthly_revenue=Money(unit="CAD", value=80.0),
    )

    score = score_risk_profile(profile)

    assert score.churn_risk == 10
    assert score.subscriber_value == 7
    assert score.priority == 70
    assert score.action_tier == "aggressive"
    assert score.confidence == "high"
    assert score.rubric_breakdown == {
        "churn.failed_payment": 3,
        "churn.repeat_grievance": 4,
        "churn.grievance_severity": 3,
        "churn.usage_trend": 2,
        "churn.bucket_balance": 1,
        "churn.usage_event_trend": 1,
        "churn.failed_usage_event": 1,
        "value.tenure": 3,
        "value.avg_monthly_revenue": 3,
    }


def test_low_risk_low_value_is_standard():
    profile = _profile(
        tenure_months=1,
        avg_monthly_revenue=Money(unit="CAD", value=10.0),
    )

    score = score_risk_profile(profile)

    assert score.churn_risk == 1
    assert score.subscriber_value == 1
    assert score.priority == 1
    assert score.action_tier == "standard"
    assert score.rubric_breakdown == {}


def test_priority_boundary_fifty_is_moderate_and_low_confidence():
    profile = _profile(
        failed_payments_90d=1,
        grievance_count_90d=2,
        grievance_max_severity="critical",
        usage_trend_pct=-0.25,
        tenure_months=18,
        avg_monthly_revenue=Money(unit="CAD", value=40.0),
        sources={
            "tmf676_payment": "unavailable",
            "tmf677_usage": "unavailable",
            "tmf635_product_usage": "ok",
            "tmf621_trouble_ticket": "ok",
        },
    )

    score = score_risk_profile(profile)

    assert score.churn_risk == 10
    assert score.subscriber_value == 5
    assert score.priority == 50
    assert score.action_tier == "moderate"
    assert score.confidence == "low"
