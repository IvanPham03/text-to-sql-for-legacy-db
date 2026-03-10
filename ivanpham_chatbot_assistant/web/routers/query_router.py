from fastapi import APIRouter, Query, Path, HTTPException
from ivanpham_chatbot_assistant.web.schemas.base_response import BaseResponse
from ivanpham_chatbot_assistant.web.schemas.query_schema import AskRequest
from ivanpham_chatbot_assistant.web.utils.response_builder import success_response
from ivanpham_chatbot_assistant.services.pipelines.online import online_pipeline as query_service

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

@router.post("/ask", response_model=BaseResponse)
async def ask_question(request: AskRequest):
    """
    Accept natural language question and return generated SQL result.
    """
    result = await query_service.ask_question(request)
    return success_response(
        data=result.model_dump(),
        message="Query executed successfully"
    )

@router.get("/history", response_model=BaseResponse)
async def query_history(
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Return previous queries.
    """
    history = await query_service.get_history(limit=limit, offset=offset)
    return success_response(
        data=[item.model_dump() for item in history],
        message="History retrieved successfully"
    )

@router.get("/history/{query_id}", response_model=BaseResponse)
async def query_detail(
    query_id: str = Path(..., description="ID of the query to retrieve")
):
    """
    Return detail of a specific query.
    """
    detail = await query_service.get_query_detail(query_id=query_id)
    return success_response(
        data=detail.model_dump(),
        message=f"Query {query_id} retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """
    Health Check endpoint for the query service.
    """
    return {"status": "ok"}
