from fastapi.routing import APIRouter

from ivanpham_chatbot_assistant.web.api import monitoring, offline, online
from ivanpham_chatbot_assistant.web.routers.query_router import router as query_router

api_router = APIRouter()
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(offline.router, prefix="/offline", tags=["offline"])
api_router.include_router(online.router, prefix="/online", tags=["online"])
api_router.include_router(query_router)

