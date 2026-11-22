"""Deterministic risk profiling and scoring for the churn workflow."""
from datetime import datetime
from typing import Iterable, Optional

from apex_churn_defense.models.trouble_ticket_models import TroubleTicket
from apex_churn_defense.payment.payment_client import PaymentClient
from apex_churn_defense.product_usage.product_usage_client import ProductUsageClient
from apex_churn_defense.risk.risk_models import RiskScore, SubscriberRiskProfile
from apex_churn_defense.risk.risk_profile_service import evaluate_risk_profile
from apex_churn_defense.risk.risk_scoring_service import score_risk_profile
from apex_churn_defense.usage.usage_client import UsageConsumptionClient


async def evaluate_risk(
    party_id: str,
    now: Optional[datetime] = None,
    payment_client: Optional[PaymentClient] = None,
    usage_client: Optional[UsageConsumptionClient] = None,
    product_usage_client: Optional[ProductUsageClient] = None,
    tickets: Optional[Iterable[TroubleTicket]] = None,
) -> tuple[SubscriberRiskProfile, RiskScore]:
    """Build the profile and apply the rubric in one call."""
    profile = await evaluate_risk_profile(
        party_id,
        now=now,
        payment_client=payment_client,
        usage_client=usage_client,
        product_usage_client=product_usage_client,
        tickets=tickets,
    )
    return profile, score_risk_profile(profile)


__all__ = [
    "RiskScore",
    "SubscriberRiskProfile",
    "evaluate_risk",
    "evaluate_risk_profile",
    "score_risk_profile",
]
