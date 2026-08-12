from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import GenreModule, Material, ModuleSection
from app.schemas.genre import GenreLibraryType


class GenreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_modules(
        self,
        *,
        include_inactive: bool = False,
        include_hidden: bool = False,
        include_deleted: bool = False,
        status: str | None = None,
        keyword: str | None = None,
        library_type: GenreLibraryType | None = None,
    ) -> list[tuple[GenreModule, int, int, int]]:
        section_count = (
            select(func.count(ModuleSection.id))
            .where(
                ModuleSection.genre_module_id == GenreModule.id,
                ModuleSection.deleted_at.is_(None),
            )
            .correlate(GenreModule)
            .scalar_subquery()
        )
        material_count = (
            select(func.count(Material.id))
            .where(
                Material.genre_module_id == GenreModule.id,
                Material.library_type == "material",
                Material.deleted_at.is_(None),
            )
            .correlate(GenreModule)
            .scalar_subquery()
        )
        script_count = (
            select(func.count(Material.id))
            .where(
                Material.genre_module_id == GenreModule.id,
                Material.library_type == "script",
                Material.deleted_at.is_(None),
            )
            .correlate(GenreModule)
            .scalar_subquery()
        )
        statement = select(GenreModule, section_count, material_count, script_count)
        if not include_deleted:
            statement = statement.where(GenreModule.deleted_at.is_(None))
        if status:
            statement = statement.where(GenreModule.status == status)
        elif not include_inactive:
            statement = statement.where(GenreModule.status == "active")
        if not include_hidden:
            visible_column = {
                "material": GenreModule.material_visible,
                "script": GenreModule.script_visible,
            }.get(library_type, GenreModule.visible)
            statement = statement.where(visible_column.is_(True))
        if keyword:
            pattern = f"%{keyword.strip()}%"
            statement = statement.where(or_(
                GenreModule.name.ilike(pattern),
                GenreModule.slug.ilike(pattern),
                GenreModule.description.ilike(pattern),
            ))
        sort_column = {
            "material": GenreModule.material_sort_order,
            "script": GenreModule.script_sort_order,
        }.get(library_type, GenreModule.sort_order)
        return list(
            self.session.execute(statement.order_by(sort_column, GenreModule.created_at)).all()
        )

    def get_module(self, module_id: str, *, include_deleted: bool = False) -> GenreModule | None:
        statement = select(GenreModule).where(GenreModule.id == module_id)
        if not include_deleted:
            statement = statement.where(GenreModule.deleted_at.is_(None))
        return self.session.scalar(statement)

    def get_module_by_slug(self, slug: str, *, include_deleted: bool = False) -> GenreModule | None:
        statement = select(GenreModule).where(func.lower(GenreModule.slug) == slug.lower())
        if not include_deleted:
            statement = statement.where(GenreModule.deleted_at.is_(None))
        return self.session.scalar(statement)

    def get_module_by_name(self, name: str, *, include_deleted: bool = False) -> GenreModule | None:
        statement = select(GenreModule).where(func.lower(GenreModule.name) == name.lower())
        if not include_deleted:
            statement = statement.where(GenreModule.deleted_at.is_(None))
        return self.session.scalar(statement)

    def module_counts(self, module_id: str) -> tuple[int, int, int]:
        section_count = self.session.scalar(
            select(func.count(ModuleSection.id)).where(
                ModuleSection.genre_module_id == module_id,
                ModuleSection.deleted_at.is_(None),
            )
        ) or 0
        material_count = self.session.scalar(
            select(func.count(Material.id)).where(
                Material.genre_module_id == module_id,
                Material.library_type == "material",
                Material.deleted_at.is_(None),
            )
        ) or 0
        script_count = self.session.scalar(
            select(func.count(Material.id)).where(
                Material.genre_module_id == module_id,
                Material.library_type == "script",
                Material.deleted_at.is_(None),
            )
        ) or 0
        return section_count, material_count, script_count

    def module_content_counts(self, module_id: str) -> tuple[int, int]:
        rows = self.session.execute(
            select(Material.library_type, func.count(Material.id))
            .where(Material.genre_module_id == module_id)
            .group_by(Material.library_type)
        ).all()
        counts = {library_type: count for library_type, count in rows}
        return counts.get("material", 0), counts.get("script", 0)

    def delete_module(self, module: GenreModule) -> None:
        self.session.delete(module)

    def create_module(self, values: dict) -> GenreModule:
        module = GenreModule(**values)
        self.session.add(module)
        self.session.flush()
        return module

    def list_sections(
        self,
        module_id: str,
        *,
        include_disabled: bool = False,
        include_deleted: bool = False,
    ) -> list[tuple[ModuleSection, int]]:
        material_count = (
            select(func.count(Material.id))
            .where(
                Material.section_id == ModuleSection.id,
                Material.library_type == "material",
                Material.deleted_at.is_(None),
            )
            .correlate(ModuleSection)
            .scalar_subquery()
        )
        statement = select(ModuleSection, material_count).where(
            ModuleSection.genre_module_id == module_id
        )
        if not include_deleted:
            statement = statement.where(ModuleSection.deleted_at.is_(None))
        if not include_disabled:
            statement = statement.where(ModuleSection.enabled.is_(True))
        return list(self.session.execute(
            statement.order_by(ModuleSection.sort_order, ModuleSection.created_at)
        ).all())

    def get_section(self, section_id: str, *, include_deleted: bool = False) -> ModuleSection | None:
        statement = select(ModuleSection).where(ModuleSection.id == section_id)
        if not include_deleted:
            statement = statement.where(ModuleSection.deleted_at.is_(None))
        return self.session.scalar(statement)

    def get_section_by_key(
        self,
        module_id: str,
        section_key: str,
        *,
        include_deleted: bool = False,
    ) -> ModuleSection | None:
        statement = select(ModuleSection).where(
            ModuleSection.genre_module_id == module_id,
            func.lower(ModuleSection.section_key) == section_key.lower(),
        )
        if not include_deleted:
            statement = statement.where(ModuleSection.deleted_at.is_(None))
        return self.session.scalar(statement)

    def create_section(self, module_id: str, values: dict) -> ModuleSection:
        section = ModuleSection(genre_module_id=module_id, **values)
        self.session.add(section)
        self.session.flush()
        return section

    def enabled_section_count(self, module_id: str, *, exclude_id: str | None = None) -> int:
        statement = select(func.count(ModuleSection.id)).where(
            ModuleSection.genre_module_id == module_id,
            ModuleSection.enabled.is_(True),
            ModuleSection.deleted_at.is_(None),
        )
        if exclude_id:
            statement = statement.where(ModuleSection.id != exclude_id)
        return self.session.scalar(statement) or 0

    def get_modules_by_ids(self, ids: list[str]) -> list[GenreModule]:
        return list(self.session.scalars(select(GenreModule).where(
            GenreModule.id.in_(ids), GenreModule.deleted_at.is_(None)
        )).all())

    def get_sections_by_ids(self, ids: list[str]) -> list[ModuleSection]:
        return list(self.session.scalars(select(ModuleSection).where(
            ModuleSection.id.in_(ids), ModuleSection.deleted_at.is_(None)
        )).all())
