from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import GenreModule, Material


@pytest.fixture()
def genre_module(db_session: Session) -> GenreModule:
    module = GenreModule(name="素材定位测试", slug="material-positioning")
    db_session.add(module)
    db_session.commit()
    return module


@pytest.fixture()
def markdown_upload() -> tuple[str, bytes, str]:
    return ("positioning.md", b"# Material positioning\n", "text/markdown")


@pytest.fixture()
def create_material(db_session: Session):
    """Create persisted materials so API tests exercise the real SQL query."""

    def factory(
        *,
        genre: GenreModule | None = None,
        platform: str | None = "番茄小说",
        heat: float | None = 80,
        library_type: str = "material",
        deleted: bool = False,
    ) -> Material:
        if genre is None:
            suffix = uuid4().hex
            genre = GenreModule(name=f"定位题材-{suffix}", slug=f"positioning-{suffix}")
            db_session.add(genre)
            db_session.flush()
        material = Material(
            genre_module_id=genre.id,
            title=f"定位素材-{uuid4().hex}",
            material_type="参考资料",
            library_type=library_type,
            upload_platform=platform,
            platform_heat=heat,
            deleted_at=datetime.now(timezone.utc) if deleted else None,
        )
        db_session.add(material)
        db_session.commit()
        return material

    return factory


def test_positioning_groups_materials_by_genre_and_platform(client, create_material) -> None:
    genre = create_material(platform="番茄小说", heat=80).genre_module
    create_material(genre=genre, platform="番茄小说", heat=90)
    create_material(genre=genre, platform="  番茄小说  ", heat=85)

    response = client.get("/api/genre-positioning")

    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{
        "genre_module_id": genre.id,
        "genre_name": genre.name,
        "theme_color": genre.theme_color,
        "upload_platform": "番茄小说",
        "average_heat": 85.0,
        "material_count": 3,
        "latest_updated_at": response.json()["data"]["items"][0]["latest_updated_at"],
    }]


def test_positioning_excludes_non_active_or_incomplete_materials(
    client, create_material, db_session: Session
) -> None:
    included = create_material(platform="番茄小说", heat=70)
    genre = included.genre_module
    create_material(genre=genre, platform="番茄小说", heat=99, library_type="script")
    create_material(genre=genre, platform="番茄小说", heat=99, deleted=True)
    create_material(genre=genre, platform=None, heat=None)
    deleted_genre_material = create_material(platform="起点中文网", heat=99)
    deleted_genre_material.genre_module.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.get("/api/genre-positioning")

    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{
        "genre_module_id": genre.id,
        "genre_name": genre.name,
        "theme_color": genre.theme_color,
        "upload_platform": "番茄小说",
        "average_heat": 70.0,
        "material_count": 1,
        "latest_updated_at": response.json()["data"]["items"][0]["latest_updated_at"],
    }]


def test_positioning_keeps_genre_platform_pairs_separate_and_uses_latest_spelling(
    client, create_material, db_session: Session
) -> None:
    first = create_material(platform="Tomato", heat=75)
    other_genre = create_material(platform="番茄小说", heat=95).genre_module
    newest = create_material(genre=first.genre_module, platform="  TOMATO  ", heat=85)
    newest.updated_at = first.updated_at + timedelta(seconds=1)
    db_session.commit()

    response = client.get("/api/genre-positioning")

    assert response.status_code == 200
    assert [(item["genre_module_id"], item["upload_platform"], item["average_heat"]) for item in response.json()["data"]["items"]] == [
        (other_genre.id, "番茄小说", 95.0),
        (first.genre_module.id, "TOMATO", 80.0),
    ]


def test_positioning_filters_using_aggregate_average_and_rejects_invalid_range(
    client, create_material
) -> None:
    genre = create_material(platform="番茄小说", heat=40).genre_module
    create_material(genre=genre, platform="番茄小说", heat=80)
    create_material(genre=genre, platform="起点中文网", heat=90)

    filtered = client.get("/api/genre-positioning", params={"heat_min": 70})
    invalid = client.get("/api/genre-positioning", params={"heat_min": 80, "heat_max": 70})

    assert [item["upload_platform"] for item in filtered.json()["data"]["items"]] == ["起点中文网"]
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_heat_range"


def test_material_list_filters_upload_platform_case_insensitively(client, create_material) -> None:
    matching = create_material(platform="  番茄小说  ", heat=80)
    create_material(genre=matching.genre_module, platform="起点中文网", heat=80)

    response = client.get("/api/materials", params={"upload_platform": "番茄小说"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]["items"]] == [matching.id]


def test_positioning_reflects_material_patch_and_delete_immediately(client, create_material) -> None:
    first = create_material(platform="番茄小说", heat=60)
    second = create_material(genre=first.genre_module, platform="番茄小说", heat=80)

    updated = client.patch(f"/api/materials/{first.id}", json={"platform_heat": 100})
    after_update = client.get("/api/genre-positioning")
    deleted = client.delete(f"/api/materials/{first.id}")
    after_delete = client.get("/api/genre-positioning")

    assert updated.status_code == 200
    assert after_update.json()["data"]["items"][0]["average_heat"] == 90.0
    assert deleted.status_code == 200
    assert after_delete.json()["data"]["items"][0]["material_count"] == 1
    assert after_delete.json()["data"]["items"][0]["average_heat"] == 80.0


def test_material_upload_requires_platform_metadata(
    client: TestClient,
    genre_module: GenreModule,
    markdown_upload: tuple[str, bytes, str],
) -> None:
    response = client.post(
        "/api/materials/upload",
        data={"library_type": "material", "genre_module_id": genre_module.id},
        files={"files": markdown_upload},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "material_platform_required"


@pytest.mark.parametrize("heat", [0, 100])
def test_material_upload_accepts_heat_boundaries(
    client: TestClient,
    genre_module: GenreModule,
    markdown_upload: tuple[str, bytes, str],
    heat: int,
) -> None:
    response = client.post(
        "/api/materials/upload",
        data={
            "library_type": "material",
            "genre_module_id": genre_module.id,
            "upload_platform": "  番茄小说  ",
            "platform_heat": str(heat),
        },
        files={"files": markdown_upload},
    )

    assert response.status_code == 200
    item = response.json()["data"]["materials"][0]
    assert item["upload_platform"] == "番茄小说"
    assert item["platform_heat"] == heat


def test_script_upload_does_not_require_platform_metadata(
    client: TestClient,
    genre_module: GenreModule,
    markdown_upload: tuple[str, bytes, str],
) -> None:
    response = client.post(
        "/api/materials/upload",
        data={"library_type": "script", "genre_module_id": genre_module.id},
        files={"files": markdown_upload},
    )

    assert response.status_code == 200
    assert response.json()["data"]["materials"][0]["upload_platform"] is None


def test_material_update_normalizes_platform_and_keeps_omitted_heat(
    client: TestClient,
    genre_module: GenreModule,
    markdown_upload: tuple[str, bytes, str],
) -> None:
    created = client.post(
        "/api/materials/upload",
        data={
            "library_type": "material",
            "genre_module_id": genre_module.id,
            "upload_platform": "番茄小说",
            "platform_heat": "75",
        },
        files={"files": markdown_upload},
    ).json()["data"]["materials"][0]

    response = client.patch(
        f"/api/materials/{created['id']}",
        json={"upload_platform": "  起点中文网  "},
    )

    assert response.status_code == 200
    assert response.json()["data"]["upload_platform"] == "起点中文网"
    assert response.json()["data"]["platform_heat"] == 75


def test_legacy_material_update_keeps_empty_platform_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    legacy = Material(
        title="旧素材",
        material_type="legacy",
    )
    db_session.add(legacy)
    db_session.commit()

    response = client.patch(f"/api/materials/{legacy.id}", json={"title": "旧素材更新"})

    assert response.status_code == 200
    assert response.json()["data"]["upload_platform"] is None
    assert response.json()["data"]["platform_heat"] is None


def test_material_update_rejects_incomplete_platform_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    legacy = Material(
        title="旧素材",
        material_type="legacy",
    )
    db_session.add(legacy)
    db_session.commit()

    response = client.patch(f"/api/materials/{legacy.id}", json={"upload_platform": "番茄小说"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "incomplete_platform_metadata"
