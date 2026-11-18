"""Pydantic models for TMF676 Payment (consumed, Package 1.2)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Money(BaseModel):
    """TMF676 Money — the project-wide money shape."""

    unit: str
    value: float


class AccountRef(BaseModel):
    id: str
    href: Optional[str] = None
    name: Optional[str] = None


class PaymentMethodRef(BaseModel):
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class PayerRef(BaseModel):
    """TMF676 RelatedParty as used by Payment.payer."""

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class EntityRef(BaseModel):
    id: str
    href: Optional[str] = None


class PaymentItem(BaseModel):
    item: EntityRef
    id: Optional[str] = None
    amount: Optional[Money] = None
    taxAmount: Optional[Money] = None
    totalAmount: Optional[Money] = None


class Payment(BaseModel):
    """TMF676 Payment — required: account, paymentMethod."""

    account: AccountRef
    paymentMethod: PaymentMethodRef
    id: Optional[str] = None
    href: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    paymentDate: Optional[datetime] = None
    status: Optional[str] = None
    amount: Optional[Money] = None
    taxAmount: Optional[Money] = None
    totalAmount: Optional[Money] = None
    payer: Optional[PayerRef] = None
    paymentItem: Optional[list[PaymentItem]] = None

    model_config = {"populate_by_name": True}


class PaymentCollection(BaseModel):
    totalCount: int
    items: list[Payment]
