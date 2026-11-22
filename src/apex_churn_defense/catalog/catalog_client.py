"""TMF620 Product Catalog read client (catalog system, consumed)."""
import os

import httpx
from pydantic import ValidationError

from apex_churn_defense.catalog.catalog_models import ProductOffering

PRODUCT_OFFERING_PATH = "/productOffering"
_UPSTREAM_PAGE_SIZE = 100
_DEFAULT_TIMEOUT = 5.0


def catalog_base_url() -> str:
    return os.getenv(
        "CATALOG_BASE_URL",
        "http://127.0.0.1:9005/tmf-api/productCatalogManagement/v5",
    )


class CatalogClient:
    _base_url = catalog_base_url()
    _transport: httpx.AsyncBaseTransport | None = None
    _timeout = _DEFAULT_TIMEOUT

    async def list_product_offerings(self) -> list[ProductOffering]:
        """Read every product offering, page by page.

        Stops at X-Total-Count when the upstream sends it, otherwise on a short page.
        """
        offerings: list[ProductOffering] = []
        offset = 0
        while True:
            page, total = await self._list_page(offset)
            offerings.extend(page)
            if (total is not None and len(offerings) >= total) or (
                len(page) < _UPSTREAM_PAGE_SIZE
            ):
                return offerings
            offset += _UPSTREAM_PAGE_SIZE

    async def _list_page(
        self, offset: int
    ) -> tuple[list[ProductOffering], int | None]:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                resp = await client.get(
                    f"{self._base_url}{PRODUCT_OFFERING_PATH}",
                    params={"offset": offset, "limit": _UPSTREAM_PAGE_SIZE},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                502, "Product catalog system unavailable", str(exc)
            ) from exc

        if resp.status_code != 200:
            raise UpstreamError(
                502, "Product catalog system error", _upstream_message(resp)
            )

        try:
            payload = resp.json()
            total_header = resp.headers.get("X-Total-Count")
            return (
                [ProductOffering.model_validate(item) for item in payload],
                int(total_header) if total_header else None,
            )
        except (ValueError, TypeError, ValidationError) as exc:
            raise UpstreamError(
                502, "Malformed product catalog response", str(exc)
            ) from exc


def _upstream_message(resp: httpx.Response) -> str:
    try:
        return str(resp.json().get("reason") or resp.text)
    except (ValueError, AttributeError):
        return resp.text


class UpstreamError(Exception):
    """Non-2xx or unusable response from the product catalog system."""

    def __init__(self, status_code: int, reason: str, message: str = ""):
        super().__init__(message or reason)
        self.status_code = status_code
        self.reason = reason
        self.message = message
