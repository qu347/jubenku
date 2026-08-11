from uuid import uuid4

from fastapi.testclient import TestClient


def create_module(
    client: TestClient,
    *,
    name: str,
    slug: str,
    default_sections: bool = True,
    sort_order: int = 0,
) -> dict:
    response = client.post("/api/genre-modules", json={
        "name": name,
        "slug": slug,
        "icon": "Collection",
        "description": "Sprint 2 测试模块",
        "theme_color": "#FF7A45",
        "sort_order": sort_order,
        "status": "active",
        "visible": True,
        "profile_json": {},
        "create_default_sections": default_sections,
    })
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_section(client: TestClient, module_id: str, key: str, name: str, order: int = 0) -> dict:
    response = client.post(f"/api/genre-modules/{module_id}/sections", json={
        "section_key": key,
        "section_name": name,
        "icon": "Document",
        "sort_order": order,
        "enabled": True,
        "field_schema": [],
        "filter_schema": {},
        "card_schema": {},
    })
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_get_module_by_slug(client: TestClient) -> None:
    create_module(client, name="规则怪谈", slug="rule-horror")
    response = client.get("/api/genre-modules/slug/rule-horror")
    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "rule-horror"
    assert len(response.json()["data"]["sections"]) == 9


def test_missing_slug_returns_404(client: TestClient) -> None:
    response = client.get("/api/genre-modules/slug/not-found")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "genre_not_found"


def test_disabled_module_hidden_from_default_navigation(client: TestClient) -> None:
    module = create_module(client, name="停用题材", slug="disabled-genre")
    assert client.post(f"/api/genre-modules/{module['id']}/disable").status_code == 200
    default_slugs = [item["slug"] for item in client.get("/api/genre-modules").json()["data"]]
    assert "disabled-genre" not in default_slugs


def test_include_inactive_returns_disabled_module(client: TestClient) -> None:
    module = create_module(client, name="停用可查", slug="inactive-query")
    client.post(f"/api/genre-modules/{module['id']}/disable")
    response = client.get("/api/genre-modules?include_inactive=true")
    assert "inactive-query" in [item["slug"] for item in response.json()["data"]]


def test_hidden_module_not_in_navigation(client: TestClient) -> None:
    module = create_module(client, name="隐藏题材", slug="hidden-genre")
    client.patch(f"/api/genre-modules/{module['id']}", json={"visible": False})
    assert "hidden-genre" not in [item["slug"] for item in client.get("/api/genre-modules").json()["data"]]
    all_items = client.get("/api/genre-modules?include_hidden=true").json()["data"]
    assert "hidden-genre" in [item["slug"] for item in all_items]


def test_duplicate_module_and_sections(client: TestClient) -> None:
    module = create_module(client, name="复制题材", slug="copy-genre")
    response = client.post(f"/api/genre-modules/{module['id']}/duplicate")
    assert response.status_code == 200
    duplicate = response.json()["data"]
    assert duplicate["name"] == "复制题材副本"
    assert duplicate["slug"] == "copy-genre-copy"
    assert duplicate["status"] == "inactive"
    assert duplicate["visible"] is False
    sections = client.get(f"/api/genre-modules/{duplicate['id']}/sections?include_disabled=true").json()["data"]
    assert len(sections) == 9


def test_duplicate_module_generates_unique_slug(client: TestClient) -> None:
    module = create_module(client, name="连续复制", slug="repeat-copy")
    first = client.post(f"/api/genre-modules/{module['id']}/duplicate").json()["data"]
    second = client.post(f"/api/genre-modules/{module['id']}/duplicate").json()["data"]
    assert first["slug"] == "repeat-copy-copy"
    assert second["slug"] == "repeat-copy-copy-2"


def test_batch_reorder_modules(client: TestClient) -> None:
    first = create_module(client, name="排序题材甲", slug="order-a", sort_order=0)
    second = create_module(client, name="排序题材乙", slug="order-b", sort_order=1)
    response = client.patch("/api/genre-modules/batch/reorder", json={"items": [
        {"id": first["id"], "sort_order": 5},
        {"id": second["id"], "sort_order": 2},
    ]})
    assert response.status_code == 200
    order = {item["id"]: item["sort_order"] for item in response.json()["data"]}
    assert order[first["id"]] == 5
    assert order[second["id"]] == 2


def test_invalid_module_reorder_rolls_back(client: TestClient) -> None:
    module = create_module(client, name="回滚题材", slug="rollback-genre", sort_order=3)
    response = client.patch("/api/genre-modules/batch/reorder", json={"items": [
        {"id": module["id"], "sort_order": 99},
        {"id": str(uuid4()), "sort_order": 1},
    ]})
    assert response.status_code == 422
    persisted = client.get(f"/api/genre-modules/{module['id']}").json()["data"]
    assert persisted["sort_order"] == 3


def test_same_module_section_key_conflict(client: TestClient) -> None:
    module = create_module(client, name="板块冲突", slug="section-conflict", default_sections=False)
    create_section(client, module["id"], "custom", "自定义一")
    response = client.post(f"/api/genre-modules/{module['id']}/sections", json={
        "section_key": "custom", "section_name": "自定义二", "icon": "Document",
        "sort_order": 1, "enabled": True, "field_schema": [], "filter_schema": {}, "card_schema": {},
    })
    assert response.status_code == 409


def test_different_modules_allow_same_section_key(client: TestClient) -> None:
    first = create_module(client, name="板块题材甲", slug="section-a", default_sections=False)
    second = create_module(client, name="板块题材乙", slug="section-b", default_sections=False)
    assert create_section(client, first["id"], "shared", "共享板块甲")["section_key"] == "shared"
    assert create_section(client, second["id"], "shared", "共享板块乙")["section_key"] == "shared"


def test_disabled_section_filtered_from_detail(client: TestClient) -> None:
    module = create_module(client, name="禁用板块", slug="disabled-section")
    sections = client.get(f"/api/genre-modules/{module['id']}/sections").json()["data"]
    section = sections[0]
    client.post(f"/api/module-sections/{section['id']}/disable")
    detail = client.get("/api/genre-modules/slug/disabled-section").json()["data"]
    assert section["id"] not in [item["id"] for item in detail["sections"]]


def test_include_disabled_returns_disabled_section(client: TestClient) -> None:
    module = create_module(client, name="查询禁用板块", slug="include-disabled")
    section = client.get(f"/api/genre-modules/{module['id']}/sections").json()["data"][0]
    client.post(f"/api/module-sections/{section['id']}/disable")
    detail = client.get("/api/genre-modules/slug/include-disabled?include_disabled=true").json()["data"]
    assert section["id"] in [item["id"] for item in detail["sections"]]


def test_batch_reorder_sections(client: TestClient) -> None:
    module = create_module(client, name="板块排序", slug="section-order", default_sections=False)
    first = create_section(client, module["id"], "first", "第一板块", 0)
    second = create_section(client, module["id"], "second", "第二板块", 1)
    response = client.patch("/api/module-sections/batch/reorder", json={"items": [
        {"id": first["id"], "sort_order": 8},
        {"id": second["id"], "sort_order": 2},
    ]})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [second["id"], first["id"]]


def test_soft_deleted_module_not_returned(client: TestClient) -> None:
    module = create_module(client, name="删除题材", slug="deleted-genre")
    assert client.delete(f"/api/genre-modules/{module['id']}").status_code == 200
    assert client.get(f"/api/genre-modules/{module['id']}").status_code == 404
    assert client.get("/api/genre-modules/slug/deleted-genre").status_code == 404


def test_disabling_last_enabled_section_returns_business_error(client: TestClient) -> None:
    module = create_module(client, name="唯一板块", slug="last-section", default_sections=False)
    section = create_section(client, module["id"], "only", "唯一板块")
    response = client.post(f"/api/module-sections/{section['id']}/disable")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "last_enabled_section"


def test_batch_route_is_not_captured_as_uuid(client: TestClient) -> None:
    response = client.patch("/api/genre-modules/batch/reorder", json={"items": [
        {"id": str(uuid4()), "sort_order": 1}
    ]})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_reorder_ids"
