"""Backward-compatible aggregate for genre module and metric APIs."""

from fastapi import APIRouter

from app.api.endpoints.genre_metrics import router as metric_router
from app.api.endpoints.genre_modules import router as module_router

router = APIRouter()
router.include_router(module_router)
router.include_router(metric_router)

__all__ = ["router"]
