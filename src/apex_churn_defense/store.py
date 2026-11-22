"""In-memory ticket store — dict keyed by ticket UUID."""
from apex_churn_defense.models.trouble_ticket_models import TroubleTicket

ticket_store: dict[str, TroubleTicket] = {}
