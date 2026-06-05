"""Shared model mixins for timestamp columns."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True
    )
