from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.upload_platform import UploadPlatform


class UploadPlatformRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self) -> list[UploadPlatform]:
        statement = (
            select(UploadPlatform)
            .where(UploadPlatform.deleted_at.is_(None))
            .order_by(
                UploadPlatform.is_system.desc(),
                UploadPlatform.sort_order.asc(),
                UploadPlatform.name.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def get_by_normalized_name(self, normalized_name: str) -> UploadPlatform | None:
        return self.session.scalar(
            select(UploadPlatform).where(
                UploadPlatform.normalized_name == normalized_name,
                UploadPlatform.deleted_at.is_(None),
            )
        )

    def create(self, *, name: str, normalized_name: str) -> UploadPlatform:
        platform = UploadPlatform(
            name=name,
            normalized_name=normalized_name,
            is_system=False,
            sort_order=1000,
        )
        self.session.add(platform)
        self.session.flush()
        return platform
