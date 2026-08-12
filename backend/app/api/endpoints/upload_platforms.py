from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.upload_platform import UploadPlatformCreate, UploadPlatformRead
from app.services.upload_platform_service import UploadPlatformService


router = APIRouter(prefix="/upload-platforms", tags=["upload-platforms"])


@router.get("", response_model=ApiResponse[list[UploadPlatformRead]])
def list_upload_platforms(session: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "success": True,
        "data": UploadPlatformService(session).list(),
        "message": "上传平台列表获取成功",
        "error": None,
    }


@router.post("", response_model=ApiResponse[UploadPlatformRead], status_code=status.HTTP_201_CREATED)
def create_upload_platform(
    payload: UploadPlatformCreate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    return {
        "success": True,
        "data": UploadPlatformService(session).create(payload),
        "message": "上传平台创建成功",
        "error": None,
    }
