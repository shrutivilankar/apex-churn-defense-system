import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from src.models.trouble_ticket_models import TroubleTicket, TroubleTicketCreate
from src.store import ticket_store

BASE_PATH = "/tmf-api/troubleTicket/v5"

router = APIRouter(tags=["troubleTicket"])


@router.post(
    "/troubleTicket",
    response_model=TroubleTicket,
    response_model_exclude_none=True,
    status_code=201,
)
async def create_trouble_ticket(body: TroubleTicketCreate):
    now = datetime.now(timezone.utc)
    ticket_id = str(uuid.uuid4())
    ticket = TroubleTicket(
        id=ticket_id,
        href=f"{BASE_PATH}/troubleTicket/{ticket_id}",
        description=body.description,
        severity=body.severity,
        ticketType=body.ticketType,
        name=body.name,
        priority=body.priority,
        relatedParty=body.relatedParty,
        status="acknowledged",
        creationDate=now,
        lastUpdate=now,
        statusChangeDate=now,
    )
    ticket_store[ticket_id] = ticket



    return ticket
