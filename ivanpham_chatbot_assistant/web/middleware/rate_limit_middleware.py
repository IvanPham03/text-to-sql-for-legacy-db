from fastapi import FastAPI
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from ivanpham_chatbot_assistant.web.utils.response_builder import error_response

# Initialize the rate limiter with a default 100 requests per minute
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    Custom handler for RateLimitExceeded returning BaseResponse format.
    """
    standard_response = error_response(
        message="Rate limit exceeded",
        error_code="RATE_LIMIT_EXCEEDED",
        details=str(exc),
    )
    return JSONResponse(status_code=429, content=standard_response.model_dump())


def setup_rate_limiter(app: FastAPI) -> None:
    """Register rate limiter and exception handler."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
