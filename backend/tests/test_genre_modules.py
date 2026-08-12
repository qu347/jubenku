import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import GenreModule, Material


def module_payload(name: str = "测试幻想", slug: str = "test-fantasy") -> dict:
    return {
        "name": name,
        "slug": slug,
        "icon": "MagicStick",
        "description": "Sprint 1 接口测试题材。",
        "theme_color": "#8b5cf6",
        "sort_order": 3,
        "status": "active",
        "visible": True,
        "profile_json": {"audience": "测试用户"},
        "create_default_sections": False,
    }


def create_module(client: TestClient, name: str = "测试幻想", slug: str = "test-fantasy") -> dict:
    response = client.post("/api/genre-modules", json=module_payload(name, slug))
    assert response.status_code == 201
    return response.json()["data"]


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_create_genre_module(client: TestClient) -> None:
    created = create_module(client)
    assert created["name"] == "测试幻想"
    assert created["slug"] == "test-fantasy"
    assert created["section_count"] == 0


def test_duplicate_slug_returns_conflict(client: TestClient) -> None:
    create_module(client)
    response = client.post("/api/genre-modules", json=module_payload("另一个题材", "test-fantasy"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "genre_conflict"


def test_update_genre_module(client: TestClient) -> None:
    created = create_module(client)
    response = client.patch(
        f"/api/genre-modules/{created['id']}",
        json={"name": "测试幻想·修订", "theme_color": "#112233", "visible": False},
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "测试幻想·修订"
    assert response.json()["data"]["theme_color"] == "#112233"
    assert response.json()["data"]["visible"] is False
    assert response.json()["data"]["material_visible"] is False
    assert response.json()["data"]["script_visible"] is False
    assert client.get(
        "/api/genre-modules", params={"library_type": "material"}
    ).json()["data"] == []


def test_list_genre_modules(client: TestClient) -> None:
    create_module(client, "题材乙", "genre-b")
    create_module(client, "题材甲", "genre-a")
    response = client.get("/api/genre-modules")
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["data"]] == ["genre-b", "genre-a"]


def test_delete_empty_genre_module_permanently(
    client: TestClient,
    db_session: Session,
) -> None:
    created = create_module(client)

    response = client.delete(f"/api/genre-modules/{created['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "题材模块已永久删除"
    assert db_session.get(GenreModule, created["id"]) is None
    assert client.get(f"/api/genre-modules/{created['id']}").status_code == 404


@pytest.mark.parametrize(
    ("library_type", "expected_details"),
    [
        ("material", {"material_count": 1, "script_count": 0}),
        ("script", {"material_count": 0, "script_count": 1}),
    ],
)
def test_delete_genre_module_with_content_is_blocked(
    client: TestClient,
    db_session: Session,
    library_type: str,
    expected_details: dict[str, int],
) -> None:
    created = create_module(client)
    db_session.add(
        Material(
            genre_module_id=created["id"],
            library_type=library_type,
            title="关联内容",
            material_type="剧情",
        )
    )
    db_session.commit()

    response = client.delete(f"/api/genre-modules/{created['id']}")

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "genre_module_not_empty",
        "details": expected_details,
    }
    assert db_session.get(GenreModule, created["id"]) is not None


def test_genre_navigation_is_filtered_and_sorted_per_library(client: TestClient) -> None:
    western = create_module(client, "西方奇幻", "western-fantasy")
    xianxia = create_module(client, "东方仙侠", "eastern-xianxia")

    assert client.patch(
        f"/api/genre-modules/{western['id']}",
        json={
            "material_visible": True,
            "script_visible": False,
            "material_sort_order": 1,
            "script_sort_order": 0,
        },
    ).status_code == 200
    assert client.patch(
        f"/api/genre-modules/{xianxia['id']}",
        json={
            "material_visible": True,
            "script_visible": True,
            "material_sort_order": 0,
            "script_sort_order": 3,
        },
    ).status_code == 200

    materials = client.get("/api/genre-modules", params={"library_type": "material"})
    scripts = client.get("/api/genre-modules", params={"library_type": "script"})

    assert materials.status_code == 200
    assert scripts.status_code == 200
    assert [item["slug"] for item in materials.json()["data"]] == [
        "eastern-xianxia",
        "western-fantasy",
    ]
    assert [item["slug"] for item in scripts.json()["data"]] == ["eastern-xianxia"]
    assert client.get(
        "/api/genre-modules", params={"library_type": "unknown"}
    ).status_code == 422


def test_reorder_genre_modules_only_updates_selected_library(client: TestClient) -> None:
    first = create_module(client, "题材甲", "genre-a")
    second = create_module(client, "题材乙", "genre-b")

    response = client.patch(
        "/api/genre-modules/batch/reorder",
        params={"library_type": "script"},
        json={
            "items": [
                {"id": first["id"], "sort_order": 8},
                {"id": second["id"], "sort_order": 2},
            ]
        },
    )

    assert response.status_code == 200
    modules = {item["id"]: item for item in response.json()["data"]}
    assert modules[first["id"]]["script_sort_order"] == 8
    assert modules[second["id"]]["script_sort_order"] == 2
    assert modules[first["id"]]["material_sort_order"] == 3
    assert modules[second["id"]]["material_sort_order"] == 3


def test_create_module_section(client: TestClient) -> None:
    module = create_module(client)
    response = client.post(
        f"/api/genre-modules/{module['id']}/sections",
        json={
            "section_key": "characters",
            "section_name": "人物素材",
            "icon": "User",
            "sort_order": 1,
            "enabled": True,
            "field_schema": [
                {"key": "name", "label": "姓名", "type": "text", "required": True}
            ],
            "filter_schema": {},
            "card_schema": {},
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["section_key"] == "characters"
    assert response.json()["data"]["field_schema"][0]["key"] == "name"


def test_list_module_sections(client: TestClient) -> None:
    payload = module_payload()
    payload["create_default_sections"] = True
    module = client.post("/api/genre-modules", json=payload).json()["data"]
    response = client.get(f"/api/genre-modules/{module['id']}/sections")
    assert response.status_code == 200
    sections = response.json()["data"]
    assert len(sections) == 1
    assert [item["section_name"] for item in sections] == ["标题"]
