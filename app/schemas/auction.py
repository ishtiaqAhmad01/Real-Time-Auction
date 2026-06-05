"""Auction Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AuctionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    starting_price: Decimal
    reserve_price: Optional[Decimal] = None
    bid_increment: Decimal = Decimal("1.00")
    starts_at: datetime
    ends_at: datetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError("Title must be at least 5 characters")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters")
        return v

    @field_validator("starting_price")
    @classmethod
    def validate_starting_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Starting price must be greater than 0")
        if abs(v.as_tuple().exponent) > 2:
            raise ValueError("Starting price must have at most 2 decimal places")
        return v

    @field_validator("bid_increment")
    @classmethod
    def validate_bid_increment(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Bid increment must be greater than 0")
        return v

    @field_validator("reserve_price")
    @classmethod
    def validate_reserve_price(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("Reserve price must be greater than 0")
        return v

    @field_validator("ends_at")
    @classmethod
    def validate_ends_at(cls, v: datetime, info) -> datetime:
        starts = info.data.get("starts_at")
        if starts and v <= starts:
            raise ValueError("End time must be after start time")
        return v


class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 5:
                raise ValueError("Title must be at least 5 characters")
            if len(v) > 200:
                raise ValueError("Title must be at most 200 characters")
        return v


class AuctionResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    seller_id: UUID
    starting_price: Decimal
    current_price: Decimal
    bid_increment: Decimal
    status: str
    starts_at: datetime
    ends_at: datetime
    winner_id: Optional[UUID] = None
    total_bids: int
    created_at: datetime
    # NOTE: reserve_price is NEVER included (hidden reserve)
    model_config = ConfigDict(from_attributes=True)


class AuctionListResponse(BaseModel):
    items: List[AuctionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
