from typing import Any, Generic, TypeVar
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    """
    Standardized error detail model.
    """
    code: str
    details: str
