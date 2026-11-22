"""TMF676 Payment read client (billing system, consumed)."""
import os

import httpx
from pydantic import ValidationError

from apex_churn_defense.payment.payment_models import Payment

PAYMENT_PATH = ""
_UPSTREAM_PAGE_SIZE = 100
_DEFAULT_TIMEOUT = 5.0


def billing_base_url() -> str:
    return os.getenv("BILLING_BASE_URL", "http://127.0.0.1:9001")


class PaymentClient:
    _base_url = billing_base_url()
    _transport: httpx.AsyncBaseTransport | None = None
    _timeout = _DEFAULT_TIMEOUT

    async def list_payments(self) -> list[Payment]:
        """Read every payment from the billing system, page by page.

        Stops at X-Total-Count when billing sends it, otherwise on a short page.
        """
        payments: list[Payment] = []
        offset = 0
        while True:
            page, total = await self._list_page(offset)
            payments.extend(page)
            if (total is not None and len(payments) >= total) or (len(page) < _UPSTREAM_PAGE_SIZE):
                return payments
            offset += _UPSTREAM_PAGE_SIZE

    """ Invoke Billing Payment API to get the list of payments.
    """
    async def _list_page(self, offset: int) -> tuple[list[Payment], int | None]:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                resp = await client.get(
                    f"{self._base_url}/payment/v4/payment",
                    params={"offset": offset, "limit": _UPSTREAM_PAGE_SIZE},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(502, "Billing system unavailable", str(exc)) from exc

        if resp.status_code != 200:
            raise UpstreamError(502, "Billing system error", _upstream_message(resp))

        try:
            payload = resp.json()
            total_header = resp.headers.get("X-Total-Count")
            return (
                [Payment.model_validate(item) for item in payload],
                int(total_header) if total_header else None,
            )
        except (ValueError, TypeError, ValidationError) as exc:
            raise UpstreamError(502, "Malformed billing response", str(exc)) from exc


def _upstream_message(resp: httpx.Response) -> str:
    try:
        return str(resp.json().get("reason") or resp.text)
    except (ValueError, AttributeError):
        return resp.text


class UpstreamError(Exception):
    """Non-2xx or unusable response from the billing system."""

    def __init__(self, status_code: int, reason: str, message: str = ""):
        super().__init__(message or reason)
        self.status_code = status_code
        self.reason = reason
        self.message = message
