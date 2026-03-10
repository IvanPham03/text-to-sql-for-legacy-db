import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.responses import JSONResponse

from ivanpham_chatbot_assistant.web.utils.response_builder import error_response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"HTTP Exception: {exc.detail}",
        request_id=request_id,
        status_code=exc.status_code,
        path=request.url.path,
    )

    standard_response = error_response(
        message="HTTP Error",
        error_code="HTTP_ERROR",
        details=str(exc.detail),
        meta={"request_id": request_id},
    )
    return JSONResponse(
        status_code=exc.status_code, content=standard_response.model_dump()
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"Validation Error: {exc.errors()}",
        request_id=request_id,
        path=request.url.path,
    )

    standard_response = error_response(
        message="Validation error",
        error_code="INVALID_REQUEST",
        details=str(exc.errors()),
        meta={"request_id": request_id},
    )
    return JSONResponse(status_code=422, content=standard_response.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Unhandled Exception: {exc!s}",
        request_id=request_id,
        path=request.url.path,
        traceback=traceback.format_exc(),
    )

    standard_response = error_response(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details="An unexpected error occurred",
        meta={"request_id": request_id},
    )
    return JSONResponse(status_code=500, content=standard_response.model_dump())


def setup_global_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
