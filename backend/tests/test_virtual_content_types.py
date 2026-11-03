from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models import CONTENT_FILE_TYPES, VIRTUAL_CONTENT_TYPES


def _setup_child(client: TestClient, account: str) -> tuple[dict[str, str], str]:
    client.post(
        "/api/v1/parents",
        json={"account_name": account, "display_name": "Parent", "password": "123456"},
    )
    login = client.post("/api/v1/auth/login", json={"account_name": account, "password": "123456"})
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "Kid", "nickname": None, "age": 6, "grade_level": None, "avatar_url": None},
    )
    return headers, child.json()["data"]["id"]


def test_virtual_content_types_have_no_content_file() -> None:
    assert set(CONTENT_FILE_TYPES) | set(VIRTUAL_CONTENT_TYPES) == {
        "character",
        "classic",
        "poem",
        "idiom",
        "englishWord",
        "math",
        "pinyin",
    }
    assert not set(CONTENT_FILE_TYPES) & set(VIRTUAL_CONTENT_TYPES)


def test_listing_virtual_content_type_does_not_create_file() -> None:
    client = TestClient(app)
    headers, child_id = _setup_child(client, "virtual-list-parent")
    contents_dir = Path(settings.data_dir) / "contents"

    for virtual_type in VIRTUAL_CONTENT_TYPES:
        resp = client.get(
            f"/api/v1/children/{child_id}/contents",
            headers=headers,
            params={"content_type": virtual_type},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["pagination"]["total"] == 0
        assert not (contents_dir / f"{virtual_type}.json").exists(), (
            f"listing content_type={virtual_type} must not create contents/{virtual_type}.json"
        )


def test_creating_virtual_content_type_is_rejected() -> None:
    client = TestClient(app)
    headers, child_id = _setup_child(client, "virtual-create-parent")
    contents_dir = Path(settings.data_dir) / "contents"

    for virtual_type in VIRTUAL_CONTENT_TYPES:
        resp = client.post(
            f"/api/v1/children/{child_id}/contents",
            headers=headers,
            json={
                "content_type": virtual_type,
                "title": "虚拟类型",
                "content_text": "不应写入",
            },
        )
        assert resp.status_code == 422
        assert not (contents_dir / f"{virtual_type}.json").exists()
