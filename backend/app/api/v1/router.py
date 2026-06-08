"""
API v1 Router - combines all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.logs import router as logs_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.copilot import router as copilot_router
from app.api.v1.endpoints.evaluations import router as evaluations_router
from app.api.v1.endpoints.misc import (
    alerts_router, feedback_router, security_router, users_router
)

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(logs_router)
api_router.include_router(analytics_router)
api_router.include_router(projects_router)
api_router.include_router(copilot_router)
api_router.include_router(evaluations_router)
api_router.include_router(alerts_router)
api_router.include_router(feedback_router)
api_router.include_router(security_router)
api_router.include_router(users_router)
