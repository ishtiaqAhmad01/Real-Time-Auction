"""Bid Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class BidCreate(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Bid amount must be greater than 0")
        return v


class BidResponse(BaseModel):
    id: UUID
    auction_id: UUID
    bidder_id: UUID
    amount: Decimal
    is_winning: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BidListResponse(BaseModel):
    items: List[BidResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
