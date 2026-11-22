"""Pydantic models for TMF635 Product Usage (consumed, Package 1.4)."""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ProductUsageStatus = Literal[    
    "rated",
    "unrated",
    "failed",
]


class Money(BaseModel):
    """TMF635 Money - the project-wide money shape."""

    unit: str
    value: float


class EntityRef(BaseModel):
    """TMF635 EntityRef - only id is required."""

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class PartyOrPartyRoleRef(EntityRef):
    """TMF635 PartyRef / PartyRoleRef - both only require id."""

    partyId: Optional[str] = None
    partyName: Optional[str] = None
    type: Optional[str] = Field(None, alias="@type")

    model_config = {"populate_by_name": True}


class RelatedPartyRefOrPartyRoleRef(BaseModel):
    role: Optional[str] = None
    partyOrPartyRole: Optional[PartyOrPartyRoleRef] = None


class Characteristic(BaseModel):
    """A name/value pair; the value type depends on the characteristic."""

    id: Optional[str] = None
    name: Optional[str] = None
    valueType: Optional[str] = None
    value: Optional[Any] = None
    type: Optional[str] = Field(None, alias="@type")

    model_config = {"populate_by_name": True}


class ServiceUsageRef(EntityRef):
    """Reference to a service usage that produced this product usage."""


class ProductRef(EntityRef):
    """Reference to the product the usage was recorded against."""


class ProductUsageSpecificationRef(EntityRef):
    version: Optional[str] = None


class Price(BaseModel):
    dutyFreeAmount: Optional[Money] = None
    percentage: Optional[float] = None
    taxIncludedAmount: Optional[Money] = None
    taxRate: Optional[float] = None


class ProductOfferingPriceRef(EntityRef):
    version: Optional[str] = None


class ProductPrice(BaseModel):
    """Price assigned to a product usage when it is rated."""

    description: Optional[str] = None
    name: Optional[str] = None
    productOfferingPrice: Optional[ProductOfferingPriceRef] = None
    recurringChargePeriod: Optional[str] = None
    unitOfMeasure: Optional[str] = None
    price: Optional[Price] = None
    priceType: Optional[str] = None


class ProductUsage(BaseModel):
    """TMF635 ProductUsage_RES - required: id, href."""

    id: str
    href: str
    creationDate: Optional[datetime] = None
    lastUpdate: Optional[datetime] = None
    status: Optional[ProductUsageStatus] = None
    usageType: Optional[str] = None
    usageCharacteristic: list[Characteristic] = Field(default_factory=list)
    serviceUsage: list[ServiceUsageRef] = Field(default_factory=list)
    relatedParty: list[RelatedPartyRefOrPartyRoleRef] = Field(default_factory=list)
    usageProductPrice: list[ProductPrice] = Field(default_factory=list)
    product: Optional[ProductRef] = None
    usageSpecification: Optional[ProductUsageSpecificationRef] = None


class ProductUsageCollection(BaseModel):
    totalCount: int
    items: list[ProductUsage]
