"""Functional tests for internal payment history enrichment — Package 1.2."""
import asyncio

import httpx
import pytest

from src.payment.payment_client import PaymentClient, UpstreamError
from src.payment.payment_service import get_payment_history
from stubs.billing import app as billing_stub


def _client(transport: httpx.AsyncBaseTransport | None = None) -> PaymentClient:
    client = PaymentClient()
    client._transport = transport or httpx.ASGITransport(app=billing_stub)
    return client


def test_payment_history_happy_path():
    collection = asyncio.run(
        get_payment_history("sub-123", limit=2, client=_client())
    )

    assert collection.totalCount == 3
    items = collection.items
    assert len(items) == 2
    assert items[0].id == "pay-0003"
    assert items[0].status == "failed"
    assert items[0].amount.unit == "CAD"
    assert items[0].amount.value == 45.0
    assert items[0].account.id == "acc-123"
    assert items[0].paymentMethod.id == "pm-visa-4242"
    assert items[0].payer.id == "sub-123"
    assert items[0].taxAmount is None


def test_payment_history_upstream_error_raises():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, json={"code": "ERR500", "reason": "billing exploded"}
        )

    client = _client(httpx.MockTransport(failing))

    with pytest.raises(UpstreamError) as excinfo:
        asyncio.run(get_payment_history("sub-123", client=client))

    err = excinfo.value
    assert err.status_code == 502
    assert err.reason == "Billing system error"
    assert err.message == "billing exploded"
