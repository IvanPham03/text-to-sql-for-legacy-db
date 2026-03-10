# Middleware and Observability

This document outlines the infrastructure components that wrap the core API business logic, providing distributed tracing, structured logging, global exception handling, rate limiting, and metrics.

## 1. Request ID Middleware (`RequestIDMiddleware`)

Every incoming request is assigned a unique UUID. This ID is essential for tracking requests across microservices or through complex backend logs.

* **Headers**: Looks for an incoming `X-Request-ID` header. If missing, it generates a new UUID.
* **Context**: Sets `request.state.request_id` for downstream use inside the application.
* **Response**: Attaches the `X-Request-ID` header to the outgoing response.

## 2. API Logging Middleware (`APILoggingMiddleware`)

Automates logging of all incoming requests and outgoing responses using `loguru`. Logs are emitted in a structured JSON layout suitable for aggregation tools (e.g., ELK, Datadog).

Logs record:
* `request_id`
* `method`
* `path`
* `client_ip`
* `status_code`
* `latency_ms`

## 3. Global Exception Handler

A centralized exception handler ensures that **no stack traces or unhandled exceptions are leaked to the client**.

Located in `web/exceptions/global_exception_handler.py`.

It catches:
1. `HTTPException`: Native FastAPI HTTP errors.
2. `RequestValidationError`: Pydantic validation failures.
3. `Exception`: Every other generic/unhandled error.

All exceptions are parsed and reformatted using the `error_response` builder, ensuring the client ALWAYS receives the standard `BaseResponse` model (described in `docs/api/standards.md`). Detailed stack traces are logged internally using the `request_id`.

## 4. Rate Limiting (`slowapi`)

The API requires protection against abuse or runaway scripts.

* Implemented using `slowapi` (a token-bucket rate limiter for Starlette/FastAPI).
* **Default limit**: Currently set globally to 100 requests per minute per IP.
* **Response**: Exceeding the limit results in an `HTTP 429 Too Many Requests` wrapped in the standard `BaseResponse` format.
* **Override**: Rate limits can be overridden per-endpoint using the `@limiter.limit("5/minute")` decorator.

## 5. Prometheus Metrics

We track core API metrics using `prometheus-client`. These metrics are natively scraped by Prometheus.

* **Endpoint**: `GET /api/v1/metrics`
* **Metrics Tracked**:
  * `http_requests_total` (Counter): Broken down by `method`, `endpoint`, and `status_code`.
  * `http_request_latency_seconds` (Histogram): Request latency broken down by `method` and `endpoint`.
  * `http_request_errors_total` (Counter): Backend exceptions broken down by `method`, `endpoint`, and `error_type`.

## Integration Overview

All these components are registered during application startup in `web/application.py`. The order of middleware registration is critical because Starlette executes them in reverse order (bottom-to-top) for incoming requests.

```python
# Setup Exceptions
setup_global_exception_handlers(app)

# Setup Limiter
setup_rate_limiter(app)

# Last added is first to execute
app.add_middleware(APILoggingMiddleware)
app.add_middleware(RequestIDMiddleware)  # Runs second, has no access to log latency
app.add_middleware(PrometheusMiddleware) # Runs first, catches everything for metrics
```
