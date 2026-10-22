from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_batch_upsert_characters() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "character-parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "character-parent", "password": "123456"},
    )
    token = login.json()["data"]["access_token"]
    headers = _auth_header(token)
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "Kid", "nickname": None, "age": 6, "grade_level": None, "avatar_url": None},
    )
    child_id = child.json()["data"]["id"]

    payload = {
        "content_text": "- 根、 茂、 但 、闻 、响\n- 苔 、初、 本 、习、根",
        "pronunciation": "共同发音",
        "meaning": "共同释义",
        "example": "共同示例",
        "difficulty": 2,
        "status": "enabled",
        "sort_order": 10,
        "detail": {"source": "textbook"},
    }
    created = client.post(
        f"/api/v1/children/{child_id}/contents/characters/batch",
        headers=headers,
        json=payload,
    )

    assert created.status_code == 201
    created_data = created.json()["data"]
    assert created_data["created_count"] == 9
    assert created_data["updated_count"] == 0
    assert [item["title"] for item in created_data["list"]] == list("根茂但闻响苔初本习")
    assert all(item["title"] == item["content_text"] for item in created_data["list"])
    assert all(item["meaning"] == "共同释义" for item in created_data["list"])
    ids = {item["title"]: item["id"] for item in created_data["list"]}

    payload["meaning"] = "覆盖释义"
    updated = client.post(
        f"/api/v1/children/{child_id}/contents/characters/batch",
        headers=headers,
        json=payload,
    )

    assert updated.status_code == 201
    updated_data = updated.json()["data"]
    assert updated_data["created_count"] == 0
    assert updated_data["updated_count"] == 9
    assert {item["title"]: item["id"] for item in updated_data["list"]} == ids
    assert all(item["meaning"] == "覆盖释义" for item in updated_data["list"])


def test_parent_full_flow() -> None:
    client = TestClient(app)

    create_parent = client.post(
        "/api/v1/parents",
        json={"account_name": "parent001", "display_name": "Parent", "password": "123456"},
    )
    assert create_parent.status_code == 201
    assert create_parent.json()["code"] == 0

    login = client.post("/api/v1/auth/login", json={"account_name": "parent001", "password": "123456"})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    me = client.get("/api/v1/auth/me", headers=_auth_header(token))
    assert me.status_code == 200
    assert me.json()["data"]["account_name"] == "parent001"

    child_resp = client.post(
        "/api/v1/children",
        json={"name": "Kid", "nickname": "K", "age": 5, "grade_level": "K", "avatar_url": None},
        headers=_auth_header(token),
    )
    assert child_resp.status_code == 201
    child_id = child_resp.json()["data"]["id"]

    list_children = client.get("/api/v1/children", headers=_auth_header(token))
    assert list_children.status_code == 200
    assert list_children.json()["data"]["pagination"]["total"] == 1

    create_content = client.post(
        f"/api/v1/children/{child_id}/contents",
        headers=_auth_header(token),
        json={
            "content_type": "poem",
            "title": "Quiet Night Thought",
            "content_text": "line1 line2",
            "pronunciation": None,
            "meaning": "desc",
            "example": None,
            "difficulty": 1,
            "status": "enabled",
            "sort_order": 0,
            "detail": {"author": "Li Bai"},
        },
    )
    assert create_content.status_code == 201
    content_id = create_content.json()["data"]["id"]

    list_content = client.get(f"/api/v1/children/{child_id}/contents", headers=_auth_header(token))
    assert list_content.status_code == 200
    assert list_content.json()["data"]["pagination"]["total"] == 1

    patch_content = client.patch(
        f"/api/v1/children/{child_id}/contents/{content_id}/status",
        headers=_auth_header(token),
        json={"status": "disabled"},
    )
    assert patch_content.status_code == 200
    assert patch_content.json()["data"]["status"] == "disabled"

    create_rule = client.post(
        f"/api/v1/children/{child_id}/rules",
        headers=_auth_header(token),
        json={"question_count": 5, "default_content_types": ["poem"], "allow_child_select_types": True, "status": 1},
    )
    assert create_rule.status_code == 201

    get_rule = client.get(f"/api/v1/children/{child_id}/rules", headers=_auth_header(token))
    assert get_rule.status_code == 200
    assert get_rule.json()["data"]["question_count"] == 5

    # Seed session files to verify parent-side session and stats queries.
    data_dir = Path(settings.data_dir) / "sessions"
    data_dir.mkdir(parents=True, exist_ok=True)

    session_id = "session-1"
    question_id = "question-1"
    (data_dir / "learning_sessions.json").write_text(
        json.dumps(
            [
                {
                    "id": session_id,
                    "child_id": child_id,
                    "selected_content_types": ["poem"],
                    "total_questions": 1,
                    "answered_questions": 1,
                    "correct_questions": 0,
                    "accuracy_rate": 0,
                    "session_status": "completed",
                    "started_at": "2026-08-20T10:00:00Z",
                    "finished_at": "2026-08-20T10:01:00Z",
                    "created_at": "2026-08-20T10:00:00Z",
                    "updated_at": "2026-08-20T10:01:00Z",
                    "is_deleted": 0,
                    "deleted_at": None,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data_dir / "session_questions.json").write_text(
        json.dumps(
            [
                {
                    "id": question_id,
                    "session_id": session_id,
                    "content_id": content_id,
                    "content_type": "poem",
                    "question_type": "next_line_choice",
                    "question_stem": "next line?",
                    "question_options": ["a", "b", "c"],
                    "correct_answer": "a",
                    "answer_explanation": "explain",
                    "question_order": 1,
                    "content_snapshot": {"child_id": child_id},
                    "created_at": "2026-08-20T10:00:00Z",
                    "updated_at": "2026-08-20T10:00:00Z",
                    "is_deleted": 0,
                    "deleted_at": None,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data_dir / "answer_records.json").write_text(
        json.dumps(
            [
                {
                    "id": "answer-1",
                    "session_question_id": question_id,
                    "session_id": session_id,
                    "child_id": child_id,
                    "user_answer": "b",
                    "correct_answer": "a",
                    "is_correct": 0,
                    "answer_duration_ms": 1000,
                    "answered_at": "2026-08-20T10:00:30Z",
                    "created_at": "2026-08-20T10:00:30Z",
                    "updated_at": "2026-08-20T10:00:30Z",
                    "is_deleted": 0,
                    "deleted_at": None,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    sessions = client.get(f"/api/v1/children/{child_id}/sessions", headers=_auth_header(token))
    assert sessions.status_code == 200
    assert sessions.json()["data"]["pagination"]["total"] == 1

    session_detail = client.get(f"/api/v1/children/{child_id}/sessions/{session_id}/result", headers=_auth_header(token))
    assert session_detail.status_code == 200
    assert len(session_detail.json()["data"]["answers"]) == 1

    stats_overview = client.get(f"/api/v1/children/{child_id}/stats/overview", headers=_auth_header(token))
    assert stats_overview.status_code == 200
    assert stats_overview.json()["data"]["total_sessions"] == 1

    weak = client.get(f"/api/v1/children/{child_id}/stats/weak-contents", headers=_auth_header(token))
    assert weak.status_code == 200
    assert weak.json()["data"][0]["content_id"] == content_id


def test_auth_required() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/children")
    assert r.status_code == 401
    assert r.json()["code"] == 40101
