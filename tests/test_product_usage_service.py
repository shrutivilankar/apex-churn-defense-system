"""Functional tests for internal product usage history enrichment - Package 1.4."""
import asyncio

import httpx
import pytest

from apex_churn_defense.product_usage.product_usage_client import ProductUsageClient, UpstreamError
from apex_churn_defense.product_usage.product_usage_service import get_usage_history
from stubs.usage_history import app as usage_history_stub


def _client(transport: httpx.AsyncBaseTransport | None = None) -> ProductUsageClient:
    client = ProductUsageClient()
    client._transport = transport or httpx.ASGITransport(app=usage_history_stub)
    return client


def test_usage_history_happy_path():
    collection = asyncio.run(
        get_usage_history("sub-123", limit=2, client=_client())
    )

    assert collection.totalCount == 3
    items = collection.items
    assert [usage.id for usage in items] == ["pu-0001", "pu-0002"]

    voice = items[0]
    assert voice.status == "rated"
    assert voice.usageType == "InternationalVoice"
    assert voice.usageCharacteristic[0].value == "GB"
    assert voice.usageCharacteristic[1].value == 300
    assert voice.relatedParty[0].partyOrPartyRole.id == "sub-123"
    assert voice.product.id == "prod-voice-123"
    assert voice.usageSpecification.version == "2.5"
    assert voice.usageProductPrice[0].price.dutyFreeAmount.unit == "CAD"
    assert voice.usageProductPrice[0].price.dutyFreeAmount.value == 2.5

    data_session = items[1]
    assert data_session.usageType == "DataSession"
    assert data_session.usageCharacteristic[0].value == 8.2
    assert data_session.serviceUsage == []


def test_usage_history_upstream_error_raises():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, json={"code": "ERR500", "reason": "Internal Error in usage history system"}
        )

    client = _client(httpx.MockTransport(failing))

    with pytest.raises(UpstreamError) as excinfo:
        asyncio.run(get_usage_history("sub-123", client=client))

    err = excinfo.value
    assert err.status_code == 502
    assert err.reason == "Usage history system error"
    assert err.message == "Internal Error in usage history system"
