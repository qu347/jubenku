from typing import Any

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.database.base import utc_now
from app.models import GenreModule, ModuleSection
from app.repositories import GenreRepository
from app.schemas.genre import (
    GenreModuleCreate,
    GenreModuleUpdate,
    ModuleSectionCreate,
    ModuleSectionUpdate,
    ReorderPayload,
)
from app.seed.data import DEFAULT_SECTIONS


class GenreService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = GenreRepository(session)

    @staticmethod
    def module_data(module: GenreModule, section_count: int = 0, material_count: int = 0) -> dict[str, Any]:
        return {
            "id": module.id,
            "name": module.name,
            "slug": module.slug,
            "icon": module.icon,
            "description": module.description,
            "theme_color": module.theme_color,
            "sort_order": module.sort_order,
            "status": module.status,
            "visible": module.visible,
            "profile_json": module.profile_json or {},
            "created_at": module.created_at,
            "updated_at": module.updated_at,
            "deleted_at": module.deleted_at,
            "section_count": section_count,
            "material_count": material_count,
        }

    @staticmethod
    def section_data(section: ModuleSection, material_count: int = 0) -> dict[str, Any]:
        return {
            "id": section.id,
            "genre_module_id": section.genre_module_id,
            "section_key": section.section_key,
            "section_name": section.section_name,
            "icon": section.icon,
            "sort_order": section.sort_order,
            "enabled": section.enabled,
            "field_schema": section.field_schema or [],
            "filter_schema": section.filter_schema or {},
            "card_schema": section.card_schema or {},
            "created_at": section.created_at,
            "updated_at": section.updated_at,
            "deleted_at": section.deleted_at,
            "material_count": material_count,
        }

    def list_modules(
        self,
        *,
        include_inactive: bool = False,
        include_hidden: bool = False,
        include_deleted: bool = False,
        module_status: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.repository.list_modules(
            include_inactive=include_inactive,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
            status=module_status,
            keyword=keyword,
        )
        return [self.module_data(module, sections, materials) for module, sections, materials in rows]

    def get_module(self, module_id: str) -> dict[str, Any]:
        module = self._module_or_404(module_id)
        section_count, material_count = self.repository.module_counts(module.id)
        return self.module_data(module, section_count, material_count)

    def get_module_by_slug(self, slug: str, *, include_disabled: bool = False) -> dict[str, Any]:
        module = self.repository.get_module_by_slug(slug)
        if module is None:
            raise AppException("题材模块不存在", status_code=status.HTTP_404_NOT_FOUND, code="genre_not_found")
        sections = self.repository.list_sections(module.id, include_disabled=include_disabled)
        section_count, material_count = self.repository.module_counts(module.id)
        return {
            **self.module_data(module, section_count, material_count),
            "sections": [self.section_data(section, count) for section, count in sections],
        }

    def create_module(self, payload: GenreModuleCreate) -> dict[str, Any]:
        self._validate_module_unique(payload.slug, payload.name)
        values = payload.model_dump(exclude={"create_default_sections"})
        try:
            module = self.repository.create_module(values)
            if payload.create_default_sections:
                for sort_order, section in enumerate(DEFAULT_SECTIONS):
                    self.repository.create_section(module.id, {**section, "sort_order": sort_order})
            self.session.commit()
            self.session.refresh(module)
        except IntegrityError as exc:
            self.session.rollback()
            raise self._genre_conflict() from exc
        section_count, material_count = self.repository.module_counts(module.id)
        return self.module_data(module, section_count, material_count)

    def update_module(self, module_id: str, payload: GenreModuleUpdate) -> dict[str, Any]:
        module = self._module_or_404(module_id)
        changes = payload.model_dump(exclude_unset=True)
        self._validate_module_unique(changes.get("slug"), changes.get("name"), exclude_id=module.id)
        for field, value in changes.items():
            setattr(module, field, value)
        self._commit_conflict_safe()
        self.session.refresh(module)
        section_count, material_count = self.repository.module_counts(module.id)
        return self.module_data(module, section_count, material_count)

    def delete_module(self, module_id: str) -> dict[str, str]:
        module = self._module_or_404(module_id)
        module.soft_delete()
        self.session.commit()
        return {"id": module.id}

    def set_module_enabled(self, module_id: str, enabled: bool) -> dict[str, Any]:
        module = self._module_or_404(module_id)
        module.status = "active" if enabled else "inactive"
        self.session.commit()
        self.session.refresh(module)
        section_count, material_count = self.repository.module_counts(module.id)
        return self.module_data(module, section_count, material_count)

    def duplicate_module(self, module_id: str) -> dict[str, Any]:
        source = self._module_or_404(module_id)
        source_sections = self.repository.list_sections(source.id, include_disabled=True)
        slug = self._next_copy_slug(source.slug)
        name = self._next_copy_name(source.name)
        try:
            duplicate = self.repository.create_module({
                "name": name,
                "slug": slug,
                "icon": source.icon,
                "description": source.description,
                "theme_color": source.theme_color,
                "sort_order": source.sort_order + 1,
                "status": "inactive",
                "visible": False,
                "profile_json": dict(source.profile_json or {}),
            })
            for section, _count in source_sections:
                self.repository.create_section(duplicate.id, {
                    "section_key": section.section_key,
                    "section_name": section.section_name,
                    "icon": section.icon,
                    "sort_order": section.sort_order,
                    "enabled": section.enabled,
                    "field_schema": list(section.field_schema or []),
                    "filter_schema": dict(section.filter_schema or {}),
                    "card_schema": dict(section.card_schema or {}),
                })
            self.session.commit()
            self.session.refresh(duplicate)
        except Exception:
            self.session.rollback()
            raise
        section_count, material_count = self.repository.module_counts(duplicate.id)
        return self.module_data(duplicate, section_count, material_count)

    def reorder_modules(self, payload: ReorderPayload) -> list[dict[str, Any]]:
        items = [(str(item.id), item.sort_order) for item in payload.items]
        modules = self.repository.get_modules_by_ids([item_id for item_id, _ in items])
        if len(modules) != len(items):
            raise AppException(
                "排序列表包含不存在的题材模块",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="invalid_reorder_ids",
            )
        order_map = dict(items)
        try:
            for module in modules:
                module.sort_order = order_map[module.id]
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self.list_modules(include_inactive=True, include_hidden=True)

    def list_sections(self, module_id: str, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        self._module_or_404(module_id)
        return [
            self.section_data(section, count)
            for section, count in self.repository.list_sections(module_id, include_disabled=include_disabled)
        ]

    def get_section(self, section_id: str) -> dict[str, Any]:
        section = self._section_or_404(section_id)
        return self.section_data(section)

    def create_section(self, module_id: str, payload: ModuleSectionCreate) -> dict[str, Any]:
        self._module_or_404(module_id)
        self._validate_section_unique(module_id, payload.section_key)
        try:
            section = self.repository.create_section(module_id, payload.model_dump(mode="json"))
            self.session.commit()
            self.session.refresh(section)
        except IntegrityError as exc:
            self.session.rollback()
            raise self._section_conflict() from exc
        return self.section_data(section)

    def update_section(self, section_id: str, payload: ModuleSectionUpdate) -> dict[str, Any]:
        section = self._section_or_404(section_id)
        changes = payload.model_dump(exclude_unset=True, mode="json")
        new_key = changes.get("section_key")
        if new_key:
            self._validate_section_unique(section.genre_module_id, new_key, exclude_id=section.id)
        if changes.get("enabled") is False and section.enabled:
            self._ensure_another_enabled_section(section)
        for field, value in changes.items():
            setattr(section, field, value)
        try:
            self.session.commit()
            self.session.refresh(section)
        except IntegrityError as exc:
            self.session.rollback()
            raise self._section_conflict() from exc
        return self.section_data(section)

    def delete_section(self, section_id: str) -> dict[str, str]:
        section = self._section_or_404(section_id)
        if section.enabled:
            self._ensure_another_enabled_section(section)
        section.soft_delete()
        self.session.commit()
        return {"id": section.id}

    def set_section_enabled(self, section_id: str, enabled: bool) -> dict[str, Any]:
        section = self._section_or_404(section_id)
        if not enabled and section.enabled:
            self._ensure_another_enabled_section(section)
        section.enabled = enabled
        self.session.commit()
        self.session.refresh(section)
        return self.section_data(section)

    def reorder_sections(self, payload: ReorderPayload) -> list[dict[str, Any]]:
        items = [(str(item.id), item.sort_order) for item in payload.items]
        sections = self.repository.get_sections_by_ids([item_id for item_id, _ in items])
        if len(sections) != len(items):
            raise AppException(
                "排序列表包含不存在的功能板块",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="invalid_reorder_ids",
            )
        if len({section.genre_module_id for section in sections}) != 1:
            raise AppException(
                "一次只能排序同一题材模块下的板块",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="mixed_module_sections",
            )
        order_map = dict(items)
        module_id = sections[0].genre_module_id
        try:
            for section in sections:
                section.sort_order = order_map[section.id]
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self.list_sections(module_id, include_disabled=True)

    def _module_or_404(self, module_id: str) -> GenreModule:
        module = self.repository.get_module(module_id)
        if module is None:
            raise AppException("题材模块不存在", status_code=status.HTTP_404_NOT_FOUND, code="genre_not_found")
        return module

    def _section_or_404(self, section_id: str) -> ModuleSection:
        section = self.repository.get_section(section_id)
        if section is None:
            raise AppException("功能板块不存在", status_code=status.HTTP_404_NOT_FOUND, code="section_not_found")
        return section

    def _validate_module_unique(self, slug: str | None, name: str | None, exclude_id: str | None = None) -> None:
        slug_match = self.repository.get_module_by_slug(slug, include_deleted=True) if slug else None
        name_match = self.repository.get_module_by_name(name, include_deleted=True) if name else None
        if (slug_match and slug_match.id != exclude_id) or (name_match and name_match.id != exclude_id):
            raise self._genre_conflict()

    def _validate_section_unique(self, module_id: str, key: str, exclude_id: str | None = None) -> None:
        match = self.repository.get_section_by_key(module_id, key, include_deleted=True)
        if match and match.id != exclude_id:
            raise self._section_conflict()

    def _ensure_another_enabled_section(self, section: ModuleSection) -> None:
        if self.repository.enabled_section_count(section.genre_module_id, exclude_id=section.id) < 1:
            raise AppException(
                "每个题材至少保留一个启用板块",
                status_code=status.HTTP_409_CONFLICT,
                code="last_enabled_section",
            )

    def _next_copy_slug(self, source_slug: str) -> str:
        base = f"{source_slug}-copy"
        candidate = base
        counter = 2
        while self.repository.get_module_by_slug(candidate, include_deleted=True):
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    def _next_copy_name(self, source_name: str) -> str:
        base = f"{source_name}副本"
        candidate = base
        counter = 2
        while self.repository.get_module_by_name(candidate, include_deleted=True):
            candidate = f"{base}{counter}"
            counter += 1
        return candidate[:50]

    def _commit_conflict_safe(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._genre_conflict() from exc

    @staticmethod
    def _genre_conflict() -> AppException:
        return AppException(
            "题材名称或 slug 已存在",
            status_code=status.HTTP_409_CONFLICT,
            code="genre_conflict",
        )

    @staticmethod
    def _section_conflict() -> AppException:
        return AppException(
            "当前题材下的板块 key 已存在",
            status_code=status.HTTP_409_CONFLICT,
            code="section_conflict",
        )
