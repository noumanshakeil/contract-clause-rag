from fastapi import APIRouter
from backend.api import contracts, health, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(contracts.router, prefix="/api", tags=["contracts"])
api_router.include_router(ui.router, tags=["ui"])
