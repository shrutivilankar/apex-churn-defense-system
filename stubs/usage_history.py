"""Fake TMF635 Product Usage server ("Usage History" system) for local runs and tests.

Run with: uv run uvicorn stubs.usage_history:app --port 9003
Base URL: http://127.0.0.1:9003/tmf-api/productUsageManagement/v5
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Stub UsageHistory - TMF635 Product Usage")

PRODUCT_USAGES = [
    {
        "@type": "ProductUsage",
        "id": "pu-0001",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0001",
        "creationDate": "2026-11-12T14:35:05Z",
        "lastUpdate": "2026-11-12T14:38:00Z",
        "status": "rated",
        "usageType": "InternationalVoice",
        "usageCharacteristic": [
            {"@type": "StringCharacteristic", "name": "destinationCountryCode", "value": "GB"},
            {"@type": "IntegerCharacteristic", "name": "duration", "value": 300},
        ],
        "serviceUsage": [
            {
                "@type": "ServiceUsageRef",
                "@referredType": "ServiceUsage",
                "id": "su-0001",
                "name": "Voice session",
            }
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-123",
                    "name": "Subscriber 123",
                },
            }
        ],
        "usageProductPrice": [
            {
                "@type": "ProductPrice",
                "name": "International voice rate",
                "priceType": "usage",
                "price": {
                    "@type": "Price",
                    "dutyFreeAmount": {"unit": "CAD", "value": 2.5},
                    "taxRate": 13,
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-voice-123",
            "name": "Voice plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-voice",
            "name": "InternationalVoice",
            "version": "2.5",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0002",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0002",
        "creationDate": "2026-11-10T08:00:00Z",
        "status": "rated",
        "usageType": "DataSession",
        "usageCharacteristic": [
            {"@type": "FloatCharacteristic", "name": "volume", "value": 8.2},
            {"@type": "StringCharacteristic", "name": "units", "value": "GB"},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-123",
                    "name": "Subscriber 123",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-data-10",
            "name": "10 GB data plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-data",
            "name": "DataSession",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0003",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0003",
        "creationDate": "2026-11-08T09:15:00Z",
        "status": "unrated",
        "usageType": "Sms",
        "usageCharacteristic": [
            {"@type": "IntegerCharacteristic", "name": "count", "value": 5},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-123",
                    "name": "Subscriber 123",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-sms-123",
            "name": "SMS add-on",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-sms",
            "name": "Sms",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0004",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0004",
        "creationDate": "2026-11-11T11:00:00Z",
        "status": "rated",
        "usageType": "RoamingData",
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-999",
                    "name": "Subscriber 999",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-roam-999",
            "name": "Roaming pass",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-roaming",
            "name": "RoamingData",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0005",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0005",
        "creationDate": "2026-11-10T19:30:00Z",
        "status": "failed",
        "usageType": "DataSession",
        "usageCharacteristic": [
            {"@type": "FloatCharacteristic", "name": "volume", "value": 8.0},
            {"@type": "StringCharacteristic", "name": "units", "value": "GB"},
            {"@type": "StringCharacteristic", "name": "throttleReason", "value": "peakHourPolicy"},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-456",
                    "name": "Subscriber 456",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-premium-456",
            "name": "Premium 10 GB plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-data",
            "name": "DataSession",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0006",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0006",
        "creationDate": "2026-10-18T20:00:00Z",
        "status": "rated",
        "usageType": "DataSession",
        "usageCharacteristic": [
            {"@type": "FloatCharacteristic", "name": "volume", "value": 6.2},
            {"@type": "StringCharacteristic", "name": "units", "value": "GB"},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-456",
                    "name": "Subscriber 456",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-premium-456",
            "name": "Premium 10 GB plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-data",
            "name": "DataSession",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0007",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0007",
        "creationDate": "2026-10-05T19:15:00Z",
        "status": "rated",
        "usageType": "DataSession",
        "usageCharacteristic": [
            {"@type": "FloatCharacteristic", "name": "volume", "value": 7.4},
            {"@type": "StringCharacteristic", "name": "units", "value": "GB"},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-456",
                    "name": "Subscriber 456",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-premium-456",
            "name": "Premium 10 GB plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-data",
            "name": "DataSession",
            "version": "1.0",
        },
    },
    {
        "@type": "ProductUsage",
        "id": "pu-0008",
        "href": "/tmf-api/productUsageManagement/v5/productUsage/pu-0008",
        "creationDate": "2026-09-28T21:00:00Z",
        "status": "rated",
        "usageType": "DataSession",
        "usageCharacteristic": [
            {"@type": "FloatCharacteristic", "name": "volume", "value": 5.8},
            {"@type": "StringCharacteristic", "name": "units", "value": "GB"},
        ],
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "@referredType": "Party",
                    "id": "sub-456",
                    "name": "Subscriber 456",
                },
            }
        ],
        "product": {
            "@type": "ProductRef",
            "@referredType": "Product",
            "id": "prod-premium-456",
            "name": "Premium 10 GB plan",
        },
        "usageSpecification": {
            "@type": "ProductUsageSpecificationRef",
            "@referredType": "ProductUsageSpecification",
            "id": "pus-data",
            "name": "DataSession",
            "version": "1.0",
        },
    },
]


@app.get("/tmf-api/productUsageManagement/v5/productUsage")
def list_product_usage(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    page = PRODUCT_USAGES[offset : offset + limit]
    return JSONResponse(
        content=page,
        headers={
            "X-Total-Count": str(len(PRODUCT_USAGES)),
            "X-Result-Count": str(len(page)),
        },
    )
