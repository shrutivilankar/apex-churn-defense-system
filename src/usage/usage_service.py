"""Internal usage and balance enrichment (TMF677 read, Package 1.3).

Consumption and remaining balances are queried from the charging system and
consumed by the churn workflow; they are not exposed as an inbound API.
"""
from src.usage.usage_client import UsageConsumptionClient
from src.usage.usage_models import UsageConsumptionCollection, UsageConsumptionReport



async def get_usage_consumption(
    party_id: str,
    offset: int = 0,
    limit: int = 10,
    client: UsageConsumptionClient | None = None,
) -> UsageConsumptionCollection:
    """Consumption and remaining balances of one party, newest report first."""
    if not party_id:
        raise ValueError("party_id is required")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    usage_client = client or UsageConsumptionClient()
    query = await usage_client.query_usage_consumption(party_id)

    reports = sorted(query.usageConsumption, key=_newest_first, reverse=True)
    return UsageConsumptionCollection(
        totalCount=len(reports), items=reports[offset : offset + limit]
    )


def _newest_first(report: UsageConsumptionReport) -> float:
    return report.creationDate.timestamp() if report.creationDate else 0.0
