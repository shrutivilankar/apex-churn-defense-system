"""Functional tests for TMF621 POST /troubleTicket — Package 1.1."""
import uuid

import pytest
from fastapi.testclient import TestClient

from apex_churn_defense.main import app
from apex_churn_defense.store import ticket_store

BASE = "/tmf-api/troubleTicket/v5"
client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_store():
    ticket_store.clear()
    yield
    ticket_store.clear()


def _payload():
    return {
        "description": "Overcharged for data usage",
        "severity": "Major",
        "ticketType": "Bill Dispute",
        "name": "Overage complaint",
        "relatedParty": [
            {
                "role": "customer",
                "partyOrPartyRole": {"id": "sub-123", "@referredType": "Party"},
            }
        ],
    }


def test_create_ticket_happy_path():
    resp = client.post(f"{BASE}/troubleTicket", json=_payload())

    assert resp.status_code == 201
    body = resp.json()
    uuid.UUID(body["id"])
    assert body["href"] == f"{BASE}/troubleTicket/{body['id']}"
    assert body["status"] == "acknowledged"
    assert body["name"] == "Overage complaint"
    assert body["relatedParty"][0]["partyOrPartyRole"]["id"] == "sub-123"
    assert body["creationDate"]
    assert body["lastUpdate"]
    assert body["statusChangeDate"]
    assert body["ticketType"] == "Bill Dispute"
    assert "resolutionDate" not in body


def test_create_ticket_missing_severity_returns_tmf_400():
    payload = _payload()
    del payload["severity"]

    resp = client.post(f"{BASE}/troubleTicket", json=payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "ERR400"
    assert body["reason"] == "Invalid input"
    assert body["status"] == "400"
    assert "severity" in body["message"]
