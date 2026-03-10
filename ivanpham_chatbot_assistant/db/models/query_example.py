from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ivanpham_chatbot_assistant.db.base import Base


class QueryExample(Base):
    """Stores example natural language -> SQL pairs for training RAG."""

    __tablename__ = "query_examples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("databases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    question: Mapped[str] = mapped_column(String, nullable=False)
    sql_query: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Could link back to Database if necessary, but skipping
    # for now to match Table requests
