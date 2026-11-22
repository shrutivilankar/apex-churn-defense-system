"""Pydantic models for TMF677 Usage Consumption (consumed, Package 1.3)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Quantity(BaseModel):
    """TMF677 Quantity - an amount in a given unit."""

    amount: float
    units: str


class TimePeriod(BaseModel):
    startDateTime: Optional[datetime] = None
    endDateTime: Optional[datetime] = None


class PartyOrPartyRoleRef(BaseModel):
    """TMF677 PartyRef / PartyRoleRef - both only require id."""

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    partyId: Optional[str] = None
    partyName: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class RelatedParty(BaseModel):
    role: Optional[str] = None
    party_or_party_role: Optional[PartyOrPartyRoleRef] = Field(
        None, alias="partyOrPartyRole"
    )

    model_config = {"populate_by_name": True}


class PartyAccountRef(BaseModel):
    id: str
    href: Optional[str] = None
    name: Optional[str] = None


class ProductRef(BaseModel):
    id: str
    href: Optional[str] = None
    name: Optional[str] = None


class BucketCounter(BaseModel):
    """A consumption counter, or a ConsumptionSummary when nested in product."""

    id: Optional[str] = None
    href: Optional[str] = None
    counterType: Optional[str] = None
    level: Optional[str] = None
    user: Optional[RelatedParty] = None
    value: Optional[Quantity] = None
    valueName: Optional[str] = None
    consumptionPeriod: Optional[TimePeriod] = None


class Bucket(BaseModel):
    """A bucket tracks remaining balance and its consumption counters."""

    id: Optional[str] = None
    href: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    usageType: Optional[str] = None
    isShared: Optional[bool] = None
    remainingValue: Optional[Quantity] = None
    remainingValueName: Optional[str] = None
    validFor: Optional[TimePeriod] = None
    relatedParty: list[RelatedParty] = Field(default_factory=list)
    bucketCounter: list[BucketCounter] = Field(default_factory=list)


class UsageConsumptionProductRef(ProductRef):
    consumptionSummary: list[BucketCounter] = Field(default_factory=list)


class UsageConsumptionReport(BaseModel):
    """TMF677 UsageConsumptionReport_RES - required: id, href."""

    id: str
    href: str
    name: Optional[str] = None
    description: Optional[str] = None
    creationDate: Optional[datetime] = None
    lastUpdate: Optional[datetime] = None
    validPeriod: Optional[TimePeriod] = None
    bucket: list[Bucket] = Field(default_factory=list)
    relatedParty: list[RelatedParty] = Field(default_factory=list)
    partyAccount: list[PartyAccountRef] = Field(default_factory=list)
    product: list[UsageConsumptionProductRef] = Field(default_factory=list)


class QueryUsageConsumptionCreate(BaseModel):
    """TMF677 QueryUsageConsumption_FVO - request at least one relatedParty."""

    relatedParty: list[RelatedParty] = Field(..., min_length=1)


class QueryUsageConsumption(BaseModel):
    """TMF677 QueryUsageConsumption_RES - required: id, href."""

    id: str
    href: str
    state: Optional[str] = None
    creationDate: Optional[datetime] = None
    usageConsumption: list[UsageConsumptionReport] = Field(default_factory=list)
    relatedParty: list[RelatedParty] = Field(default_factory=list)
    partyAccount: list[PartyAccountRef] = Field(default_factory=list)


class UsageConsumptionCollection(BaseModel):
    totalCount: int
    items: list[UsageConsumptionReport]
