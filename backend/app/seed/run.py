from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import GenreModule, ModuleSection
from app.seed.data import DEFAULT_GENRE_MODULES, DEFAULT_SECTIONS


def seed_genre_modules(session: Session) -> tuple[int, int]:
    for sort_order, item in enumerate(DEFAULT_GENRE_MODULES):
        module = session.scalar(select(GenreModule).where(GenreModule.slug == item["slug"]))
        if module is None:
            module = GenreModule(
                **item,
                description=f"{item['name']}题材的模块化创作素材。",
                sort_order=sort_order,
                status="active",
                visible=True,
                profile_json={},
            )
            session.add(module)
            session.flush()
        else:
            module.name = item["name"]
            module.icon = item["icon"]
            module.theme_color = item["theme_color"]
            module.sort_order = sort_order
            module.status = "active"
            module.visible = True
            module.deleted_at = None

        for section_order, section_item in enumerate(DEFAULT_SECTIONS):
            section = session.scalar(
                select(ModuleSection).where(
                    ModuleSection.genre_module_id == module.id,
                    ModuleSection.section_key == section_item["section_key"],
                )
            )
            if section is None:
                session.add(ModuleSection(
                    genre_module_id=module.id,
                    **section_item,
                    sort_order=section_order,
                    enabled=True,
                    filter_schema={},
                    card_schema={},
                ))
            else:
                section.section_name = section_item["section_name"]
                section.icon = section_item["icon"]
                section.sort_order = section_order
                section.enabled = True
                section.deleted_at = None

    session.commit()
    module_count = session.query(GenreModule).filter(GenreModule.deleted_at.is_(None)).count()
    section_count = session.query(ModuleSection).filter(ModuleSection.deleted_at.is_(None)).count()
    return module_count, section_count


def main() -> None:
    with SessionLocal() as session:
        module_count, section_count = seed_genre_modules(session)
    print(f"初始化完成：{module_count} 个题材模块，{section_count} 个功能板块。")


if __name__ == "__main__":
    main()
