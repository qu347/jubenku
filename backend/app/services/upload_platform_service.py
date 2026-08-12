import unicodedata
from typing import Any

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.upload_platform import UploadPlatform
from app.repositories.upload_platform_repository import UploadPlatformRepository
from app.schemas.upload_platform import UploadPlatformCreate


DEFAULT_UPLOAD_PLATFORMS: tuple[str, ...] = (
    "番茄小说",
    "七猫",
    "起点中文网",
    "晋江文学城",
    "纵横中文网",
    "抖音",
    "快手",
    "小红书",
    "微信公众号",
    "知乎",
)


def normalize_upload_platform_name(value: str) -> tuple[str, str]:
    display_name = unicodedata.normalize("NFKC", value).strip()
    if not display_name or len(display_name) > 60:
        raise AppException(
            "平台名称必须为 1 到 60 个字符",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_upload_platform",
        )
    return display_name, display_name.casefold()


def upload_platform_to_dict(platform: UploadPlatform) -> dict[str, Any]:
    return {
        "id": platform.id,
        "name": platform.name,
        "is_system": platform.is_system,
    }


class UploadPlatformService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UploadPlatformRepository(session)

    def list(self) -> list[dict[str, Any]]:
        return [upload_platform_to_dict(item) for item in self.repository.list_active()]

    def create(self, payload: UploadPlatformCreate) -> dict[str, Any]:
        display_name, normalized_name = normalize_upload_platform_name(payload.name)
        if self.repository.get_by_normalized_name(normalized_name) is not None:
            raise self._duplicate_error()
        try:
            platform = self.repository.create(name=display_name, normalized_name=normalized_name)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._duplicate_error() from exc
        return upload_platform_to_dict(platform)

    @staticmethod
    def _duplicate_error() -> AppException:
        return AppException(
            "该平台已存在",
            status_code=status.HTTP_409_CONFLICT,
            code="upload_platform_exists",
        )
