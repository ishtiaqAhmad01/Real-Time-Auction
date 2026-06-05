"""Transaction Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    id: UUID
    auction_id: UUID
    buyer_id: UUID
    seller_id: UUID
    amount: Decimal
    status: str
    reference_number: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: Optional[UUID] = None
    new_value: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # NOTE: old_value and metadata are NOT returned in public API for security
