from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.schema import Schema


class Database(Base):
    """Stores database instances that are indexed."""

    __tablename__ = "databases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    db_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. postgres, mysql
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    schemas: Mapped[list[Schema]] = relationship(
        back_populates="database", cascade="all, delete-orphan"
    )
