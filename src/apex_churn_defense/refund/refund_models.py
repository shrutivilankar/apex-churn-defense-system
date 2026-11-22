"""Pydantic models for TMF676 Refund (consumed, Package 1.5)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from apex_churn_defense.payment.payment_models import AccountRef, Money, PaymentMethodRef


class PaymentRef(BaseModel):
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class RefundCreate(BaseModel):
    """TMF676 Refund_Create - required: account, paymentMethod, totalAmount."""

    account: AccountRef
    paymentMethod: PaymentMethodRef
    totalAmount: Money
    amount: Optional[Money] = None
    taxAmount: Optional[Money] = None
    description: Optional[str] = None
    name: Optional[str] = None
    correlatorId: Optional[str] = None
    refundDate: Optional[datetime] = None
    payment: Optional[PaymentRef] = None

    model_config = {"populate_by_name": True}


class Refund(BaseModel):
    """TMF676 Refund_RES - required: account, paymentMethod."""

    account: AccountRef
    paymentMethod: PaymentMethodRef
    id: Optional[str] = None
    href: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    correlatorId: Optional[str] = None
    refundDate: Optional[datetime] = None
    status: Optional[str] = None
    statusDate: Optional[datetime] = None
    amount: Optional[Money] = None
    taxAmount: Optional[Money] = None
    totalAmount: Optional[Money] = None
    payment: Optional[PaymentRef] = None

    model_config = {"populate_by_name": True}


class RefundProposal(BaseModel):
    """Advisory refund awaiting human approval; never sent upstream unapproved."""

    id: str
    status: Literal["pendingApproval", "approved", "executed"]
    refundRequest: RefundCreate
    creationDate: datetime
    approvedBy: Optional[str] = None
    approvalDate: Optional[datetime] = None
    refund: Optional[Refund] = None
