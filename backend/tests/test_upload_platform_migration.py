from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


def test_upload_platform_catalog_migration_backfills_history_and_roundtrips(tmp_path: Path) -> None:
    database_path = tmp_path / "upload-platform_catalog.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    original_url = settings.database_url
    settings.database_url = database_url
    engine = None
    try:
        command.upgrade(config, "20260812_0008")
        engine = create_engine(database_url)
        now = datetime.now(timezone.utc).isoformat()
        with engine.begin() as connection:
            connection.execute(
                text(
                    """INSERT INTO genre_modules
                    (id,name,slug,icon,description,theme_color,sort_order,status,visible,
                     profile_json,created_at,updated_at,deleted_at,material_visible,script_visible,
                     material_sort_order,script_sort_order)
                    VALUES
                    ('11111111-1111-1111-1111-111111111111','迁移测试','migration-platform',
                     'Collection','','#f59e0b',0,'active',1,'{}',:now,:now,NULL,1,1,0,0)"""
                ),
                {"now": now},
            )
            connection.execute(
                text(
                    """INSERT INTO materials
                    (id,title,material_type,genre,summary,content,genre_module_id,
                     created_at,updated_at,upload_platform,platform_heat)
                    VALUES
                    ('22222222-2222-2222-2222-222222222222','历史素材','剧情','西方奇幻',
                     '摘要','正文','11111111-1111-1111-1111-111111111111',:now,:now,'历史站点',80)"""
                ),
                {"now": now},
            )
        engine.dispose()

        command.upgrade(config, "head")
        command.check(config)
        engine = create_engine(database_url)
        assert "upload_platforms" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT name,is_system FROM upload_platforms ORDER BY is_system DESC,sort_order,name")
            ).all()
            assert len(rows) == 11
            assert rows[0] == ("番茄小说", 1)
            assert ("历史站点", 0) in rows
            assert connection.execute(
                text("SELECT upload_platform FROM materials WHERE id='22222222-2222-2222-2222-222222222222'")
            ).scalar_one() == "历史站点"

        engine.dispose()
        command.downgrade(config, "20260812_0008")
        engine = create_engine(database_url)
        assert "upload_platforms" not in inspect(engine).get_table_names()
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT upload_platform FROM materials WHERE id='22222222-2222-2222-2222-222222222222'")
            ).scalar_one() == "历史站点"

        engine.dispose()
        command.upgrade(config, "head")
        command.check(config)
    finally:
        if engine is not None:
            engine.dispose()
        settings.database_url = original_url
        database_path.unlink(missing_ok=True)
