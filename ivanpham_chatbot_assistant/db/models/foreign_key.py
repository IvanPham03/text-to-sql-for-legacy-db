from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey as SAForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.column import Column
    from ivanpham_chatbot_assistant.db.models.table import Table


class ForeignKey(Base):
    """Stores foreign key relationships."""

    __tablename__ = "foreign_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source_table_id: Mapped[uuid.UUID] = mapped_column(
        SAForeignKey("tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_column_id: Mapped[uuid.UUID] = mapped_column(
        SAForeignKey("columns.id", ondelete="CASCADE"), nullable=False, index=True
    )

    target_table_id: Mapped[uuid.UUID] = mapped_column(
        SAForeignKey("tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_column_id: Mapped[uuid.UUID] = mapped_column(
        SAForeignKey("columns.id", ondelete="CASCADE"), nullable=False, index=True
    )

    constraint_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships to source and target columns can be established if desired, but
    # we'll keep it simple for now as requested.
    source_table: Mapped[Table] = relationship("Table", foreign_keys=[source_table_id])
    target_table: Mapped[Table] = relationship("Table", foreign_keys=[target_table_id])
    source_column: Mapped[Column] = relationship(
        "Column", foreign_keys=[source_column_id]
    )
    target_column: Mapped[Column] = relationship(
        "Column", foreign_keys=[target_column_id]
    )
