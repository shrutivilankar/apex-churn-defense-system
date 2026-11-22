"""Pydantic models for competitor pricing (consumed, Package 1.5).

No TMF contract covers competitor pricing, so the offer shape below is
project-defined. It reuses the project-wide money and collection conventions.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Money(BaseModel):
    """Project-wide money shape shared with TMF676/TMF635."""

    unit: str
    value: float


class TimePeriod(BaseModel):
    startDateTime: Optional[datetime] = None
    endDateTime: Optional[datetime] = None


class Discount(BaseModel):
    """A percentage or fixed-amount discount; exactly one must be set."""

    percentage: Optional[float] = None
    amount: Optional[Money] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_kind(self):
        if (self.percentage is None) == (self.amount is None):
            raise ValueError("discount requires exactly one of percentage or amount")
        return self


class CompetitorOffer(BaseModel):
    """A competitor's current offer - required: id, competitor, name, price."""

    id: str
    competitor: str
    name: str
    price: Money
    billingPeriod: Optional[str] = None
    description: Optional[str] = None
    discounts: list[Discount] = Field(default_factory=list)
    validFor: Optional[TimePeriod] = None


class CompetitorOfferCollection(BaseModel):
    totalCount: int
    items: list[CompetitorOffer]
