import json
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Text, cast, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import GenreModule, Material, MaterialTag, Tag


class MaterialRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, material_id: str) -> Material | None:
        return self.session.scalar(
            select(Material)
            .options(
                joinedload(Material.genre_module),
                selectinload(Material.material_tag_links).joinedload(MaterialTag.tag),
            )
            .where(
                Material.id == material_id,
                Material.deleted_at.is_(None),
            )
        )

    def get_module(self, module_id: str) -> GenreModule | None:
        return self.session.scalar(
            select(GenreModule).where(
                GenreModule.id == module_id,
                GenreModule.deleted_at.is_(None),
            )
        )

    def create(self, values: dict) -> Material:
        material = Material(**values)
        self.session.add(material)
        self.session.flush()
        return material

    def list(
        self,
        *,
        keyword: str | None,
        genre_module_id: str | None,
        material_type: str | None,
        file_extension: str | None,
        tags: list[str],
        source: str | None,
        uploaded_from: date | None,
        uploaded_to: date | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Material], int]:
        statement = (
            select(Material)
            .options(
                joinedload(Material.genre_module),
                selectinload(Material.material_tag_links).joinedload(MaterialTag.tag),
            )
            .where(Material.deleted_at.is_(None))
        )
        if keyword:
            pattern = f"%{keyword.strip()}%"
            statement = statement.where(
                or_(
                    Material.title.ilike(pattern),
                    Material.original_filename.ilike(pattern),
                    Material.description.ilike(pattern),
                    Material.summary.ilike(pattern),
                    Material.content.ilike(pattern),
                    Material.source.ilike(pattern),
                )
            )
        if genre_module_id:
            statement = statement.where(Material.genre_module_id == genre_module_id)
        if material_type:
            statement = statement.where(Material.material_type == material_type)
        if file_extension:
            normalized_extension = file_extension.strip().lower()
            if normalized_extension and not normalized_extension.startswith("."):
                normalized_extension = f".{normalized_extension}"
            statement = statement.where(Material.file_extension == normalized_extension)
        if tags:
            tags_expression = cast(Material.tags_json, Text)
            clauses = []
            for tag in tags:
                encoded = json.dumps(tag, ensure_ascii=True)
                clauses.append(tags_expression.ilike(f"%{encoded}%"))
                if not tag.isascii():
                    clauses.append(tags_expression.ilike(f'%"{tag}"%'))
                clauses.append(
                    exists().where(
                        MaterialTag.material_id == Material.id,
                        MaterialTag.tag_id == Tag.id,
                        MaterialTag.deleted_at.is_(None),
                        Tag.deleted_at.is_(None),
                        func.lower(Tag.name) == tag.casefold(),
                    )
                )
            statement = statement.where(or_(*clauses))
        if source:
            statement = statement.where(func.lower(Material.source) == source.strip().lower())
        if uploaded_from:
            start = datetime.combine(uploaded_from, time.min, tzinfo=timezone.utc)
            statement = statement.where(Material.created_at >= start)
        if uploaded_to:
            end = datetime.combine(uploaded_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
            statement = statement.where(Material.created_at < end)

        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        sort_map = {
            "created_desc": Material.created_at.desc(),
            "created_asc": Material.created_at.asc(),
            "updated_desc": Material.updated_at.desc(),
            "updated_asc": Material.updated_at.asc(),
            "title_asc": Material.title.asc(),
            "title_desc": Material.title.desc(),
            "file_size_desc": Material.file_size.desc(),
            "file_size_asc": Material.file_size.asc(),
        }
        items = list(
            self.session.scalars(
                statement.order_by(sort_map[sort], Material.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def delete(self, material: Material) -> None:
        self.session.delete(material)
