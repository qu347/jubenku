from __future__ import annotations

import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import GenreModule, Material


def normalize_upload_platform(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip()).casefold()


class GenrePositioningRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        genre_module_id: str | None,
        upload_platform: str | None,
    ) -> list[Material]:
        normalized_platform = (
            normalize_upload_platform(upload_platform) if upload_platform is not None else None
        )
        return [
            material
            for material in self._valid_materials()
            if (genre_module_id is None or material.genre_module_id == genre_module_id)
            and normalize_upload_platform(material.upload_platform)
            and (
                normalized_platform is None
                or normalize_upload_platform(material.upload_platform) == normalized_platform
            )
        ]

    def timeline(self, upload_platform: str | None) -> list[Material]:
        return self.list(genre_module_id=None, upload_platform=upload_platform)

    def _valid_materials(self) -> list[Material]:
        statement = (
            select(Material)
            .join(GenreModule, GenreModule.id == Material.genre_module_id)
            .options(joinedload(Material.genre_module))
            .where(
                Material.deleted_at.is_(None),
                Material.library_type == "material",
                Material.upload_platform.is_not(None),
                func.trim(Material.upload_platform) != "",
                Material.platform_heat.is_not(None),
                GenreModule.deleted_at.is_(None),
                GenreModule.status == "active",
            )
        )
        return list(self.session.scalars(statement))
