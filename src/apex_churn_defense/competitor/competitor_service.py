"""Internal competitor pricing enrichment (Package 1.5).

Current competitor offers are read from the competitor pricing system and
consumed by the churn workflow; they are not exposed as an inbound API.
"""
from datetime import datetime, timezone

from apex_churn_defense.competitor.competitor_client import CompetitorPricingClient
from apex_churn_defense.competitor.competitor_models import (
    CompetitorOffer,
    CompetitorOfferCollection,
)


async def get_competitor_offers(
    competitor: str | None = None,
    offset: int = 0,
    limit: int = 10,
    client: CompetitorPricingClient | None = None,
) -> CompetitorOfferCollection:
    """Current competitor offers, optionally narrowed to one competitor.

    An offer without a validity window is treated as current; expired and
    not-yet-started offers are dropped.
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    pricing_client = client or CompetitorPricingClient()
    offers = await pricing_client.list_offers()

    now = datetime.now(timezone.utc)
    matches = [offer for offer in offers if _is_current(offer, now)]
    if competitor:
        wanted = competitor.casefold()
        matches = [o for o in matches if o.competitor.casefold() == wanted]

    return CompetitorOfferCollection(
        totalCount=len(matches), items=matches[offset : offset + limit]
    )


def _is_current(offer: CompetitorOffer, now: datetime) -> bool:
    valid_for = offer.validFor
    if valid_for is None:
        return True
    start = _as_utc(valid_for.startDateTime)
    end = _as_utc(valid_for.endDateTime)
    if start is not None and now < start:
        return False
    if end is not None and now > end:
        return False
    return True


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
