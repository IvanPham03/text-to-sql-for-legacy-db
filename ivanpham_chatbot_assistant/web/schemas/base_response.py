from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict
from .error_response import ErrorDetail

# Generic type for the data payload
T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """
    Standardized API response format for all endpoints.
    """
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: Dict[str, Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)
