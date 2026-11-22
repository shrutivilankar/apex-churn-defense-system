"""Functional tests for TMF621 POST /troubleTicket — Package 1.1."""
import pytest
from fastapi.testclient import TestClient

from apex_churn_defense import routes
from apex_churn_defense.main import app
from apex_churn_defense.store import ticket_store
from apex_churn_defense.workflow import LLMResponse

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


def test_create_ticket_happy_path(monkeypatch):
    recommendation = LLMResponse(
        recommended_offers=["OFFER-DATA-50"],
        recommended_refund=[25.0],
        recommendation_description="Apply a one-time credit and offer a larger data plan.",
    )

    async def _fake_workflow(ticket):
        return {"structured_response": recommendation}

    monkeypatch.setattr(routes, "run_churn_defence_workflow", _fake_workflow)

    resp = client.post(f"{BASE}/troubleTicket", json=_payload())

    assert resp.status_code == 201
    assert resp.json() == {
        "recommended_offers": ["OFFER-DATA-50"],
        "recommended_refund": [25.0],
        "recommendation_description": (
            "Apply a one-time credit and offer a larger data plan."
        ),
    }
    assert len(ticket_store) == 1


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
