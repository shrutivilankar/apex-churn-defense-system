"""Internal sellable offer lookup (TMF620 read, Package 1.6).

Sellable offers are read from the product catalog system and consumed by the
churn workflow; they are not exposed as an inbound API of this service.
"""
from apex_churn_defense.catalog.catalog_client import CatalogClient
from apex_churn_defense.catalog.catalog_models import (
    ProductOffering,
    ProductOfferingCollection,
)


async def get_sellable_offers(
    offset: int = 0,
    limit: int = 10,
    client: CatalogClient | None = None,
) -> ProductOfferingCollection:
    """Product offerings that can be sold stand-alone (isSellable is true).

    TMF620 has no required sellable filter, so the filter is applied after reading.
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    catalog_client = client or CatalogClient()
    offerings = await catalog_client.list_product_offerings()

    sellable: list[ProductOffering] = [
        offering for offering in offerings if offering.isSellable is True
    ]
    return ProductOfferingCollection(
        totalCount=len(sellable), items=sellable[offset : offset + limit]
    )
