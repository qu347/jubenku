from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GenreModule, Material

DEMO_SOURCE = "platform-heat-demo-v1"
DEMO_MARKER_KEY = "platform_heat_demo"
DEMO_PLATFORMS = ("抖音", "番茄小说", "小红书", "星河短剧")
_MONTH_PATTERNS = ((0, 2, 4), (1, 3, 5), (0, 3, 5), (1, 2, 4))


@dataclass(frozen=True)
class DemoHeatResult:
    created_count: int
    updated_count: int
    total_count: int


def _recent_months(now: datetime) -> list[datetime]:
    current = now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)
    current_index = current.year * 12 + current.month - 1
    months: list[datetime] = []
    for offset in range(5, -1, -1):
        year, month_index = divmod(current_index - offset, 12)
        months.append(datetime(year, month_index + 1, 15, 12, 0, tzinfo=timezone.utc))
    return months


def _marker_key(material: Material) -> str | None:
    marker = (material.metadata_json or {}).get(DEMO_MARKER_KEY)
    if not isinstance(marker, dict) or marker.get("version") != 1:
        return None
    key = marker.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


def _active_genres(session: Session) -> list[GenreModule]:
    statement = (
        select(GenreModule)
        .where(
            GenreModule.deleted_at.is_(None),
            GenreModule.status == "active",
            GenreModule.visible.is_(True),
            GenreModule.material_visible.is_(True),
        )
        .order_by(GenreModule.material_sort_order, GenreModule.sort_order, GenreModule.name)
        .limit(6)
    )
    return list(session.scalars(statement))


def _apply_demo_values(
    material: Material,
    *,
    genre: GenreModule,
    platform: str,
    month: datetime,
    heat: float,
    demo_key: str,
) -> None:
    period = month.strftime("%Y-%m")
    material.library_type = "material"
    material.genre_module_id = genre.id
    material.title = f"【趋势演示】{platform} · {genre.name} · {period}"
    material.material_type = "剧情"
    material.genre = genre.name
    material.summary = "平台题材月度热度趋势虚拟数据"
    material.content = "该记录仅用于展示题材热度曲线，不包含真实业务内容。"
    material.status = "completed"
    material.source_type = "original"
    material.metadata_json = {DEMO_MARKER_KEY: {"version": 1, "key": demo_key}}
    material.description = "用于查看平台题材月度热度曲线的虚拟素材，可通过演示数据工具一键清理。"
    material.tags_json = ["剧情:逆袭", "情绪:热血", "时代背景:现代", "演示数据"]
    material.source = DEMO_SOURCE
    material.uploaded_by = "演示数据工具"
    material.project_owner = "趋势图演示"
    material.upload_platform = platform
    material.platform_heat = heat
    material.original_filename = ""
    material.stored_filename = ""
    material.storage_path = ""
    material.file_extension = ""
    material.mime_type = "application/octet-stream"
    material.file_size = 0
    material.created_at = month
    material.updated_at = month


def seed_demo_heat(session: Session, *, now: datetime | None = None) -> DemoHeatResult:
    genres = _active_genres(session)
    if not genres:
        raise ValueError("没有可用于趋势演示的启用素材题材")

    existing_items = list(session.scalars(select(Material).where(Material.source == DEMO_SOURCE)))
    existing_by_key = {
        key: material
        for material in existing_items
        if (key := _marker_key(material)) is not None
    }
    months = _recent_months(now or datetime.now(timezone.utc))
    created_count = 0
    updated_count = 0

    for platform_index, platform in enumerate(DEMO_PLATFORMS):
        genre_count = min(3, len(genres))
        selected_genres = [genres[(platform_index + offset) % len(genres)] for offset in range(genre_count)]
        for genre_offset, genre in enumerate(selected_genres):
            for month_offset in _MONTH_PATTERNS[platform_index]:
                month = months[month_offset]
                demo_key = f"{platform_index}:{genre.id}:{month.strftime('%Y-%m')}"
                material = existing_by_key.get(demo_key)
                if material is None:
                    material = Material(title="演示数据", material_type="剧情")
                    session.add(material)
                    existing_by_key[demo_key] = material
                    created_count += 1
                else:
                    updated_count += 1
                heat = float(55 + ((platform_index * 17 + genre_offset * 11 + month_offset * 7) % 43))
                _apply_demo_values(
                    material,
                    genre=genre,
                    platform=platform,
                    month=month,
                    heat=heat,
                    demo_key=demo_key,
                )

    session.flush()
    return DemoHeatResult(
        created_count=created_count,
        updated_count=updated_count,
        total_count=len(existing_by_key),
    )


def remove_demo_heat(session: Session) -> int:
    candidates = list(session.scalars(select(Material).where(Material.source == DEMO_SOURCE)))
    removable = [material for material in candidates if _marker_key(material) is not None]
    for material in removable:
        session.delete(material)
    session.flush()
    return len(removable)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成或清理平台题材热度趋势演示数据")
    parser.add_argument("--remove", action="store_true", help="只清理带完整演示标记的虚拟素材")
    return parser


def main(argv: list[str] | None = None) -> int:
    from app.database.session import SessionLocal

    args = _build_parser().parse_args(argv)
    session = SessionLocal()
    try:
        if args.remove:
            removed = remove_demo_heat(session)
            session.commit()
            print(f"已清理演示素材：{removed} 条")
        else:
            result = seed_demo_heat(session)
            session.commit()
            print(f"演示素材已就绪：新增 {result.created_count} 条，更新 {result.updated_count} 条，共 {result.total_count} 条")
        return 0
    except (ValueError, OSError) as exc:
        session.rollback()
        print(f"演示数据操作失败：{exc}")
        return 1
    except Exception:
        session.rollback()
        print("演示数据操作失败：数据库写入未完成")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
