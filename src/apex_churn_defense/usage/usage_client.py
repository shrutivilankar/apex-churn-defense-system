"""TMF677 Usage Consumption read client (charging system, consumed)."""
import os

import httpx
from pydantic import ValidationError

from apex_churn_defense.usage.usage_models import (
    PartyOrPartyRoleRef,
    QueryUsageConsumption,
    QueryUsageConsumptionCreate,
    RelatedParty,
)

QUERY_PATH = "/queryUsageConsumption"
_DEFAULT_TIMEOUT = 5.0


def charging_base_url() -> str:
    return os.getenv(
        "CHARGING_BASE_URL", "http://127.0.0.1:9002/tmf-api/usageConsumption/v5"
    )


class UsageConsumptionClient:
    _base_url = charging_base_url()
    _transport: httpx.AsyncBaseTransport | None = None
    _timeout = _DEFAULT_TIMEOUT

    async def query_usage_consumption(
        self, party_id: str
    ) -> QueryUsageConsumption:
        """Ask the charging system for one party's consumption and balances."""
        if not party_id:
            raise ValueError("party_id is required")

        body = QueryUsageConsumptionCreate(
            relatedParty=[
                RelatedParty(
                    role="customer",
                    partyOrPartyRole=PartyOrPartyRoleRef(
                        id=party_id, referred_type="Party"
                    ),
                )
            ]
        )

        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                resp = await client.post(
                    f"{self._base_url}{QUERY_PATH}",
                    json=body.model_dump(by_alias=True, exclude_none=True),
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(502, "Charging system unavailable", str(exc)) from exc

        if resp.status_code != 201:
            raise UpstreamError(502, "Charging system error", _upstream_message(resp))

        try:
            return QueryUsageConsumption.model_validate(resp.json())
        except (ValueError, TypeError, ValidationError) as exc:
            raise UpstreamError(502, "Malformed charging response", str(exc)) from exc


def _upstream_message(resp: httpx.Response) -> str:
    try:
        return str(resp.json().get("reason") or resp.text)
    except (ValueError, AttributeError):
        return resp.text


class UpstreamError(Exception):
    """Non-2xx or unusable response from the charging system."""

    def __init__(self, status_code: int, reason: str, message: str = ""):
        super().__init__(message or reason)
        self.status_code = status_code
        self.reason = reason
        self.message = message
