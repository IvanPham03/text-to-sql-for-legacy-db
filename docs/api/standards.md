# API Standards & Request/Response Formats

This document describes the standardized request and response format used across the Text-to-SQL API. By following these conventions, the API ensures consistency, predictability, and ease of use for clients.

## Standard Response Format

All API endpoints return a standardized wrapper model `BaseResponse`.

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "key": "value"
  },
  "error": null,
  "meta": {
    "request_id": "8f3b0e1b-4d43-41bb-bd03-c0d12753a7ff",
    "timestamp": "2023-11-01T14:32:00.000Z"
  }
}
```

### Components

* **`success`** (`bool`): Indicates whether the request was successful.
* **`message`** (`string`): A human-readable message about the result.
* **`data`** (`any`, optional): The requested payload or result data. Omitted or `null` if no data is returned.
* **`error`** (`ErrorDetail`, optional): Details about an error if `success` is false.
* **`meta`** (`object`): Request metadata. Always includes `request_id` and `timestamp`.

## Standard Error Format

When an error occurs, the standard response wrapper is still used, but `success` is `false` and the `error` object is populated.

```json
{
  "success": false,
  "message": "Validation error",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "details": "[{'type': 'missing', 'loc': ('body', 'database_name'), 'msg': 'Field required'}]"
  },
  "meta": {
    "request_id": "8f3b0e1b-4d43-41bb-bd03-c0d12753a7ff",
    "timestamp": "2023-11-01T14:32:00.000Z"
  }
}
```

### Components of `error` (`ErrorDetail`)

* **`code`** (`string`): A programmatic identifier for the error category (e.g., `INTERNAL_ERROR`, `INVALID_REQUEST`, `HTTP_ERROR`, `RATE_LIMIT_EXCEEDED`).
* **`details`** (`string`): Specific details, often including framework exceptions or validation messages.

## Using the Response Builder

Developers do not need to construct the `BaseResponse` manually. Use the utility functions in `web/utils/response_builder.py`.

```python
from ivanpham_chatbot_assistant.web.utils.response_builder import success_response, error_response

# Success
return success_response(data={"user_id": 123}, message="User retrieved")

# Error
return error_response(
    message="Unauthorized access", 
    error_code="UNAUTHORIZED", 
    details="Invalid token"
)
```

## Pagination

For endpoints returning lists of items, the `data` field should contain a `PaginationResponse` object:

```json
{
  "success": true,
  "message": "List retrieved",
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "size": 50,
    "pages": 3
  },
  "error": null,
  "meta": {...}
}
```

## FastAPI Configuration

All endpoints **must** define `response_model=BaseResponse` in their router decorator to ensure OpenAPI documentation correctly reflects the wrapper structure.

```python
@router.post("/example", response_model=BaseResponse)
async def post_example(request: ExampleRequest):
    ...
```
