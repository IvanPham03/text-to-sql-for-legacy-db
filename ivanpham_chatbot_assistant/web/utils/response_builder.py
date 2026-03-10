import uuid
from datetime import UTC, datetime
from typing import Any

from ivanpham_chatbot_assistant.web.schemas.base_response import BaseResponse
from ivanpham_chatbot_assistant.web.schemas.error_response import ErrorDetail


def _generate_meta() -> dict[str, Any]:
    """Generate default metadata for responses."""
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def success_response(
    data: Any | None = None,
    message: str = "Success",
    meta: dict[str, Any] | None = None,
) -> BaseResponse[Any]:
    """
    Construct a successful API response.

    :param data: The payload data.
    :param message: A success message.
    :param meta: Additional metadata.
    :return: BaseResponse instance for a success.
    """
    response_meta = _generate_meta()
    if meta:
        response_meta.update(meta)

    return BaseResponse(
        success=True, message=message, data=data, error=None, meta=response_meta
    )


def error_response(
    message: str = "An error occurred",
    error_code: str = "INTERNAL_SERVER_ERROR",
    details: str = "",
    meta: dict[str, Any] | None = None,
) -> BaseResponse[Any]:
    """
    Construct an error API response.

    :param message: A high-level error message.
    :param error_code: A specific error code identifier.
    :param details: Detailed description of the error.
    :param meta: Additional metadata.
    :return: BaseResponse instance for an error.
    """
    response_meta = _generate_meta()
    if meta:
        response_meta.update(meta)

    return BaseResponse(
        success=False,
        message=message,
        data=None,
        error=ErrorDetail(code=error_code, details=details),
        meta=response_meta,
    )
