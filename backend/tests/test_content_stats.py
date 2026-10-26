from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _question(qid: str, cid: str, order: int) -> dict:
    return {
        "id": qid,
        "session_id": "s1",
        "content_id": cid,
        "content_type": "character",
        "question_type": "character_card",
        "question_stem": "字",
        "question_options": [],
        "correct_answer": "",
        "answer_explanation": "",
        "question_order": order,
        "content_snapshot": {},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "deleted_at": None,
        "is_deleted": 0,
        "viewed_at": "2026-01-01T00:00:00Z",
    }


def test_content_learn_stats_and_sorting() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "stats-parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "stats-parent", "password": "123456"},
    )
    headers = _auth(login.json()["data"]["access_token"])
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小统", "age": 6},
    ).json()["data"]["id"]

    imported = client.post(
        f"/api/v1/children/{child_id}/contents/characters/batch",
        headers=headers,
        json={"content_text": "根、茂、叶", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    ids = {item["title"]: item["id"] for item in imported.json()["data"]["list"]}

    data_dir = Path(settings.data_dir) / "sessions"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "session_questions.json").write_text(
        json.dumps(
            [
                _question("q1", ids["根"], 1),
                _question("q2", ids["根"], 2),
                _question("q3", ids["根"], 3),
                _question("q4", ids["茂"], 1),
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    desc = client.get(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        params={"sort_by": "learn_count", "sort_order": "desc", "page_size": 10},
    )
    assert desc.status_code == 200
    desc_list = desc.json()["data"]["list"]
    stats = {item["title"]: item for item in desc_list}
    assert stats["根"]["learn_count"] == 3
    assert stats["茂"]["learn_count"] == 1
    assert stats["叶"]["learn_count"] == 0
    assert stats["根"]["error_count"] == 0
    assert stats["根"]["error_rate"] == 0
    assert [item["title"] for item in desc_list] == ["根", "茂", "叶"]

    asc = client.get(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        params={"sort_by": "learn_count", "sort_order": "asc", "page_size": 10},
    )
    assert asc.status_code == 200
    assert [item["title"] for item in asc.json()["data"]["list"]] == ["叶", "茂", "根"]


def test_clear_content_stats() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "clear-parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "clear-parent", "password": "123456"},
    )
    headers = _auth(login.json()["data"]["access_token"])
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小清", "age": 6},
    ).json()["data"]["id"]

    imported = client.post(
        f"/api/v1/children/{child_id}/contents/characters/batch",
        headers=headers,
        json={"content_text": "根、茂、叶", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    ids = {item["title"]: item["id"] for item in imported.json()["data"]["list"]}

    data_dir = Path(settings.data_dir) / "sessions"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "session_questions.json").write_text(
        json.dumps(
            [
                _question("q1", ids["根"], 1),
                _question("q2", ids["根"], 2),
                _question("q3", ids["根"], 3),
                _question("q4", ids["茂"], 1),
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    before = client.get(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        params={"page_size": 10},
    )
    assert {item["title"]: item["learn_count"] for item in before.json()["data"]["list"]} == {
        "根": 3,
        "茂": 1,
        "叶": 0,
    }

    cleared = client.delete(
        f"/api/v1/children/{child_id}/stats",
        headers=headers,
        params={"content_type": "character"},
    )
    assert cleared.status_code == 200
    assert cleared.json()["data"]["cleared"] == 4

    after = client.get(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        params={"page_size": 10},
    )
    assert {item["title"]: item["learn_count"] for item in after.json()["data"]["list"]} == {
        "根": 0,
        "茂": 0,
        "叶": 0,
    }
