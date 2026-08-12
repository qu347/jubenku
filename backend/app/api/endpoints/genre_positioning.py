from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.genre_positioning import GenrePositioningList, GenrePositioningTimeline
from app.services.genre_positioning_service import GenrePositioningService

router = APIRouter(prefix="/genre-positioning", tags=["genre-positioning"])


@router.get("/timeline", response_model=ApiResponse[GenrePositioningTimeline])
def get_genre_positioning_timeline(
    upload_platform: str | None = Query(default=None, max_length=60),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenrePositioningService(session).timeline(upload_platform=upload_platform)
    return {"success": True, "data": data, "message": "题材平台时间线获取成功", "error": None}


@router.get("", response_model=ApiResponse[GenrePositioningList])
def list_genre_positioning(
    genre_module_id: UUID | None = None,
    upload_platform: str | None = Query(default=None, max_length=60),
    heat_min: float | None = Query(default=None, ge=0, le=100),
    heat_max: float | None = Query(default=None, ge=0, le=100),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenrePositioningService(session).list(
        genre_module_id=str(genre_module_id) if genre_module_id else None,
        upload_platform=upload_platform,
        heat_min=heat_min,
        heat_max=heat_max,
    )
    return {"success": True, "data": data, "message": "题材平台定位获取成功", "error": None}
