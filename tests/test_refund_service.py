"""Functional tests for the TMF676-backed refund tool - Package 1.5."""
import asyncio

import httpx
import pytest

from apex_churn_defense.payment.payment_models import AccountRef, Money, PaymentMethodRef
from apex_churn_defense.refund.refund_client import RefundClient
from apex_churn_defense.refund.refund_service import (
    RefundApprovalRequired,
    approve_refund,
    execute_approved_refund,
    request_refund,
)
from stubs.billing import REFUNDS
from stubs.billing import app as billing_stub


def _client(transport: httpx.AsyncBaseTransport | None = None) -> RefundClient:
    client = RefundClient()
    client._transport = transport or httpx.ASGITransport(app=billing_stub)
    return client


def _request():
    return request_refund(
        account=AccountRef(id="acc-123", name="Subscriber 123"),
        payment_method=PaymentMethodRef(id="pm-visa-4242", name="Visa ending 4242"),
        total_amount=Money(unit="CAD", value=51.3),
        amount=Money(unit="CAD", value=45.0),
        tax_amount=Money(unit="CAD", value=6.3),
        description="Refund of overage charges on the November bill",
        correlator_id="tt-0001",
    )


def test_refund_executes_after_human_approval():
    proposal = _request()
    assert proposal.status == "pendingApproval"
    assert proposal.refund is None

    approved = approve_refund(proposal.id, approved_by="supervisor-42")
    assert approved.status == "approved"
    assert approved.approvedBy == "supervisor-42"
    assert approved.approvalDate is not None

    executed = asyncio.run(execute_approved_refund(proposal.id, client=_client()))

    assert executed.status == "executed"
    refund = executed.refund
    assert refund.id.startswith("ref-")
    assert REFUNDS[-1]["id"] == refund.id
    assert refund.status == "done"
    assert refund.href == f"/payment/v4/refund/{refund.id}"
    assert refund.account.id == "acc-123"
    assert refund.paymentMethod.id == "pm-visa-4242"
    assert refund.totalAmount.unit == "CAD"
    assert refund.totalAmount.value == 51.3
    assert refund.amount.value == 45.0
    assert refund.taxAmount.value == 6.3
    assert refund.correlatorId == "tt-0001"
    assert refund.refundDate is not None


def test_refund_without_approval_never_reaches_billing():
    proposal = _request()
    sent_before = len(REFUNDS)

    with pytest.raises(RefundApprovalRequired):
        asyncio.run(execute_approved_refund(proposal.id, client=_client()))

    assert len(REFUNDS) == sent_before
    assert proposal.status == "pendingApproval"
    assert proposal.refund is None
