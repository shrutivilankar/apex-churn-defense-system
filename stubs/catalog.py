"""Fake TMF620 Product Catalog server for local runs and tests.

Run with: uv run uvicorn stubs.catalog:app --port 9005
Base URL: http://127.0.0.1:9005/tmf-api/productCatalogManagement/v5
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Stub Catalog - TMF620 Product Catalog")

PRODUCT_OFFERINGS = [
    {
        "@type": "ProductOffering",
        "id": "off-0001",
        "href": "/tmf-api/productCatalogManagement/v5/productOffering/off-0001",
        "name": "Overage Shield 5 GB",
        "description": "5 GB bonus data to absorb an overage bill",
        "version": "1.0",
        "lifecycleStatus": "active",
        "isSellable": True,
        "isBundle": False,
        "validFor": {
            "startDateTime": "2026-01-01T00:00:00Z",
            "endDateTime": "2027-12-31T23:59:59Z",
        },
        "category": [
            {
                "@type": "CategoryRef",
                "@referredType": "Category",
                "id": "cat-retention",
                "name": "Retention",
            }
        ],
        "productOfferingPrice": [
            {
                "@type": "ProductOfferingPriceRef",
                "@referredType": "ProductOfferingPrice",
                "id": "pop-0001",
                "name": "5 GB bonus data",
                "version": "1.0",
            }
        ],
    },
    {
        "@type": "ProductOffering",
        "id": "off-0002",
        "href": "/tmf-api/productCatalogManagement/v5/productOffering/off-0002",
        "name": "Loyalty 10 GB Bonus",
        "description": "10 GB bonus data for loyalty retention",
        "version": "2.0",
        "lifecycleStatus": "active",
        "isSellable": True,
        "isBundle": False,
        "category": [
            {
                "@type": "CategoryRef",
                "@referredType": "Category",
                "id": "cat-promotion",
                "name": "Promotion",
            }
        ],
    },
    {
        "@type": "ProductOffering",
        "id": "off-0003",
        "href": "/tmf-api/productCatalogManagement/v5/productOffering/off-0003",
        "name": "Home + Mobile Bundle",
        "description": "Bundle of home internet and mobile plans",
        "version": "1.0",
        "lifecycleStatus": "active",
        "isSellable": False,
        "isBundle": True,
    },
    {
        "@type": "ProductOffering",
        "id": "off-0004",
        "href": "/tmf-api/productCatalogManagement/v5/productOffering/off-0004",
        "name": "Legacy Unlimited",
        "description": "Retired plan without a sellable flag",
        "version": "0.9",
        "lifecycleStatus": "retired",
    },
]


@app.get("/tmf-api/productCatalogManagement/v5/productOffering")
def list_product_offering(
    offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)
):
    page = PRODUCT_OFFERINGS[offset : offset + limit]
    return JSONResponse(
        content=page,
        headers={
            "X-Total-Count": str(len(PRODUCT_OFFERINGS)),
            "X-Result-Count": str(len(page)),
        },
    )
