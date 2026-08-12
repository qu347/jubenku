from fastapi import APIRouter

from app.api.endpoints import genre_metrics, genre_modules, genre_positioning, health, materials, upload_platforms

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(genre_modules.router)
api_router.include_router(materials.router)
api_router.include_router(genre_metrics.router)
api_router.include_router(genre_positioning.router)
api_router.include_router(upload_platforms.router)
