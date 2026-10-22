from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_character_cards_are_viewed_before_session_completion() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "card_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "card_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小字", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/characters/batch",
        headers=headers,
        json={"content_text": "根、茂", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    client.post(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 2,
            "default_content_types": ["character"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["character"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    assert data["session"]["completed_questions"] == 0
    assert {question["question_stem"] for question in data["questions"]} == {"根", "茂"}
    assert all(question["question_type"] == "character_card" for question in data["questions"])
    assert all(question["question_options"] == [] for question in data["questions"])

    session_id = data["session"]["id"]
    incomplete = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert incomplete.status_code == 409

    first, second = data["questions"]
    first_view = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{first['id']}/viewed",
        headers=headers,
        json={"view_duration_ms": 800},
    )
    assert first_view.status_code == 200
    assert first_view.json()["data"]["progress"]["completed_questions"] == 1
    duplicate_view = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{first['id']}/viewed",
        headers=headers,
        json={"view_duration_ms": 900},
    )
    assert duplicate_view.status_code == 200
    assert duplicate_view.json()["data"]["progress"]["completed_questions"] == 1
    second_view = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{second['id']}/viewed",
        headers=headers,
        json={"view_duration_ms": 700},
    )
    assert second_view.json()["data"]["progress"]["completed_questions"] == 2

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 2


def test_child_learning_full_flow() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "learner_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "learner_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小雨", "nickname": "雨点", "age": 5},
    ).json()["data"]

    poems = [
        ("静夜思", ["床前明月光", "疑是地上霜"]),
        ("春晓", ["春眠不觉晓", "处处闻啼鸟"]),
    ]
    for title, lines in poems:
        response = client.post(
            f"/api/v1/children/{child['id']}/contents",
            headers=headers,
            json={
                "content_type": "poem",
                "title": title,
                "content_text": "，".join(lines),
                "meaning": f"{title}的诗意",
                "difficulty": 1,
                "status": "enabled",
                "detail": {"poem_lines": lines},
            },
        )
        assert response.status_code == 201

    client.post(
        f"/api/v1/children/{child['id']}/rules",
        headers=headers,
        json={
            "question_count": 5,
            "default_content_types": ["poem"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child['id']}/sessions",
        headers=headers,
        json={"selected_content_types": []},
    )
    assert started.status_code == 201
    started_data = started.json()["data"]
    assert started_data["session"]["total_questions"] == 2
    assert len(started_data["questions"]) == 2
    assert "correct_answer" not in started_data["questions"][0]
    assert started_data["questions"][0]["question_type"] == "next_line_choice"

    session_id = started_data["session"]["id"]
    detail = client.get(
        f"/api/v1/children/{child['id']}/sessions/{session_id}", headers=headers
    ).json()["data"]
    first, second = detail["questions"]
    assert "correct_answer" not in first

    invalid = client.post(
        f"/api/v1/children/{child['id']}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": first["id"], "user_answer": "不在选项中的答案"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == 42205

    correct_answers = {"床前明月光": "疑是地上霜", "春眠不觉晓": "处处闻啼鸟"}
    first_answer = next(answer for line, answer in correct_answers.items() if line in first["question_stem"])
    first_wrong_answer = next(option for option in first["question_options"] if option != first_answer)
    second_answer = next(answer for line, answer in correct_answers.items() if line in second["question_stem"])

    wrong = client.post(
        f"/api/v1/children/{child['id']}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": first["id"], "user_answer": first_wrong_answer, "answer_duration_ms": 1200},
    )
    assert wrong.status_code == 200
    assert wrong.json()["data"]["is_correct"] is False

    duplicate = client.post(
        f"/api/v1/children/{child['id']}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": first["id"], "user_answer": first_answer},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40903

    correct = client.post(
        f"/api/v1/children/{child['id']}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": second["id"], "user_answer": second_answer},
    )
    assert correct.json()["data"]["progress"]["accuracy_rate"] == 50

    completed = client.post(
        f"/api/v1/children/{child['id']}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    result = completed.json()["data"]
    assert result["session"]["session_status"] == "completed"
    assert result["session"]["correct_questions"] == 1
    assert len(result["summary"]["need_review_contents"]) == 1


def test_generates_templates_for_all_content_types() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "template_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "template_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小禾", "age": 5},
    ).json()["data"]["id"]

    contents = [
        {
            "content_type": "character",
            "title": "山",
            "content_text": "山峰",
            "pronunciation": "shān",
        },
        {
            "content_type": "classic",
            "title": "三字经",
            "content_text": "人之初",
            "detail": {"sentence_text": "人之初", "next_sentence": "性本善"},
        },
        {
            "content_type": "poem",
            "title": "静夜思",
            "content_text": "床前明月光，疑是地上霜",
            "detail": {"poem_lines": ["床前明月光", "疑是地上霜"]},
        },
        {
            "content_type": "idiom",
            "title": "一心一意",
            "content_text": "专心做事",
            "meaning": "心思专一",
        },
        {
            "content_type": "englishWord",
            "title": "apple",
            "content_text": "apple",
            "meaning": "苹果",
        },
    ]
    for content in contents:
        response = client.post(
            f"/api/v1/children/{child_id}/contents",
            headers=headers,
            json={"difficulty": 1, "status": "enabled", **content},
        )
        assert response.status_code == 201

    content_types = ["character", "classic", "poem", "idiom", "englishWord"]
    rule = client.post(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 5,
            "default_content_types": content_types,
            "allow_child_select_types": True,
            "status": 1,
        },
    )
    assert rule.status_code == 201

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": content_types},
    )
    assert started.status_code == 201
    questions = started.json()["data"]["questions"]
    question_types = {question["content_type"]: question["question_type"] for question in questions}
    assert question_types == {
        "character": "character_card",
        "classic": "next_line_choice",
        "poem": "next_line_choice",
        "idiom": "meaning_choice",
        "englishWord": "translation_choice",
    }