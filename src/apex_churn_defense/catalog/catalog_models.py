"""Pydantic models for TMF620 Product Catalog (consumed, Package 1.6)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntityRef(BaseModel):
    """TMF620 EntityRef - only id is required."""

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")

    model_config = {"populate_by_name": True}


class TimePeriod(BaseModel):
    startDateTime: Optional[datetime] = None
    endDateTime: Optional[datetime] = None


class ProductOffering(BaseModel):
    """TMF620 ProductOffering_RES - required: id, href."""

    id: str
    href: str
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    lifecycleStatus: Optional[str] = None
    isSellable: Optional[bool] = None
    isBundle: Optional[bool] = None
    validFor: Optional[TimePeriod] = None
    category: list[EntityRef] = Field(default_factory=list)
    productOfferingPrice: list[EntityRef] = Field(default_factory=list)


class ProductOfferingCollection(BaseModel):
    totalCount: int
    items: list[ProductOffering]
