"""Pydantic models for TMF621 Trouble Ticket (exposed, Package 1.1)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TicketStatus = Literal[
    "acknowledged",
    "rejected",
    "pending",
    "held",
    "inProgress",
    "cancelled",
    "closed",
    "resolved",
]


class PartyRef(BaseModel):
    id: str
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class RelatedParty(BaseModel):
    role: str
    party_or_party_role: PartyRef = Field(..., alias="partyOrPartyRole")

    model_config = {"populate_by_name": True}


class TroubleTicketCreate(BaseModel):
    """Required: description, severity, ticketType. relatedParty required by this system."""

    description: str
    severity: str
    ticketType: str
    name: Optional[str] = None
    priority: Optional[str] = None
    relatedParty: list[RelatedParty] = Field(..., min_length=1)


class TroubleTicket(BaseModel):
    """TroubleTicket_RES: id and href are required in the response."""

    id: str
    href: str
    description: str
    severity: str
    ticketType: str
    name: Optional[str] = None
    priority: Optional[str] = None
    relatedParty: list[RelatedParty]
    status: Optional[TicketStatus] = None
    creationDate: Optional[datetime] = None
    lastUpdate: Optional[datetime] = None
    statusChangeDate: Optional[datetime] = None

    model_config = {"populate_by_name": True}
