import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


def test_sprint3_migration_roundtrip_preserves_31_materials_20_metrics_and_chinese() -> None:
    descriptor, filename = tempfile.mkstemp(prefix="script_materials_migration_", suffix=".db")
    os.close(descriptor)
    database_path = Path(filename)
    database_path.unlink()
    database_url = f"sqlite:///{database_path.as_posix()}"
    original_url = settings.database_url
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[1] / "alembic"),
    )
    settings.database_url = database_url
    engine = None
    try:
        command.upgrade(config, "20260810_0003")
        engine = create_engine(database_url)
        now = datetime.now(timezone.utc).isoformat()
        with engine.begin() as connection:
            connection.execute(
                text(
                    """INSERT INTO genre_modules
                    (id,name,slug,icon,description,theme_color,sort_order,status,visible,
                     profile_json,created_at,updated_at,deleted_at)
                    VALUES
                    ('11111111-1111-1111-1111-111111111111','迁移测试','migration-test',
                     'Collection','','#f59e0b',0,'active',1,'{}',:now,:now,NULL)"""
                ),
                {"now": now},
            )
            material_rows = [
                {
                    "id": f"10000000-0000-0000-0000-{index:012d}",
                    "title": f"旧素材 {index:02d}",
                    "material_type": "人物素材" if index % 2 else "剧情素材",
                    "genre": "悬疑灵异",
                    "summary": f"中文历史摘要 {index:02d}",
                    "content": f"中文历史正文：近30天素材 {index:02d}",
                    "genre_module_id": "11111111-1111-1111-1111-111111111111",
                    "now": now,
                }
                for index in range(1, 32)
            ]
            connection.execute(
                text(
                    """INSERT INTO materials
                    (id,title,material_type,genre,summary,content,genre_module_id,
                     created_at,updated_at)
                    VALUES
                    (:id,:title,:material_type,:genre,:summary,:content,:genre_module_id,
                     :now,:now)"""
                ),
                material_rows,
            )
            base_values = {
                "genre_module_id": "11111111-1111-1111-1111-111111111111",
                "platform": "平台",
                "channel": "频道",
                "average_age": 30,
                "audience_share": 50,
                "heat_index": 80,
                "trend": "stable",
                "is_core": True,
                "sample_size": 100,
                "data_source": "来源",
                "remark": "",
                "now": now,
            }
            metric_rows = [
                {
                    **base_values,
                    "id": f"20000000-0000-0000-0000-{index:012d}",
                    "platform": f"中文平台 {index:02d}",
                    "channel": f"内部频道 {index:02d}",
                    "period": "近30天" if index % 2 else "2026-08",
                    "age_group": ("中年" if index % 3 else "老年") if index % 2 else "middle",
                    "education_level": "高学历" if index % 2 else "high",
                    "trend": "rising" if index % 3 else "stable",
                    "remark": f"中文历史备注 {index:02d}",
                }
                for index in range(1, 21)
            ]
            connection.execute(
                text(
                    """INSERT INTO genre_metrics
                    (id,genre_module_id,platform,channel,period,average_age,age_group,
                     education_level,audience_share,heat_index,trend,is_core,sample_size,
                     data_source,remark,created_at,updated_at,deleted_at)
                    VALUES
                    (:id,:genre_module_id,:platform,:channel,:period,:average_age,:age_group,
                     :education_level,:audience_share,:heat_index,:trend,:is_core,:sample_size,
                     :data_source,:remark,:now,:now,NULL)"""
                ),
                metric_rows,
            )

        expected_metrics = [
            (
                item["id"],
                item["platform"],
                item["period"],
                item["age_group"],
                item["education_level"],
                item["trend"],
                item["remark"],
            )
            for item in metric_rows
        ]
        expected_materials = [
            (item["id"], item["title"], item["summary"], item["content"])
            for item in material_rows
        ]

        def assert_historical_rows_unchanged() -> None:
            assert engine is not None
            with engine.connect() as connection:
                material_rows_after = list(
                    connection.execute(
                        text(
                            "SELECT id,title,summary,content FROM materials ORDER BY id"
                        )
                    )
                )
                metric_rows_after = list(
                    connection.execute(
                        text(
                            "SELECT id,platform,period,age_group,education_level,trend,remark "
                            "FROM genre_metrics ORDER BY id"
                        )
                    )
                )
            assert [tuple(row) for row in material_rows_after] == expected_materials
            assert [tuple(row) for row in metric_rows_after] == expected_metrics

        command.upgrade(config, "head")
        command.check(config)
        assert_historical_rows_unchanged()
        assert "storage_path" in {column["name"] for column in inspect(engine).get_columns("materials")}
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM materials")).scalar_one() == 31
            assert connection.execute(text("SELECT COUNT(*) FROM genre_metrics")).scalar_one() == 20
            assert connection.execute(
                text(
                    "SELECT COUNT(*) FROM materials "
                    "WHERE storage_path='' AND original_filename='' AND stored_filename='' AND file_size=0"
                )
            ).scalar_one() == 31

        engine.dispose()
        command.downgrade(config, "20260810_0003")
        engine = create_engine(database_url)
        assert_historical_rows_unchanged()
        assert "storage_path" not in {column["name"] for column in inspect(engine).get_columns("materials")}

        engine.dispose()
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        assert_historical_rows_unchanged()
    finally:
        if engine is not None:
            engine.dispose()
        settings.database_url = original_url
        database_path.unlink(missing_ok=True)
