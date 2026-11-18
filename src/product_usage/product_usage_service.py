"""Internal product usage history enrichment (TMF635 read, Package 1.4).

Usage history is read from the usage history system and consumed by the churn
workflow; it is not exposed as an inbound API of this service.
"""
from src.product_usage.product_usage_client import ProductUsageClient
from src.product_usage.product_usage_models import (
    ProductUsage,
    ProductUsageCollection,
)


async def get_usage_history(
    party_id: str,
    offset: int = 0,
    limit: int = 10,
    client: ProductUsageClient | None = None,
) -> ProductUsageCollection:
    """Usage events recorded for one party, newest first.

    TMF635 has no required party filter, so the filter is applied after reading.
    """
    if not party_id:
        raise ValueError("party_id is required")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    usage_client = client or ProductUsageClient()
    usages = await usage_client.list_product_usage()

    matches = [usage for usage in usages if _is_for_party(usage, party_id)]
    matches.sort(key=_newest_first, reverse=True)
    return ProductUsageCollection(
        totalCount=len(matches), items=matches[offset : offset + limit]
    )


def _is_for_party(usage: ProductUsage, party_id: str) -> bool:
    for related in usage.relatedParty:
        ref = related.partyOrPartyRole
        if ref is None:
            continue
        if ref.id == party_id or ref.partyId == party_id:
            return True
    return False


def _newest_first(usage: ProductUsage) -> float:
    return usage.creationDate.timestamp() if usage.creationDate else 0.0
