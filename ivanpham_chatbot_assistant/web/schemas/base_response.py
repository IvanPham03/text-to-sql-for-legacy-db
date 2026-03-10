from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

from .error_response import ErrorDetail

# Generic type for the data payload
T = TypeVar("T")


class BaseResponse[T](BaseModel):
    """
    Standardized API response format for all endpoints.
    """

    success: bool
    message: str
    data: T | None = None
    error: ErrorDetail | None = None
    meta: dict[str, Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)
