"""Functional tests for internal usage/balance enrichment - Package 1.3."""
import asyncio

import httpx
import pytest

from apex_churn_defense.usage.usage_client import UpstreamError, UsageConsumptionClient
from apex_churn_defense.usage.usage_service import get_usage_consumption
from stubs.charging import app as charging_stub


def _client(transport: httpx.AsyncBaseTransport | None = None) -> UsageConsumptionClient:
    client = UsageConsumptionClient()
    client._transport = transport or httpx.ASGITransport(app=charging_stub)
    return client


def test_usage_consumption_happy_path():
    collection = asyncio.run(
        get_usage_consumption("sub-123", limit=2, client=_client())
    )

    assert collection.totalCount == 2
    items = collection.items
    assert [report.id for report in items] == ["ucr-0001", "ucr-0002"]

    latest = items[0]
    data_bucket = latest.bucket[0]
    assert data_bucket.usageType == "data"
    assert data_bucket.remainingValue.amount == 1.8
    assert data_bucket.remainingValue.units == "GB"
    assert data_bucket.bucketCounter[0].value.amount == 8.2
    assert data_bucket.bucketCounter[0].value.units == "GB"
    assert data_bucket.bucketCounter[0].user.party_or_party_role.id == "sub-123"
    assert latest.bucket[1].remainingValue.units == "min"
    assert latest.partyAccount == []

    older = items[1]
    assert older.bucket[0].remainingValue.amount == 4.0
    assert older.bucket[0].relatedParty[0].party_or_party_role.id == "sub-123"


def test_usage_consumption_upstream_error_raises():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, json={"code": "ERR500", "reason": "charging exploded"}
        )

    client = _client(httpx.MockTransport(failing))

    with pytest.raises(UpstreamError) as excinfo:
        asyncio.run(get_usage_consumption("sub-123", client=client))

    err = excinfo.value
    assert err.status_code == 502
    assert err.reason == "Charging system error"
    assert err.message == "charging exploded"
