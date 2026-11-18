"""Fake TMF677 Usage Consumption server (charging system) for local runs and tests.

Run with: uv run uvicorn stubs.charging:app --port 9002
Base URL: http://127.0.0.1:9002/tmf-api/usageConsumption/v5
"""
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Stub Charging - TMF677 Usage Consumption")

REPORTS = [
    {
        "id": "ucr-0001",
        "href": "/tmf-api/usageConsumption/v5/usageConsumptionReport/ucr-0001",
        "name": "November usage report",
        "description": "Current balances and consumption for subscriber 123",
        "creationDate": "2026-11-10T08:00:00Z",
        "lastUpdate": "2026-11-10T08:00:00Z",
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {
                    "id": "sub-123",
                    "name": "Subscriber 123",
                    "@referredType": "Party",
                },
            }
        ],
        "bucket": [
            {
                "id": "bkt-data-123",
                "name": "Main offer - data",
                "usageType": "data",
                "isShared": False,
                "remainingValue": {"amount": 1.8, "units": "GB"},
                "remainingValueName": "1.8 GB remaining",
                "validFor": {
                    "startDateTime": "2026-11-01T00:00:00Z",
                    "endDateTime": "2026-11-30T23:59:59Z",
                },
                "bucketCounter": [
                    {
                        "counterType": "used",
                        "level": "global",
                        "value": {"amount": 8.2, "units": "GB"},
                        "valueName": "8.2 GB used",
                        "consumptionPeriod": {
                            "startDateTime": "2026-11-01T00:00:00Z",
                            "endDateTime": "2026-11-10T08:00:00Z",
                        },
                        "user": {
                            "role": "user",
                            "partyOrPartyRole": {
                                "id": "sub-123",
                                "name": "Subscriber 123",
                                "@referredType": "Individual",
                            },
                        },
                    }
                ],
            },
            {
                "id": "bkt-voice-123",
                "name": "Main offer - voice",
                "usageType": "voice",
                "isShared": False,
                "remainingValue": {"amount": 60, "units": "min"},
                "bucketCounter": [
                    {
                        "counterType": "used",
                        "level": "global",
                        "value": {"amount": 40, "units": "min"},
                    }
                ],
            },
        ],
        "product": [
            {
                "id": "prod-data-10",
                "name": "10 GB data plan",
                "consumptionSummary": [
                    {
                        "counterType": "outOfBucket",
                        "level": "global",
                        "value": {"amount": 20, "units": "CAD"},
                    }
                ],
            }
        ],
    },
    {
        "id": "ucr-0002",
        "href": "/tmf-api/usageConsumption/v5/usageConsumptionReport/ucr-0002",
        "name": "October usage report",
        "creationDate": "2026-10-10T08:00:00Z",
        "bucket": [
            {
                "id": "bkt-data-oct-123",
                "name": "Main offer - data",
                "usageType": "data",
                "remainingValue": {"amount": 4.0, "units": "GB"},
                "relatedParty": [
                    {
                        "role": "customer",
                        "partyOrPartyRole": {
                            "id": "sub-123",
                            "name": "Subscriber 123",
                            "@referredType": "Party",
                        },
                    }
                ],
                "bucketCounter": [
                    {
                        "counterType": "used",
                        "level": "global",
                        "value": {"amount": 6.0, "units": "GB"},
                    }
                ],
            }
        ],
    },
    {
        "id": "ucr-0003",
        "href": "/tmf-api/usageConsumption/v5/usageConsumptionReport/ucr-0003",
        "name": "November usage report for subscriber 999",
        "creationDate": "2026-11-12T08:00:00Z",
        "bucket": [
            {
                "id": "bkt-sms-999",
                "name": "Main offer - sms",
                "usageType": "sms",
                "remainingValue": {"amount": 95, "units": "sms"},
                "bucketCounter": [
                    {
                        "counterType": "used",
                        "level": "global",
                        "value": {"amount": 5, "units": "sms"},
                        "user": {
                            "role": "user",
                            "partyOrPartyRole": {
                                "id": "sub-999",
                                "name": "Subscriber 999",
                                "@referredType": "Individual",
                            },
                        },
                    }
                ],
            }
        ],
    },
]


def _party_ids(report: dict) -> set[str]:
    ids = {rp["partyOrPartyRole"]["id"] for rp in report.get("relatedParty", [])}
    for bucket in report.get("bucket", []):
        ids.update(rp["partyOrPartyRole"]["id"] for rp in bucket.get("relatedParty", []))
        ids.update(
            counter["user"]["partyOrPartyRole"]["id"]
            for counter in bucket.get("bucketCounter", [])
            if counter.get("user")
        )
    return ids


def _requested_party_ids(body: dict) -> set[str]:
    ids: set[str] = set()
    for related in body.get("relatedParty", []):
        if related.get("id"):
            ids.add(related["id"])
        party = related.get("partyOrPartyRole") or {}
        if party.get("id"):
            ids.add(party["id"])
    return ids


@app.post("/tmf-api/usageConsumption/v5/queryUsageConsumption", status_code=201)
def create_query_usage_consumption(body: dict):
    requested = _requested_party_ids(body)
    if not requested:
        return JSONResponse(
            status_code=400,
            content={
                "code": "ERR400",
                "reason": "Invalid input",
                "message": "relatedParty with a party id is required",
                "status": "400",
            },
        )

    query_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=201,
        content={
            "id": query_id,
            "href": f"/tmf-api/usageConsumption/v5/queryUsageConsumption/{query_id}",
            "state": "done",
            "creationDate": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "relatedParty": body["relatedParty"],
            "usageConsumption": [
                report for report in REPORTS if _party_ids(report) & requested
            ],
        },
    )
