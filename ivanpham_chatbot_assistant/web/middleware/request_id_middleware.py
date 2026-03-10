import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to assign a unique request ID to every incoming request.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in request state for internal use
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Attach to response
        response.headers["X-Request-ID"] = request_id
        return response
