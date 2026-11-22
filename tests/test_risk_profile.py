"""Functional tests for subscriber risk profiling - internal package."""
import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from apex_churn_defense.models.trouble_ticket_models import PartyRef, RelatedParty, TroubleTicket
from apex_churn_defense.payment.payment_client import PaymentClient
from apex_churn_defense.product_usage.product_usage_client import ProductUsageClient
from apex_churn_defense.risk.risk_profile_service import evaluate_risk_profile
from apex_churn_defense.usage.usage_client import UsageConsumptionClient
from stubs.billing import app as billing_stub
from stubs.charging import app as charging_stub
from stubs.usage_history import app as usage_history_stub

NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)


def _clients():
    payment = PaymentClient()
    payment._transport = httpx.ASGITransport(app=billing_stub)
    usage = UsageConsumptionClient()
    usage._transport = httpx.ASGITransport(app=charging_stub)
    product = ProductUsageClient()
    product._transport = httpx.ASGITransport(app=usage_history_stub)
    return payment, usage, product


def _ticket(ticket_id, party_id, severity, created):
    return TroubleTicket(
        id=ticket_id,
        href=f"/tmf-api/troubleTicket/v5/troubleTicket/{ticket_id}",
        description="Bill grievance",
        severity=severity,
        ticketType="Bill Dispute",
        relatedParty=[
            RelatedParty(role="customer", partyOrPartyRole=PartyRef(id=party_id))
        ],
        creationDate=created,
    )


def test_risk_profile_happy_path():
    payment, usage, product = _clients()
    tickets = [
        _ticket("t-1", "sub-123", "Critical", datetime(2026, 11, 1, tzinfo=timezone.utc)),
        _ticket("t-2", "sub-123", "Minor", datetime(2026, 10, 1, tzinfo=timezone.utc)),
        _ticket("t-3", "sub-999", "Critical", datetime(2026, 11, 1, tzinfo=timezone.utc)),
        _ticket("t-4", "sub-123", "Critical", datetime(2026, 1, 1, tzinfo=timezone.utc)),
    ]

    profile = asyncio.run(
        evaluate_risk_profile(
            "sub-123",
            now=NOW,
            payment_client=payment,
            usage_client=usage,
            product_usage_client=product,
            tickets=tickets,
        )
    )

    assert profile.failed_payments_90d == 1
    assert profile.tenure_months == 2
    assert profile.total_revenue.unit == "CAD"
    assert profile.total_revenue.value == pytest.approx(102.6)
    assert profile.avg_monthly_revenue.value == pytest.approx(51.3)
    assert profile.usage_trend_pct == pytest.approx((8.2 - 6.0) / 6.0)
    assert profile.bucket_remaining_pct == pytest.approx(1.8 / 10.0)
    assert profile.usage_events_30d == 3
    assert profile.usage_events_prev_30d == 0
    assert profile.usage_event_trend_pct is None
    assert profile.failed_usage_events == 1
    assert profile.grievance_count_90d == 2
    assert profile.grievance_max_severity == "critical"
    assert profile.data_gaps == []
    assert profile.sources == {
        "tmf676_payment": "ok",
        "tmf677_usage": "ok",
        "tmf635_product_usage": "ok",
        "tmf621_trouble_ticket": "ok",
    }


def test_risk_profile_degrades_when_payment_upstream_fails():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"code": "ERR500", "reason": "billing exploded"})

    payment = PaymentClient()
    payment._transport = httpx.MockTransport(failing)
    _, usage, product = _clients()

    profile = asyncio.run(
        evaluate_risk_profile(
            "sub-123",
            now=NOW,
            payment_client=payment,
            usage_client=usage,
            product_usage_client=product,
            tickets=[],
        )
    )

    assert profile.failed_payments_90d == 0
    assert profile.tenure_months == 0
    assert profile.total_revenue.value == 0.0
    assert profile.sources["tmf676_payment"] == "unavailable"
    assert "tmf676_payment" in profile.data_gaps
    assert profile.sources["tmf677_usage"] == "ok"
    assert profile.usage_events_30d == 3
