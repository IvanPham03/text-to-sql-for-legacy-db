from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationResponse[T](BaseModel):
    """
    Standardized pagination response model wrapper.
    """

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
