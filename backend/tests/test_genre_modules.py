from fastapi.testclient import TestClient


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


def test_list_genre_modules(client: TestClient) -> None:
    create_module(client, "题材乙", "genre-b")
    create_module(client, "题材甲", "genre-a")
    response = client.get("/api/genre-modules")
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["data"]] == ["genre-b", "genre-a"]


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
    assert len(sections) == 9
    assert [item["section_name"] for item in sections] == [
        "概览", "受众定位", "创作元素", "人物素材", "剧情素材",
        "场景素材", "对白素材", "世界观素材", "参考资料",
    ]
