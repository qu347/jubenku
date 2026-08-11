import io
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.logging import get_app_logger
from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.genre_metric import (
    GenreMetricCreate,
    GenreMetricDeleteResult,
    GenreMetricImportResult,
    GenreMetricPage,
    GenreMetricRead,
    GenreMetricUpdate,
)
from app.services.genre_metric_service import GenreMetricService

router = APIRouter(prefix="/genre-metrics", tags=["genre-metrics"])
logger = get_app_logger("genre_metrics")


def _filters(
    genre_module_id: UUID | None,
    platform: str | None,
    channel: str | None,
    period: str | None,
    age_group: str | None,
    education_level: str | None,
    trend: str | None,
    is_core: bool | None,
    heat_min: float | None,
    heat_max: float | None,
) -> dict[str, Any]:
    return {
        "genre_module_id": str(genre_module_id) if genre_module_id else None,
        "platform": platform,
        "channel": channel,
        "period": period,
        "age_group": age_group,
        "education_level": education_level,
        "trend": trend,
        "is_core": is_core,
        "heat_min": heat_min,
        "heat_max": heat_max,
    }


@router.get("", response_model=ApiResponse[GenreMetricPage])
def list_genre_metrics(
    genre_module_id: UUID | None = None,
    platform: str | None = Query(default=None, max_length=60),
    channel: str | None = Query(default=None, max_length=60),
    period: str | None = Query(default=None, max_length=20),
    age_group: str | None = Query(default=None, pattern=r"^(youth|middle|senior)$"),
    education_level: str | None = Query(default=None, pattern=r"^(low|medium|high)$"),
    trend: str | None = Query(default=None, pattern=r"^(rising|stable|falling)$"),
    is_core: bool | None = None,
    heat_min: float | None = Query(default=None, ge=0, le=100),
    heat_max: float | None = Query(default=None, ge=0, le=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreMetricService(session).list(
        page=page,
        page_size=page_size,
        **_filters(
            genre_module_id,
            platform,
            channel,
            period,
            age_group,
            education_level,
            trend,
            is_core,
            heat_min,
            heat_max,
        ),
    )
    return {"success": True, "data": data, "message": "定位数据列表获取成功", "error": None}


@router.post("", response_model=ApiResponse[GenreMetricRead], status_code=status.HTTP_201_CREATED)
def create_genre_metric(
    payload: GenreMetricCreate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    return {
        "success": True,
        "data": GenreMetricService(session).create(payload),
        "message": "定位数据创建成功",
        "error": None,
    }


# Static utility paths are declared before the UUID detail path.
@router.get("/import-template")
def download_import_template(
    format_: str = Query(default="xlsx", alias="format", pattern=r"^(xlsx|csv)$"),
    session: Session = Depends(get_db),
) -> StreamingResponse:
    content, media_type, filename = GenreMetricService(session).template(format_)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=ApiResponse[GenreMetricImportResult])
async def import_genre_metrics(
    file: Annotated[UploadFile, File()],
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = await GenreMetricService(session).import_file(file)
    logger.info(
        "genre_metric_import success_rows=%s failed_rows=%s",
        data["success_count"],
        data["failure_count"],
    )
    return {"success": True, "data": data, "message": "定位数据导入处理完成", "error": None}


@router.get("/export")
def export_genre_metrics(
    format_: str = Query(default="xlsx", alias="format", pattern=r"^(xlsx|csv)$"),
    genre_module_id: UUID | None = None,
    platform: str | None = Query(default=None, max_length=60),
    channel: str | None = Query(default=None, max_length=60),
    period: str | None = Query(default=None, max_length=20),
    age_group: str | None = Query(default=None, pattern=r"^(youth|middle|senior)$"),
    education_level: str | None = Query(default=None, pattern=r"^(low|medium|high)$"),
    trend: str | None = Query(default=None, pattern=r"^(rising|stable|falling)$"),
    is_core: bool | None = None,
    heat_min: float | None = Query(default=None, ge=0, le=100),
    heat_max: float | None = Query(default=None, ge=0, le=100),
    session: Session = Depends(get_db),
) -> StreamingResponse:
    content, media_type, filename = GenreMetricService(session).export(
        format_,
        **_filters(
            genre_module_id,
            platform,
            channel,
            period,
            age_group,
            education_level,
            trend,
            is_core,
            heat_min,
            heat_max,
        ),
    )
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{metric_id}", response_model=ApiResponse[GenreMetricRead])
def get_genre_metric(metric_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "success": True,
        "data": GenreMetricService(session).get(str(metric_id)),
        "message": "定位数据详情获取成功",
        "error": None,
    }


@router.patch("/{metric_id}", response_model=ApiResponse[GenreMetricRead])
def update_genre_metric(
    metric_id: UUID,
    payload: GenreMetricUpdate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    return {
        "success": True,
        "data": GenreMetricService(session).update(str(metric_id), payload),
        "message": "定位数据更新成功",
        "error": None,
    }


@router.delete("/{metric_id}", response_model=ApiResponse[GenreMetricDeleteResult])
def delete_genre_metric(metric_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "success": True,
        "data": GenreMetricService(session).delete(str(metric_id)),
        "message": "定位数据已删除",
        "error": None,
    }
