from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GenreModule, Material
from app.tools.seed_demo_heat import (
    DEMO_MARKER_KEY,
    DEMO_SOURCE,
    remove_demo_heat,
    seed_demo_heat,
)


def create_genres(session: Session) -> list[GenreModule]:
    genres = [
        GenreModule(
            name=f"演示题材{index + 1}",
            slug=f"demo-genre-{index + 1}",
            sort_order=index,
            material_sort_order=index,
        )
        for index in range(6)
    ]
    session.add_all(genres)
    session.flush()
    return genres


def test_demo_heat_seed_is_idempotent_and_visible_in_positioning_api(
    db_session: Session, client
) -> None:
    create_genres(db_session)
    now = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)

    first = seed_demo_heat(db_session, now=now)
    second = seed_demo_heat(db_session, now=now)
    db_session.commit()

    demo_items = list(db_session.scalars(select(Material).where(Material.source == DEMO_SOURCE)))
    assert first.created_count == 36
    assert first.updated_count == 0
    assert second.created_count == 0
    assert second.updated_count == 36
    assert len(demo_items) == 36
    assert {item.upload_platform for item in demo_items} == {
        "抖音",
        "番茄小说",
        "小红书",
        "星河短剧",
    }
    assert len({item.created_at.strftime("%Y-%m") for item in demo_items}) == 6
    assert all(item.title.startswith("【趋势演示】") for item in demo_items)
    assert all(item.storage_path == "" for item in demo_items)
    assert all(item.metadata_json[DEMO_MARKER_KEY]["version"] == 1 for item in demo_items)

    aggregate = client.get("/api/genre-positioning")
    timeline = client.get(
        "/api/genre-positioning/timeline",
        params={"upload_platform": "星河短剧"},
    )
    all_timeline = client.get("/api/genre-positioning/timeline")

    assert aggregate.status_code == 200
    assert "星河短剧" in {
        item["upload_platform"] for item in aggregate.json()["data"]["items"]
    }
    assert timeline.status_code == 200
    assert len({point["genre_module_id"] for point in timeline.json()["data"]["points"]}) == 3
    assert len(timeline.json()["data"]["periods"]) == 3
    assert all_timeline.status_code == 200
    assert len(all_timeline.json()["data"]["periods"]) == 6


def test_demo_heat_removal_only_deletes_fully_marked_demo_rows(db_session: Session) -> None:
    genre = create_genres(db_session)[0]
    seed_demo_heat(db_session, now=datetime(2026, 8, 12, tzinfo=timezone.utc))
    real = Material(
        genre_module_id=genre.id,
        title="真实素材",
        material_type="剧情",
        library_type="material",
        upload_platform="星河短剧",
        platform_heat=88,
        source="用户上传",
    )
    suspicious = Material(
        genre_module_id=genre.id,
        title="只有来源相同但没有标记",
        material_type="剧情",
        library_type="material",
        upload_platform="星河短剧",
        platform_heat=66,
        source=DEMO_SOURCE,
        metadata_json={},
    )
    db_session.add_all([real, suspicious])
    db_session.flush()

    removed = remove_demo_heat(db_session)
    db_session.commit()

    remaining = list(db_session.scalars(select(Material)))
    assert removed == 36
    assert {item.id for item in remaining} == {real.id, suspicious.id}


def test_demo_heat_seed_requires_an_active_material_genre(db_session: Session) -> None:
    with pytest.raises(ValueError, match="没有可用于趋势演示的启用素材题材"):
        seed_demo_heat(db_session, now=datetime(2026, 8, 12, tzinfo=timezone.utc))
