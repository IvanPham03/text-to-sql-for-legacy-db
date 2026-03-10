from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginationResponse(BaseModel, Generic[T]):
    """
    Standardized pagination response model wrapper.
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
