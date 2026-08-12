from __future__ import annotations

from datetime import timezone
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

    def timeline(self, *, upload_platform: str | None) -> dict[str, Any]:
        normalized_platform = upload_platform.strip() if upload_platform else ""
        if not normalized_platform:
            raise AppException(
                "上传平台不能为空",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="platform_required",
            )

        materials = self.repository.timeline(normalized_platform)
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for material in materials:
            created_at = material.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            period = created_at.astimezone(timezone.utc).strftime("%Y-%m")
            genre = material.genre_module
            key = (period, genre.id)
            point = grouped.setdefault(
                key,
                {
                    "genre_module_id": genre.id,
                    "genre_name": genre.name,
                    "theme_color": genre.theme_color,
                    "period": period,
                    "heat_total": 0.0,
                    "material_count": 0,
                },
            )
            point["heat_total"] += float(material.platform_heat)
            point["material_count"] += 1

        points = []
        for point in grouped.values():
            points.append(
                {
                    "genre_module_id": point["genre_module_id"],
                    "genre_name": point["genre_name"],
                    "theme_color": point["theme_color"],
                    "period": point["period"],
                    "average_heat": round(point["heat_total"] / point["material_count"], 1),
                    "material_count": point["material_count"],
                }
            )
        points.sort(key=lambda point: (point["period"], point["genre_name"], point["genre_module_id"]))
        periods = sorted({point["period"] for point in points})
        latest_material = max(
            materials,
            key=lambda material: (
                material.updated_at.replace(tzinfo=timezone.utc)
                if material.updated_at.tzinfo is None
                else material.updated_at.astimezone(timezone.utc),
                material.id,
            ),
            default=None,
        )

        return {
            "upload_platform": (
                latest_material.upload_platform.strip() if latest_material else normalized_platform
            ),
            "periods": periods,
            "points": points,
            "total_materials": len(materials),
        }
