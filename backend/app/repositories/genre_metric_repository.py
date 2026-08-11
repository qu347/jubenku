from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import GenreMetric, GenreModule

AGE_FILTER_ALIASES = {
    "youth": ("youth", "少年"),
    "middle": ("middle", "中年"),
    "senior": ("senior", "老年"),
}
EDUCATION_FILTER_ALIASES = {
    "low": ("low", "低学历"),
    "medium": ("medium", "中学历"),
    "high": ("high", "高学历"),
}
PERIOD_FILTER_ALIASES = {"2026-08": ("2026-08", "近30天")}
TREND_FILTER_ALIASES = {
    "rising": ("rising", "上升"),
    "stable": ("stable", "稳定"),
    "falling": ("falling", "下降"),
}


class GenreMetricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, metric_id: str) -> GenreMetric | None:
        return self.session.scalar(
            select(GenreMetric)
            .options(joinedload(GenreMetric.genre_module))
            .where(GenreMetric.id == metric_id, GenreMetric.deleted_at.is_(None))
        )

    def get_module(self, module_id: str) -> GenreModule | None:
        return self.session.scalar(
            select(GenreModule).where(
                GenreModule.id == module_id,
                GenreModule.deleted_at.is_(None),
            )
        )

    def get_module_by_name(self, name: str) -> GenreModule | None:
        return self.session.scalar(
            select(GenreModule).where(
                func.lower(GenreModule.name) == name.strip().lower(),
                GenreModule.deleted_at.is_(None),
            )
        )

    def _filtered_statement(
        self,
        *,
        genre_module_id: str | None,
        platform: str | None,
        channel: str | None,
        period: str | None,
        age_group: str | None,
        education_level: str | None,
        trend: str | None,
        is_core: bool | None,
        heat_min: float | None,
        heat_max: float | None,
    ):
        statement = (
            select(GenreMetric)
            .options(joinedload(GenreMetric.genre_module))
            .where(GenreMetric.deleted_at.is_(None))
        )
        if genre_module_id:
            statement = statement.where(GenreMetric.genre_module_id == genre_module_id)
        if platform:
            statement = statement.where(func.lower(GenreMetric.platform) == platform.strip().lower())
        if channel:
            statement = statement.where(func.lower(GenreMetric.channel) == channel.strip().lower())
        if period:
            normalized_period = period.strip().upper()
            statement = statement.where(
                GenreMetric.period.in_(PERIOD_FILTER_ALIASES.get(normalized_period, (normalized_period,)))
            )
        if age_group:
            statement = statement.where(
                GenreMetric.age_group.in_(AGE_FILTER_ALIASES.get(age_group, (age_group,)))
            )
        if education_level:
            statement = statement.where(
                GenreMetric.education_level.in_(
                    EDUCATION_FILTER_ALIASES.get(education_level, (education_level,))
                )
            )
        if trend:
            statement = statement.where(
                GenreMetric.trend.in_(TREND_FILTER_ALIASES.get(trend, (trend,)))
            )
        if is_core is not None:
            statement = statement.where(GenreMetric.is_core.is_(is_core))
        if heat_min is not None:
            statement = statement.where(GenreMetric.heat_index >= heat_min)
        if heat_max is not None:
            statement = statement.where(GenreMetric.heat_index <= heat_max)
        return statement

    def list(
        self,
        *,
        page: int,
        page_size: int,
        **filters,
    ) -> tuple[list[GenreMetric], int]:
        statement = self._filtered_statement(**filters)
        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        items = list(
            self.session.scalars(
                statement.order_by(GenreMetric.created_at.desc(), GenreMetric.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def export(self, **filters) -> list[GenreMetric]:
        return list(
            self.session.scalars(
                self._filtered_statement(**filters).order_by(
                    GenreMetric.created_at.desc(), GenreMetric.id
                )
            ).all()
        )

    def create(self, values: dict) -> GenreMetric:
        metric = GenreMetric(**values)
        self.session.add(metric)
        self.session.flush()
        return metric
