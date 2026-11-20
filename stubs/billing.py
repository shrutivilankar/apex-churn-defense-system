"""Fake TMF676 Payment server (billing system) for local runs and tests.

Run with: uv run uvicorn stubs.billing:app --port 9001
"""
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Stub Billing - TMF676 Payment")

PAYMENTS = [
    {
        "id": "pay-0001",
        "href": "/payment/v4/payment/pay-0001",
        "description": "September access and data bill",
        "paymentDate": "2026-09-05T10:00:00Z",
        "status": "captured",
        "account": {"id": "acc-123", "name": "Subscriber 123"},
        "amount": {"unit": "CAD", "value": 45.0},
        "totalAmount": {"unit": "CAD", "value": 51.3},
        "payer": {"id": "sub-123", "role": "customer", "@referredType": "Party"},
        "paymentMethod": {
            "id": "pm-visa-4242",
            "name": "Visa ending 4242",
            "@referredType": "PaymentMethod",
        },
        "paymentItem": [
            {
                "id": "pi-0001",
                "item": {"id": "inv-0001"},
                "amount": {"unit": "CAD", "value": 45.0},
            }
        ],
    },
    {
        "id": "pay-0002",
        "href": "/payment/v4/payment/pay-0002",
        "description": "October access and data bill",
        "paymentDate": "2026-10-05T10:00:00Z",
        "status": "captured",
        "account": {"id": "acc-123", "name": "Subscriber 123"},
        "amount": {"unit": "CAD", "value": 45.0},
        "totalAmount": {"unit": "CAD", "value": 51.3},
        "payer": {"id": "sub-123", "role": "customer", "@referredType": "Party"},
        "paymentMethod": {
            "id": "pm-visa-4242",
            "name": "Visa ending 4242",
            "@referredType": "PaymentMethod",
        },
        "paymentItem": [
            {
                "id": "pi-0002",
                "item": {"id": "inv-0002"},
                "amount": {"unit": "CAD", "value": 45.0},
            }
        ],
    },
    {
        "id": "pay-0003",
        "href": "/payment/v4/payment/pay-0003",
        "description": "November access and data bill",
        "paymentDate": "2026-11-05T10:00:00Z",
        "status": "failed",
        "account": {"id": "acc-123", "name": "Subscriber 123"},
        "amount": {"unit": "CAD", "value": 45.0},
        "totalAmount": {"unit": "CAD", "value": 51.3},
        "payer": {"id": "sub-123", "role": "customer", "@referredType": "Party"},
        "paymentMethod": {
            "id": "pm-visa-4242",
            "name": "Visa ending 4242",
            "@referredType": "PaymentMethod",
        },
        "paymentItem": [
            {
                "id": "pi-0003",
                "item": {"id": "inv-0003"},
                "amount": {"unit": "CAD", "value": 45.0},
            }
        ],
    },
    {
        "id": "pay-0004",
        "href": "/payment/v4/payment/pay-0004",
        "description": "October access bill",
        "paymentDate": "2026-10-06T09:30:00Z",
        "status": "captured",
        "account": {"id": "acc-999", "name": "Subscriber 999"},
        "amount": {"unit": "CAD", "value": 30.0},
        "totalAmount": {"unit": "CAD", "value": 34.2},
        "payer": {"id": "sub-999", "role": "customer", "@referredType": "Party"},
        "paymentMethod": {
            "id": "pm-mc-1111",
            "name": "Mastercard ending 1111",
            "@referredType": "PaymentMethod",
        },
    },
]


@app.get("/payment/v4/payment")
def list_payment(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    page = PAYMENTS[offset : offset + limit]
    return JSONResponse(
        content=page,
        headers={
            "X-Total-Count": str(len(PAYMENTS)),
            "X-Result-Count": str(len(page)),
        },
    )


@app.get("/payment/v4/payment/{payment_id}")
def retrieve_payment(payment_id: str):
    for payment in PAYMENTS:
        if payment["id"] == payment_id:
            return payment
    return JSONResponse(
        status_code=404,
        content={
            "code": "ERR404",
            "reason": "Payment not found",
            "message": f"No payment with id {payment_id}",
            "status": "404",
        },
    )


REFUNDS: list[dict] = []


def _error(status_code: int, reason: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": f"ERR{status_code}",
            "reason": reason,
            "message": message,
            "status": str(status_code),
        },
    )


@app.post("/payment/v4/refund", status_code=201)
def create_refund(body: dict):
    missing = [
        field
        for field in ("account", "paymentMethod", "totalAmount")
        if not body.get(field)
    ]
    if missing:
        return _error(
            400, "Invalid input", f"missing required field(s): {', '.join(missing)}"
        )

    total_amount = body["totalAmount"]
    value = total_amount.get("value")
    if not isinstance(value, (int, float)) or value <= 0:
        return _error(400, "Invalid input", "totalAmount.value must be > 0")

    refund_id = f"ref-{len(REFUNDS) + 1:04d}"
    refund = {
        "id": refund_id,
        "href": f"/payment/v4/refund/{refund_id}",
        "account": body["account"],
        "paymentMethod": body["paymentMethod"],
        "totalAmount": total_amount,
        "refundDate": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "done",
    }
    for field in ("amount", "taxAmount", "description", "name", "correlatorId"):
        if body.get(field) is not None:
            refund[field] = body[field]
    REFUNDS.append(refund)
    return refund
