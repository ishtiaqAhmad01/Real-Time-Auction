"""Bid ORM model — APPEND-ONLY table."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Numeric, ForeignKey, CheckConstraint, Index, String, text,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.auction import Auction
    from app.models.user import User


class Bid(Base):
    """
    Bid records are APPEND-ONLY — never update or delete rows in this table.
    """
    __tablename__ = "bids"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_bids_amount_positive"),
        Index("ix_bids_auction_id", "auction_id"),
        Index("ix_bids_bidder_id", "bidder_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    auction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auctions.id"), nullable=False
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_winning: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    auction: Mapped["Auction"] = relationship("Auction", back_populates="bids")
    bidder: Mapped["User"] = relationship("User", back_populates="bids")

    def __repr__(self) -> str:
        return f"<Bid {self.amount} on {self.auction_id}>"
