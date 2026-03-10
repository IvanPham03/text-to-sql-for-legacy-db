from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """
    Request payload for Natural Language to SQL query.
    """

    question: str = Field(description="Natural language question to query.")


class AskResponseData(BaseModel):
    """
    Data payload for an ask question response.
    """

    sql: str | None = None
    columns: list[str] | None = None
    rows: list[list[Any]] | None = None
    answer: str
    row_count: int = 0
    latency: float | None = Field(
        default=None, description="Pipeline execution latency in seconds."
    )


class QueryHistoryItem(BaseModel):
    """
    Summary representation of a past query.
    """

    question: str
    sql: str
    timestamp: datetime


class QueryDetailResponseData(BaseModel):
    """
    Data payload for a single query detail.
    """

    question: str
    sql: str
    result_rows: list[list[Any]]
