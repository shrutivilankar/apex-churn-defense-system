"""Functional tests for internal competitor pricing enrichment - Package 1.5."""
import asyncio

import httpx
import pytest

from src.competitor.competitor_client import CompetitorPricingClient, UpstreamError
from src.competitor.competitor_service import get_competitor_offers
from stubs.competitor_pricing import app as competitor_stub


def _client(
    transport: httpx.AsyncBaseTransport | None = None,
) -> CompetitorPricingClient:
    client = CompetitorPricingClient()
    client._transport = transport or httpx.ASGITransport(app=competitor_stub)
    return client


def test_competitor_offers_happy_path():
    collection = asyncio.run(get_competitor_offers(client=_client()))

    assert collection.totalCount == 3
    items = collection.items
    assert [offer.id for offer in items] == ["offer-0001", "offer-0002", "offer-0003"]

    northtel_20gb = items[0]
    assert northtel_20gb.competitor == "NorthTel"
    assert northtel_20gb.name == "20 GB plan"
    assert northtel_20gb.price.unit == "CAD"
    assert northtel_20gb.price.value == 45.0
    assert northtel_20gb.billingPeriod == "month"
    assert northtel_20gb.discounts[0].percentage == 20.0
    assert northtel_20gb.discounts[0].amount is None

    northtel_50gb = items[1]
    assert northtel_50gb.discounts[0].amount.unit == "CAD"
    assert northtel_50gb.discounts[0].amount.value == 10.0
    assert northtel_50gb.discounts[0].percentage is None

    unlimited = items[2]
    assert unlimited.competitor == "Maple Mobile"
    assert unlimited.discounts == []
    assert unlimited.validFor is None

    filtered = asyncio.run(
        get_competitor_offers(competitor="maple mobile", client=_client())
    )
    assert filtered.totalCount == 1
    assert filtered.items[0].id == "offer-0003"


def test_competitor_offers_upstream_error_raises():
    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, json={"code": "ERR500", "reason": "competitor feed exploded"}
        )

    client = _client(httpx.MockTransport(failing))

    with pytest.raises(UpstreamError) as excinfo:
        asyncio.run(get_competitor_offers(client=client))

    err = excinfo.value
    assert err.status_code == 502
    assert err.reason == "Competitor pricing system error"
    assert err.message == "competitor feed exploded"
