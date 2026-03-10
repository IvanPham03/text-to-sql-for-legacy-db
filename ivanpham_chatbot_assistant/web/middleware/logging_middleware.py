import time
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger

class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log API request and response details.
    """
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        
        start_time = time.perf_counter()
        
        logger.info(
            f"Incoming request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip
        )
        
        response = await call_next(request)
        
        process_time_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"Completed request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(process_time_ms, 2)
        )
        
        return response
