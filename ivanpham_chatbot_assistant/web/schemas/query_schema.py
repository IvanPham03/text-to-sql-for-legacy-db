from typing import List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AskRequest(BaseModel):
    """
    Request payload for Natural Language to SQL query.
    """
    question: str = Field(description="Natural language question to query.")

class AskResponseData(BaseModel):
    """
    Data payload for an ask question response.
    """
    sql: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    answer: str
    row_count: int = 0
    latency: Optional[float] = Field(default=None, description="Pipeline execution latency in seconds.")

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
    result_rows: List[List[Any]]
