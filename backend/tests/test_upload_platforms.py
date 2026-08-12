def test_create_upload_platform_persists_for_later_requests(client) -> None:
    created = client.post("/api/upload-platforms", json={"name": "  星河阅读  "})

    assert created.status_code == 201
    assert created.json()["data"] == {
        "id": created.json()["data"]["id"],
        "name": "星河阅读",
        "is_system": False,
    }

    listed = client.get("/api/upload-platforms")
    assert listed.status_code == 200
    assert "星河阅读" in [item["name"] for item in listed.json()["data"]]


def test_create_upload_platform_rejects_nfkc_casefold_duplicate(client) -> None:
    assert client.post("/api/upload-platforms", json={"name": "ＳＴＡＲ"}).status_code == 201

    duplicate = client.post("/api/upload-platforms", json={"name": "star"})

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "upload_platform_exists"


def test_create_upload_platform_rejects_blank_name(client) -> None:
    response = client.post("/api/upload-platforms", json={"name": "　 "})

    assert response.status_code == 422


def test_upload_platform_list_keeps_system_platforms_before_custom_platforms(client, db_session) -> None:
    created = client.post("/api/upload-platforms", json={"name": "星河阅读"})
    assert created.status_code == 201

    from app.models.upload_platform import UploadPlatform

    db_session.add_all(
        [
            UploadPlatform(name="番茄小说", normalized_name="番茄小说", is_system=True, sort_order=0),
            UploadPlatform(name="七猫", normalized_name="七猫", is_system=True, sort_order=1),
            UploadPlatform(name="起点中文网", normalized_name="起点中文网", is_system=True, sort_order=2),
        ]
    )
    db_session.commit()
    listed = client.get("/api/upload-platforms")

    assert listed.status_code == 200
    names = [item["name"] for item in listed.json()["data"]]
    assert names[:3] == ["番茄小说", "七猫", "起点中文网"]
    assert names[-1] == "星河阅读"
