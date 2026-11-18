"""In-memory ticket store — dict keyed by ticket UUID."""
from src.models.trouble_ticket_models import TroubleTicket

ticket_store: dict[str, TroubleTicket] = {}
