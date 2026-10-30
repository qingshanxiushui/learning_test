from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _setup() -> tuple[TestClient, dict[str, str], str]:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "defaults-parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "defaults-parent", "password": "123456"},
    )
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小默", "age": 6},
    ).json()["data"]["id"]
    return client, headers, child_id


def test_new_child_gets_default_rule() -> None:
    client, headers, child_id = _setup()

    rule = client.get(f"/api/v1/children/{child_id}/rules", headers=headers)
    assert rule.status_code == 200
    data = rule.json()["data"]
    assert data["child_id"] == child_id
    assert data["question_count"] == 5
    assert data["default_content_types"] == [
        "character",
        "classic",
        "poem",
        "idiom",
        "englishWord",
    ]
    assert data["allow_child_select_types"] is True
    assert data["status"] == 1


def test_new_child_gets_default_settings() -> None:
    client, headers, child_id = _setup()

    math_settings = client.get(
        f"/api/v1/children/{child_id}/math-settings", headers=headers
    )
    assert math_settings.status_code == 200
    math_data = math_settings.json()["data"]
    assert math_data["child_id"] == child_id
    assert math_data["min_value"] == 0
    assert math_data["max_value"] == 20
    assert math_data["operators"] == ["add", "subtract"]
    assert math_data["status"] == 1

    pinyin_settings = client.get(
        f"/api/v1/children/{child_id}/pinyin-settings", headers=headers
    )
    assert pinyin_settings.status_code == 200
    pinyin_data = pinyin_settings.json()["data"]
    assert pinyin_data["child_id"] == child_id
    assert pinyin_data["categories"] == ["initial"]
    assert pinyin_data["with_tone"] is False
    assert pinyin_data["status"] == 1


def test_new_child_can_start_session_without_manual_setup() -> None:
    client, headers, child_id = _setup()

    # 默认规则已就绪：即使没有任何已启用内容，也应是「内容不足」而不是「规则不存在」
    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["character"]},
    )
    assert started.status_code == 422
    assert started.json()["code"] == 42204

    # 默认算术设置已就绪：可直接开始算术学习
    math_started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["math"]},
    )
    assert math_started.status_code == 201
    questions = math_started.json()["data"]["questions"]
    assert len(questions) == 5
    assert all(item["content_type"] == "math" for item in questions)


def test_default_rule_is_not_duplicated_per_child() -> None:
    client, headers, child_id = _setup()

    second_child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小默二", "age": 7},
    ).json()["data"]["id"]

    first = client.get(f"/api/v1/children/{child_id}/rules", headers=headers).json()["data"]
    second = client.get(f"/api/v1/children/{second_child_id}/rules", headers=headers).json()["data"]
    assert first["id"] != second["id"]
    assert first["child_id"] == child_id
    assert second["child_id"] == second_child_id

    # 同一孩子重复读取不会产生额外规则
    again = client.get(f"/api/v1/children/{child_id}/rules", headers=headers).json()["data"]
    assert again["id"] == first["id"]
