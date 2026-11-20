"""Deterministic rubric applied to a subscriber risk profile."""
from src.risk.risk_models import RiskScore, SubscriberRiskProfile


def score_risk_profile(profile: SubscriberRiskProfile) -> RiskScore:
    """Apply the churn/value rubric and return a scored profile."""
    churn_rules: dict[str, int] = {}

    if profile.failed_payments_90d > 0:
        churn_rules["failed_payment"] = 3

    if profile.grievance_count_90d >= 2:
        churn_rules["repeat_grievance"] = min(
            2 * (profile.grievance_count_90d - 1), 4
        )

    severity_points = {
        "critical": 3,
        "major": 2,
        "minor": 1,
    }
    if profile.grievance_max_severity in severity_points:
        churn_rules["grievance_severity"] = severity_points[
            profile.grievance_max_severity
        ]

    if profile.usage_trend_pct is not None and profile.usage_trend_pct < -0.20:
        churn_rules["usage_trend"] = 2

    if (
        profile.bucket_remaining_pct is not None
        and profile.bucket_remaining_pct < 0.10
    ):
        churn_rules["bucket_balance"] = 1

    if (
        profile.usage_event_trend_pct is not None
        and profile.usage_event_trend_pct < -0.50
    ):
        churn_rules["usage_event_trend"] = 1

    if profile.failed_usage_events > 0:
        churn_rules["failed_usage_event"] = 1

    value_rules: dict[str, int] = {}

    if profile.tenure_months > 24:
        value_rules["tenure"] = 3
    elif profile.tenure_months > 12:
        value_rules["tenure"] = 2
    elif profile.tenure_months > 6:
        value_rules["tenure"] = 1

    avg_revenue = profile.avg_monthly_revenue.value
    if avg_revenue > 60:
        value_rules["avg_monthly_revenue"] = 3
    elif avg_revenue > 30:
        value_rules["avg_monthly_revenue"] = 2
    elif avg_revenue > 15:
        value_rules["avg_monthly_revenue"] = 1

    churn_risk = min(10, 1 + sum(churn_rules.values()))
    subscriber_value = min(10, 1 + sum(value_rules.values()))
    priority = churn_risk * subscriber_value

    if priority > 50:
        action_tier = "aggressive"
    elif priority >= 25:
        action_tier = "moderate"
    else:
        action_tier = "standard"

    unavailable = sum(
        1 for status in profile.sources.values() if status == "unavailable"
    )
    if unavailable == 0:
        confidence = "high"
    elif unavailable == 1:
        confidence = "medium"
    else:
        confidence = "low"

    rubric_breakdown = {
        **{f"churn.{name}": points for name, points in churn_rules.items()},
        **{f"value.{name}": points for name, points in value_rules.items()},
    }

    return RiskScore(
        churn_risk=churn_risk,
        subscriber_value=subscriber_value,
        priority=priority,
        action_tier=action_tier,
        confidence=confidence,
        rubric_breakdown=rubric_breakdown,
    )
