"""Auction ORM model."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Integer, Numeric, ForeignKey, CheckConstraint, Index, text,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.bid import Bid
    from app.models.transaction import Transaction


class AuctionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    LOCKED = "locked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Auction(TimestampMixin, Base):
    __tablename__ = "auctions"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_auctions_ends_after_starts"),
        CheckConstraint("current_price >= starting_price", name="ck_auctions_current_gte_starting"),
        CheckConstraint("starting_price > 0", name="ck_auctions_starting_price_positive"),
        Index("ix_auctions_status_ends_at", "status", "ends_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    starting_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reserve_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bid_increment: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("1.00")
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=AuctionStatus.PENDING.value,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    total_bids: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    seller: Mapped["User"] = relationship(
        "User", back_populates="auctions", foreign_keys=[seller_id]
    )
    winner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[winner_id])
    bids: Mapped[List["Bid"]] = relationship("Bid", back_populates="auction")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="auction")

    def __repr__(self) -> str:
        return f"<Auction {self.title} [{self.status}]>"
