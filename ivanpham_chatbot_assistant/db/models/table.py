from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.column import Column
    from ivanpham_chatbot_assistant.db.models.schema import Schema
    from ivanpham_chatbot_assistant.db.models.table_description import TableDescription


class Table(Base):
    """Stores tables in a schema."""

    __tablename__ = "tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    schema_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schemas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sync_checksum: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    schema: Mapped[Schema] = relationship(back_populates="tables")
    columns: Mapped[list[Column]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
    table_description: Mapped[TableDescription] = relationship(
        back_populates="table", uselist=False, cascade="all, delete-orphan"
    )
