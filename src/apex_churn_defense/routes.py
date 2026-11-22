import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from apex_churn_defense.models.trouble_ticket_models import TroubleTicket, TroubleTicketCreate
from apex_churn_defense.store import ticket_store
from apex_churn_defense.workflow import run_churn_defence_workflow, LLMResponse
import structlog

BASE_PATH = "/tmf-api/troubleTicket/v5"

router = APIRouter(tags=["troubleTicket"])
log = structlog.get_logger()

@router.post(
    "/troubleTicket",
    response_model=LLMResponse,
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

    response = await run_churn_defence_workflow(ticket)
    recommendation = response.get("structured_response") if response else None
    if recommendation is None:
        log.warning("Workflow returned no recommendation", ticket_id=ticket.id)
        raise HTTPException(
            status_code=502, detail="Workflow produced no recommendation"
        )

    log.info("LLM recommendations", recommendation=recommendation)
    return recommendation
