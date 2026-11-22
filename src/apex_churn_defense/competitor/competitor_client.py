"""Competitor pricing read client (competitor pricing system, consumed)."""
import os

import httpx
from pydantic import ValidationError

from apex_churn_defense.competitor.competitor_models import CompetitorOffer

OFFERS_PATH = "/offers"
_UPSTREAM_PAGE_SIZE = 100
_DEFAULT_TIMEOUT = 5.0


def competitor_base_url() -> str:
    return os.getenv("COMPETITOR_BASE_URL", "http://127.0.0.1:9004/competitor/v1")


class CompetitorPricingClient:
    _base_url = competitor_base_url()
    _transport: httpx.AsyncBaseTransport | None = None
    _timeout = _DEFAULT_TIMEOUT

    async def list_offers(self) -> list[CompetitorOffer]:
        """Read every competitor offer, page by page.

        Stops at totalCount when the upstream sends it, otherwise on a short page.
        """
        offers: list[CompetitorOffer] = []
        offset = 0
        while True:
            page, total = await self._list_page(offset)
            offers.extend(page)
            if (total is not None and len(offers) >= total) or (
                len(page) < _UPSTREAM_PAGE_SIZE
            ):
                return offers
            offset += _UPSTREAM_PAGE_SIZE

    async def _list_page(
        self, offset: int
    ) -> tuple[list[CompetitorOffer], int | None]:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                resp = await client.get(
                    f"{self._base_url}{OFFERS_PATH}",
                    params={"offset": offset, "limit": _UPSTREAM_PAGE_SIZE},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                502, "Competitor pricing system unavailable", str(exc)
            ) from exc

        if resp.status_code != 200:
            raise UpstreamError(
                502, "Competitor pricing system error", _upstream_message(resp)
            )

        try:
            payload = resp.json()
            total = payload.get("totalCount")
            return (
                [CompetitorOffer.model_validate(item) for item in payload.get("items", [])],
                int(total) if total is not None else None,
            )
        except (ValueError, TypeError, AttributeError, ValidationError) as exc:
            raise UpstreamError(
                502, "Malformed competitor pricing response", str(exc)
            ) from exc


def _upstream_message(resp: httpx.Response) -> str:
    try:
        return str(resp.json().get("reason") or resp.text)
    except (ValueError, AttributeError):
        return resp.text


class UpstreamError(Exception):
    """Non-2xx or unusable response from the competitor pricing system."""

    def __init__(self, status_code: int, reason: str, message: str = ""):
        super().__init__(message or reason)
        self.status_code = status_code
        self.reason = reason
        self.message = message
