"""Internal refund tool backed by TMF676 (Package 1.5).

Refunds are monetary actions: ``request_refund`` only records an advisory
proposal, and nothing is sent to the billing system until a human calls
``approve_refund`` and ``execute_approved_refund``. No inbound API is exposed.
"""
import uuid
from datetime import datetime, timezone

from apex_churn_defense.payment.payment_models import AccountRef, Money, PaymentMethodRef
from apex_churn_defense.refund.refund_client import RefundClient
from apex_churn_defense.refund.refund_models import RefundCreate, RefundProposal
from apex_churn_defense.refund.refund_store import refund_proposal_store


class RefundProposalNotFound(Exception):
    """No proposal exists for the given id."""


class RefundApprovalRequired(Exception):
    """Execution was attempted before a human approved the refund."""


class RefundStateError(Exception):
    """The proposal is not in a state that allows the requested action."""


def request_refund(
    account: AccountRef,
    payment_method: PaymentMethodRef,
    total_amount: Money,
    amount: Money | None = None,
    tax_amount: Money | None = None,
    description: str | None = None,
    correlator_id: str | None = None,
) -> RefundProposal:
    """Record a proposed refund for human review; does not call billing."""
    _validate_amounts(total_amount, amount, tax_amount)

    proposal = RefundProposal(
        id=str(uuid.uuid4()),
        status="pendingApproval",
        refundRequest=RefundCreate(
            account=account,
            paymentMethod=payment_method,
            totalAmount=total_amount,
            amount=amount,
            taxAmount=tax_amount,
            description=description,
            correlatorId=correlator_id,
        ),
        creationDate=datetime.now(timezone.utc),
    )
    refund_proposal_store[proposal.id] = proposal
    return proposal


def approve_refund(proposal_id: str, approved_by: str) -> RefundProposal:
    """Record a human approval; ``approved_by`` identifies the approver."""
    if not approved_by:
        raise ValueError("approved_by is required")

    proposal = _get_proposal(proposal_id)
    if proposal.status != "pendingApproval":
        raise RefundStateError(
            f"refund proposal {proposal_id} is {proposal.status}, not pendingApproval"
        )

    proposal.status = "approved"
    proposal.approvedBy = approved_by
    proposal.approvalDate = datetime.now(timezone.utc)
    return proposal


async def execute_approved_refund(
    proposal_id: str, client: RefundClient | None = None
) -> RefundProposal:
    """Send an approved refund to the billing system (TMF676 createRefund)."""
    proposal = _get_proposal(proposal_id)
    if proposal.status == "pendingApproval":
        raise RefundApprovalRequired(
            f"refund proposal {proposal_id} requires human approval before execution"
        )
    if proposal.status == "executed":
        raise RefundStateError(f"refund proposal {proposal_id} was already executed")

    refund_client = client or RefundClient()
    proposal.refund = await refund_client.create_refund(proposal.refundRequest)
    proposal.status = "executed"
    return proposal


def _get_proposal(proposal_id: str) -> RefundProposal:
    try:
        return refund_proposal_store[proposal_id]
    except KeyError as exc:
        raise RefundProposalNotFound(
            f"no refund proposal with id {proposal_id}"
        ) from exc


def _validate_amounts(
    total_amount: Money, amount: Money | None, tax_amount: Money | None
) -> None:
    if not total_amount.unit:
        raise ValueError("total_amount.unit is required")
    if total_amount.value <= 0:
        raise ValueError("total_amount.value must be > 0")
    for name, money in (("amount", amount), ("tax_amount", tax_amount)):
        if money is None:
            continue
        if money.value < 0:
            raise ValueError(f"{name}.value must be >= 0")
        if money.unit != total_amount.unit:
            raise ValueError(f"{name}.unit must match total_amount.unit")
