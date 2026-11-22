"""Functional tests for internal sellable offer lookup - Package 1.6."""
import asyncio

import httpx
import pytest

from apex_churn_defense.catalog.catalog_client import CatalogClient, UpstreamError
from apex_churn_defense.catalog.catalog_service import get_sellable_offers
from stubs.catalog import app as catalog_stub


def _client(transport: httpx.AsyncBaseTransport | None = None) -> CatalogClient:
    client = CatalogClient()
    client._transport = transport or httpx.ASGITransport(app=catalog_stub)
    return client


def test_sellable_offers_happy_path():
    collection = asyncio.run(get_sellable_offers(client=_client()))

    assert collection.totalCount == 2
    items = collection.items
    assert [offer.id for offer in items] == ["off-0001", "off-0002"]

    overage_shield = items[0]
    assert overage_shield.name == "Overage Shield 5 GB"
    assert overage_shield.isSellable is True
    assert overage_shield.isBundle is False
    assert overage_shield.category[0].id == "cat-retention"
    assert overage_shield.productOfferingPrice[0].id == "pop-0001"
    assert overage_shield.validFor.endDateTime is not None

    loyalty_bonus = items[1]
    assert loyalty_bonus.name == "Loyalty 10 GB Bonus"
    assert loyalty_bonus.version == "2.0"
    assert loyalty_bonus.productOfferingPrice == []


def test_sellable_offers_upstream_error_raises():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, json={"code": "ERR500", "reason": "catalog service exploded"}
        )

    client = _client(httpx.MockTransport(failing))

    with pytest.raises(UpstreamError) as excinfo:
        asyncio.run(get_sellable_offers(client=client))

    err = excinfo.value
    assert err.status_code == 502
    assert err.reason == "Product catalog system error"
    assert err.message == "catalog service exploded"
