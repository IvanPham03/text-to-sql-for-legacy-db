from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.column import Column


class ColumnDescription(Base):
    """Stores semantic information about columns."""

    __tablename__ = "column_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    examples: Mapped[str | None] = mapped_column(String, nullable=True)
    business_meaning: Mapped[str | None] = mapped_column(String, nullable=True)

    column: Mapped[Column] = relationship(back_populates="column_description")
