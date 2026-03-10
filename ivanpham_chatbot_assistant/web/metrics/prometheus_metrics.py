import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from fastapi import APIRouter

# Prometheus Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_latency_seconds = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

http_request_errors_total = Counter(
    "http_request_errors_total",
    "Total number of HTTP request errors",
    ["method", "endpoint", "error_type"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        endpoint = request.url.path
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            http_request_latency_seconds.labels(method=method, endpoint=endpoint).observe(time.perf_counter() - start_time)
            
            return response
            
        except Exception as exc:
            http_request_errors_total.labels(method=method, endpoint=endpoint, error_type=type(exc).__name__).inc()
            raise exc

metrics_router = APIRouter()

@metrics_router.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
