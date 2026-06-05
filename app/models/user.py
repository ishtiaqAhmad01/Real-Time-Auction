"""User ORM model."""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.auction import Auction
    from app.models.bid import Bid


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    auctions: Mapped[List["Auction"]] = relationship(
        "Auction", back_populates="seller", foreign_keys="Auction.seller_id"
    )
    bids: Mapped[List["Bid"]] = relationship("Bid", back_populates="bidder")

    def __repr__(self) -> str:
        return f"<User {self.username}>"
