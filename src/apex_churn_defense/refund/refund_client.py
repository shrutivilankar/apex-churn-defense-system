"""TMF676 Refund create client (billing system, consumed)."""
import httpx
from pydantic import ValidationError

from apex_churn_defense.payment.payment_client import billing_base_url
from apex_churn_defense.refund.refund_models import Refund, RefundCreate

REFUND_PATH = "/payment/v4/refund"
_DEFAULT_TIMEOUT = 5.0


class RefundClient:
    _base_url = billing_base_url()
    _transport: httpx.AsyncBaseTransport | None = None
    _timeout = _DEFAULT_TIMEOUT

    async def create_refund(self, refund: RefundCreate) -> Refund:
        """Submit a refund to the billing system and return the performed refund."""
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                resp = await client.post(
                    f"{self._base_url}{REFUND_PATH}",
                    json=refund.model_dump(by_alias=True, exclude_none=True),
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(502, "Billing system unavailable", str(exc)) from exc

        if resp.status_code != 201:
            raise UpstreamError(502, "Billing system error", _upstream_message(resp))

        try:
            return Refund.model_validate(resp.json())
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
