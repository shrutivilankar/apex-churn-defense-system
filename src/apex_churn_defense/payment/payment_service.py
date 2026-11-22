"""Internal payment-history enrichment (TMF676 read, Package 1.2).

Payment history is read from the billing system and consumed by the churn
workflow; it is not exposed as an inbound API of this service.
"""
from apex_churn_defense.payment.payment_client import PaymentClient
from apex_churn_defense.payment.payment_models import Payment, PaymentCollection


def _newest_first(payment: Payment) -> float:
    return payment.paymentDate.timestamp() if payment.paymentDate else 0.0


async def get_payment_history(
    party_id: str,
    offset: int = 0,
    limit: int = 10,
    client: PaymentClient | None = None,
) -> PaymentCollection:
    """Payments paid by one party, newest first.

    TMF676 has no party filter, so the filter is applied after reading payments.
    """
    if not party_id:
        raise ValueError("party_id is required")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    payment_client = client or PaymentClient()
    payments = await payment_client.list_payments()

    matches = [p for p in payments if p.payer is not None and p.payer.id == party_id]
    matches.sort(key=_newest_first, reverse=True)
    return PaymentCollection(
        totalCount=len(matches), items=matches[offset : offset + limit]
    )
