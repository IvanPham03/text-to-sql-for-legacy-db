import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger

from ivanpham_chatbot_assistant.services.pipelines.online import online_pipeline
from ivanpham_chatbot_assistant.web.schemas.base_response import BaseResponse
from ivanpham_chatbot_assistant.web.schemas.query_schema import (
    AskRequest,
    AskResponseData,
)
from ivanpham_chatbot_assistant.web.utils.response_builder import (
    error_response,
    success_response,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /ask  —  Standard (blocking) endpoint
# ---------------------------------------------------------------------------


@router.post("/ask", response_model=BaseResponse)
async def ask_question(request: AskRequest) -> BaseResponse:
    """
    Accepts a natural language question and returns the full pipeline result
    in one structured response once the pipeline has finished.

    Response payload (inside `data`):
    - sql      – the generated SQL query
    - columns  – list of column names returned by the query
    - rows     – list of value lists (one per row)
    - answer   – natural language answer
    - row_count – number of rows returned
    """
    logger.info("POST /ask received", question=request.question)

    try:
        result: AskResponseData = await online_pipeline.ask_question(request)
        return success_response(
            data=result.model_dump(),
            message="Query processed successfully.",
        )

    except Exception as exc:
        logger.exception("POST /ask pipeline error")
        return error_response(
            message="An error occurred while processing the query.",
            error_code="PIPELINE_ERROR",
            details=str(exc),
        )


# ---------------------------------------------------------------------------
# POST /ask/stream  —  Server-Sent Events (SSE) streaming endpoint
# ---------------------------------------------------------------------------


async def _event_generator(request: AskRequest) -> AsyncGenerator[str]:
    """
    Converts pipeline events into SSE-formatted strings.
    Each yielded chunk follows the SSE spec:  ``data: <JSON>\n\n``
    """
    try:
        async for event in online_pipeline.ask_question_stream(request):
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"
    except Exception as exc:
        logger.exception("SSE event generator encountered an unexpected error.")
        error_event = json.dumps({"event": "error", "message": str(exc)})
        yield f"data: {error_event}\n\n"


@router.post("/ask/stream")
async def ask_question_stream(request: AskRequest) -> StreamingResponse:
    """
    Accepts a natural language question and streams intermediate pipeline
    events back to the client using Server-Sent Events (SSE).

    The client should handle events with the following `event` values:
    - ``intent_detected``  – intent classification result
    - ``schema_retrieved`` – number of schema elements retrieved
    - ``sql_generated``    – the generated SQL string
    - ``sql_validated``    – whether validation passed
    - ``query_executed``   – number of rows returned by execution
    - ``final_answer``     – natural language answer + full result set
    - ``error``            – pipeline error (stream ends after this)

    Example client usage (JavaScript):
    ```js
    const es = new EventSource('/api/online/ask/stream');
    es.onmessage = (e) => console.log(JSON.parse(e.data));
    ```
    """
    logger.info("POST /ask/stream received", question=request.question)

    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering if behind a proxy
        },
    )


# ---------------------------------------------------------------------------
# GET /history  —  stub (not yet implemented)
# ---------------------------------------------------------------------------


@router.get("/history", response_model=BaseResponse)
async def get_history() -> BaseResponse:
    """Returns query history (not yet implemented)."""
    return success_response(data={"history": []}, message="History retrieved.")
