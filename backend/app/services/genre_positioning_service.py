from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.repositories.genre_positioning_repository import GenrePositioningRepository


class GenrePositioningService:
    def __init__(self, session: Session) -> None:
        self.repository = GenrePositioningRepository(session)

    def list(
        self,
        *,
        genre_module_id: str | None,
        upload_platform: str | None,
        heat_min: float | None,
        heat_max: float | None,
    ) -> dict[str, Any]:
        if heat_min is not None and heat_max is not None and heat_min > heat_max:
            raise AppException(
                "最低热度不能高于最高热度",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="invalid_heat_range",
            )
        items = self.repository.list(
            genre_module_id=genre_module_id,
            upload_platform=upload_platform,
            heat_min=heat_min,
            heat_max=heat_max,
        )
        for item in items:
            item["average_heat"] = round(float(item["average_heat"]), 1)
        return {"items": items, "total": len(items)}
