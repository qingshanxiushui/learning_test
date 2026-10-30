from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup() -> tuple[TestClient, dict[str, str], str]:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "math-parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "math-parent", "password": "123456"},
    )
    token = login.json()["data"]["access_token"]
    headers = _auth(token)
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小明", "age": 6},
    ).json()["data"]["id"]
    return client, headers, child_id


def test_math_settings_upsert_and_get() -> None:
    client, headers, child_id = _setup()

    # 新建孩子时自动生成默认算术设置
    defaults = client.get(f"/api/v1/children/{child_id}/math-settings", headers=headers)
    assert defaults.status_code == 200
    default_data = defaults.json()["data"]
    assert default_data is not None
    assert default_data["min_value"] == 0
    assert default_data["max_value"] == 20
    assert default_data["operators"] == ["add", "subtract"]
    assert default_data["status"] == 1

    payload = {
        "min_value": 1,
        "max_value": 20,
        "operators": ["add", "subtract", "multiply", "divide"],
        "status": 1,
    }
    created = client.put(
        f"/api/v1/children/{child_id}/math-settings", headers=headers, json=payload
    )
    assert created.status_code == 200
    data = created.json()["data"]
    assert data["min_value"] == 1
    assert data["max_value"] == 20
    assert data["operators"] == ["add", "subtract", "multiply", "divide"]
    settings_id = data["id"]

    got = client.get(f"/api/v1/children/{child_id}/math-settings", headers=headers)
    assert got.status_code == 200
    assert got.json()["data"]["id"] == settings_id

    payload["min_value"] = 5
    payload["operators"] = ["add"]
    updated = client.put(
        f"/api/v1/children/{child_id}/math-settings", headers=headers, json=payload
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["id"] == settings_id
    assert updated.json()["data"]["min_value"] == 5
    assert updated.json()["data"]["operators"] == ["add"]


def test_math_settings_invalid() -> None:
    client, headers, child_id = _setup()

    invalid_min_max = client.put(
        f"/api/v1/children/{child_id}/math-settings",
        headers=headers,
        json={"min_value": 20, "max_value": 10, "operators": ["add"], "status": 1},
    )
    assert invalid_min_max.status_code == 422
    assert invalid_min_max.json()["code"] == 42207

    empty_operators = client.put(
        f"/api/v1/children/{child_id}/math-settings",
        headers=headers,
        json={"min_value": 1, "max_value": 10, "operators": [], "status": 1},
    )
    assert empty_operators.status_code == 422
    assert empty_operators.json()["code"] == 42207
