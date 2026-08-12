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
