"""Fake competitor pricing server for local runs and tests.

Run with: uv run uvicorn stubs.competitor_pricing:app --port 9004
Base URL: http://127.0.0.1:9004/competitor/v1
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Stub Competitor Pricing")

OFFERS = [
    {
        "id": "offer-0001",
        "competitor": "NorthTel",
        "name": "20 GB plan",
        "description": "20 GB data with unlimited Canada-wide talk and text",
        "price": {"unit": "CAD", "value": 45.0},
        "billingPeriod": "month",
        "discounts": [
            {
                "percentage": 20.0,
                "description": "20% off for the first 3 months",
            }
        ],
        "validFor": {
            "startDateTime": "2026-01-01T00:00:00Z",
            "endDateTime": "2027-12-31T23:59:59Z",
        },
    },
    {
        "id": "offer-0002",
        "competitor": "NorthTel",
        "name": "50 GB plan",
        "description": "50 GB data with unlimited talk and text",
        "price": {"unit": "CAD", "value": 65.0},
        "billingPeriod": "month",
        "discounts": [
            {
                "amount": {"unit": "CAD", "value": 10.0},
                "description": "Online-only monthly credit",
            }
        ],
        "validFor": {
            "startDateTime": "2026-03-01T00:00:00Z",
            "endDateTime": "2027-06-30T23:59:59Z",
        },
    },
    {
        "id": "offer-0003",
        "competitor": "Maple Mobile",
        "name": "Unlimited plan",
        "description": "Unlimited data, talk and text",
        "price": {"unit": "CAD", "value": 70.0},
        "billingPeriod": "month",
    },
    {
        "id": "offer-0004",
        "competitor": "Maple Mobile",
        "name": "Holiday 10 GB promo",
        "description": "Seasonal promotion, no longer available",
        "price": {"unit": "CAD", "value": 35.0},
        "billingPeriod": "month",
        "discounts": [
            {
                "percentage": 50.0,
                "description": "Half price for 6 months",
            }
        ],
        "validFor": {
            "startDateTime": "2025-11-01T00:00:00Z",
            "endDateTime": "2025-12-31T23:59:59Z",
        },
    },
]


@app.get("/competitor/v1/offers")
def list_offers(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    page = OFFERS[offset : offset + limit]
    return JSONResponse(
        content={"totalCount": len(OFFERS), "items": page},
        headers={"X-Result-Count": str(len(page))},
    )
