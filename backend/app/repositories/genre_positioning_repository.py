from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import GenreModule, Material


class GenrePositioningRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        genre_module_id: str | None,
        upload_platform: str | None,
        heat_min: float | None,
        heat_max: float | None,
    ) -> list[dict[str, Any]]:
        normalized_platform = func.lower(func.trim(Material.upload_platform))
        material_filters = (
            Material.deleted_at.is_(None),
            Material.library_type == "material",
            Material.upload_platform.is_not(None),
            func.trim(Material.upload_platform) != "",
            Material.platform_heat.is_not(None),
        )

        latest_rows = (
            select(
                Material.genre_module_id.label("genre_module_id"),
                normalized_platform.label("normalized_platform"),
                func.trim(Material.upload_platform).label("upload_platform"),
                func.row_number()
                .over(
                    partition_by=(Material.genre_module_id, normalized_platform),
                    order_by=(Material.updated_at.desc(), Material.id.desc()),
                )
                .label("row_number"),
            )
            .where(*material_filters)
            .subquery()
        )

        average_heat = func.avg(Material.platform_heat).label("average_heat")
        aggregate = (
            select(
                Material.genre_module_id.label("genre_module_id"),
                GenreModule.name.label("genre_name"),
                GenreModule.theme_color.label("theme_color"),
                normalized_platform.label("normalized_platform"),
                average_heat,
                func.count(Material.id).label("material_count"),
                func.max(Material.updated_at).label("latest_updated_at"),
            )
            .join(GenreModule, GenreModule.id == Material.genre_module_id)
            .where(*material_filters, GenreModule.deleted_at.is_(None))
            .group_by(
                Material.genre_module_id,
                GenreModule.name,
                GenreModule.theme_color,
                normalized_platform,
            )
        )
        if genre_module_id:
            aggregate = aggregate.where(Material.genre_module_id == genre_module_id)
        if upload_platform:
            aggregate = aggregate.where(normalized_platform == upload_platform.strip().casefold())
        if heat_min is not None:
            aggregate = aggregate.having(func.avg(Material.platform_heat) >= heat_min)
        if heat_max is not None:
            aggregate = aggregate.having(func.avg(Material.platform_heat) <= heat_max)

        aggregate_rows = aggregate.subquery()
        statement = (
            select(
                aggregate_rows.c.genre_module_id,
                aggregate_rows.c.genre_name,
                aggregate_rows.c.theme_color,
                latest_rows.c.upload_platform,
                aggregate_rows.c.average_heat,
                aggregate_rows.c.material_count,
                aggregate_rows.c.latest_updated_at,
            )
            .join(
                latest_rows,
                latest_rows.c.genre_module_id == aggregate_rows.c.genre_module_id,
            )
            .where(
                latest_rows.c.normalized_platform == aggregate_rows.c.normalized_platform,
                latest_rows.c.row_number == 1,
            )
            .order_by(
                aggregate_rows.c.average_heat.desc(),
                aggregate_rows.c.genre_name.asc(),
                aggregate_rows.c.normalized_platform.asc(),
            )
        )
        return [dict(row) for row in self.session.execute(statement).mappings()]
