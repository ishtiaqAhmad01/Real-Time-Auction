"""Transaction ORM model."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Numeric, ForeignKey, Index, text,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.auction import Auction
    from app.models.user import User


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_reference", "reference_number", unique=True),
        Index("ix_transactions_buyer_status", "buyer_id", "status"),
        Index("ix_transactions_seller_status", "seller_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    auction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auctions.id"), nullable=False
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TransactionStatus.PENDING.value,
        nullable=False,
    )
    reference_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Relationships
    auction: Mapped["Auction"] = relationship("Auction", back_populates="transactions")
    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])

    def __repr__(self) -> str:
        return f"<Transaction {self.reference_number} [{self.status}]>"
