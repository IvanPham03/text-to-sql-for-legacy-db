from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ivanpham_chatbot_assistant.db.base import Base

if TYPE_CHECKING:
    from ivanpham_chatbot_assistant.db.models.database import Database
    from ivanpham_chatbot_assistant.db.models.table import Table


class Schema(Base):
    """Represents a database schema."""

    __tablename__ = "schemas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("databases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    database: Mapped[Database] = relationship(back_populates="schemas")
    tables: Mapped[list[Table]] = relationship(
        back_populates="schema", cascade="all, delete-orphan"
    )
