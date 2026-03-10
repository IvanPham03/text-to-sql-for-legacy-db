from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.column_description import ColumnDescription
    from ivanpham_chatbot_assistant.db.models.table import Table


class Column(Base):
    """Stores table columns."""

    __tablename__ = "columns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(255), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, default=False)
    ordinal_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_values: Mapped[list | None] = mapped_column(JSON, nullable=True)
    distinct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sync_checksum: Mapped[str | None] = mapped_column(String, nullable=True)
    null_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    table: Mapped[Table] = relationship(back_populates="columns")
    column_description: Mapped[ColumnDescription] = relationship(
        back_populates="column", uselist=False, cascade="all, delete-orphan"
    )
