"""In-memory refund proposal store - dict keyed by proposal UUID."""
from src.refund.refund_models import RefundProposal

refund_proposal_store: dict[str, RefundProposal] = {}
