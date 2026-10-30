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
    client.put(
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


def test_classic_cards_are_viewed_before_session_completion() -> None:
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
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小经", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/classics/batch",
        headers=headers,
        json={
            "content_text": (
                "人之初，性本善。性相近，习相远。\n"
                "苟不教，性乃迁。教之道，贵以专。\n"
                "昔孟母，择邻处。子不学，断机杼。\n"
                "窦燕山，有义方。教五子，名俱扬。"
            ),
            "difficulty": 1,
            "status": "enabled",
        },
    )
    assert imported.status_code == 201
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 2,
            "default_content_types": ["classic"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["classic"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    assert data["session"]["completed_questions"] == 0
    assert {question["question_stem"] for question in data["questions"]} == {
        "人之初，性本善。性相近，习相远。\n苟不教，性乃迁。教之道，贵以专。",
        "昔孟母，择邻处。子不学，断机杼。\n窦燕山，有义方。教五子，名俱扬。",
    }
    assert all(question["question_type"] == "classic_card" for question in data["questions"])
    assert all(question["question_options"] == [] for question in data["questions"])

    session_id = data["session"]["id"]
    incomplete = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert incomplete.status_code == 409

    for question in data["questions"]:
        viewed = client.post(
            f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{question['id']}/viewed",
            headers=headers,
            json={"view_duration_ms": 700},
        )
        assert viewed.status_code == 200

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 2


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
    rule = client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 5,
            "default_content_types": content_types,
            "allow_child_select_types": True,
            "status": 1,
        },
    )
    assert rule.status_code == 200

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
        "classic": "classic_card",
        "poem": "poem_card",
        "idiom": "idiom_card",
        "englishWord": "english_word_card",
    }


def test_poem_is_viewed_as_card() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "poem_card_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "poem_card_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小诗", "age": 6},
    ).json()["data"]["id"]
    client.post(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        json={
            "content_type": "poem",
            "title": "静夜思",
            "content_text": "床前明月光，疑是地上霜。",
            "difficulty": 1,
            "status": "enabled",
            "detail": {"poem_lines": ["床前明月光", "疑是地上霜"], "dynasty": "唐", "author": "李白"},
        },
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 1,
            "default_content_types": ["poem"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["poem"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    question = data["questions"][0]
    assert question["question_type"] == "poem_card"
    assert question["question_stem"] == "《静夜思》唐·李白\n床前明月光\n疑是地上霜"
    assert question["question_options"] == []

    session_id = data["session"]["id"]
    viewed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{question['id']}/viewed",
        headers=headers,
        json={"view_duration_ms": 800},
    )
    assert viewed.status_code == 200
    assert viewed.json()["data"]["progress"]["completed_questions"] == 1

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 1


def test_idiom_is_viewed_as_card() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "idiom_card_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "idiom_card_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小成", "age": 6},
    ).json()["data"]["id"]
    client.post(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        json={
            "content_type": "idiom",
            "title": "地大物博",
            "content_text": "地大物博",
            "difficulty": 1,
            "status": "enabled",
        },
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 1,
            "default_content_types": ["idiom"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["idiom"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    question = data["questions"][0]
    assert question["question_type"] == "idiom_card"
    assert question["question_stem"] == "地大物博"
    assert question["question_options"] == []

    session_id = data["session"]["id"]
    viewed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{question['id']}/viewed",
        headers=headers,
        json={"view_duration_ms": 800},
    )
    assert viewed.status_code == 200
    assert viewed.json()["data"]["progress"]["completed_questions"] == 1

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 1


def test_pinyin_is_viewed_as_card() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "pinyin_card_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "pinyin_card_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小拼", "age": 6},
    ).json()["data"]["id"]
    client.put(
        f"/api/v1/children/{child_id}/pinyin-settings",
        headers=headers,
        json={"categories": ["initial"], "with_tone": False, "status": 1},
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 3,
            "default_content_types": ["pinyin"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["pinyin"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    questions = data["questions"]
    assert len(questions) == 3
    assert all(q["question_type"] == "pinyin_card" for q in questions)
    assert all(q["content_type"] == "pinyin" for q in questions)
    assert all(q["question_options"] == [] for q in questions)
    initials = set("b p m f d t n l g k h j q x zh ch sh r z c s y w".split())
    assert all(q["question_stem"] in initials for q in questions)

    session_id = data["session"]["id"]
    for question in questions:
        viewed = client.post(
            f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{question['id']}/viewed",
            headers=headers,
            json={"view_duration_ms": 700},
        )
        assert viewed.status_code == 200

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 3


def test_card_questions_have_pinyin_annotation() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "annotation_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "annotation_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小注", "age": 6},
    ).json()["data"]["id"]
    client.post(
        f"/api/v1/children/{child_id}/contents",
        headers=headers,
        json={
            "content_type": "idiom",
            "title": "地大物博",
            "content_text": "地大物博",
            "difficulty": 1,
            "status": "enabled",
        },
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 1,
            "default_content_types": ["idiom"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["idiom"]},
    )
    assert started.status_code == 201
    question = started.json()["data"]["questions"][0]
    assert question["question_stem"] == "地大物博"
    assert question["question_pinyin"] == ["dì", "dà", "wù", "bó"]


def test_pinyin_with_tone_marks() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "pinyin_tone_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "pinyin_tone_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小调", "age": 6},
    ).json()["data"]["id"]
    client.put(
        f"/api/v1/children/{child_id}/pinyin-settings",
        headers=headers,
        json={"categories": ["single_final"], "with_tone": True, "status": 1},
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 6,
            "default_content_types": ["pinyin"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["pinyin"]},
    )
    assert started.status_code == 201
    stems = {q["question_stem"] for q in started.json()["data"]["questions"]}
    assert len(stems) == 6
    # 单韵母带声调：不应出现无调号的原始字母
    assert all(s not in {"a", "o", "e", "i", "u", "ü"} for s in stems)


def test_english_words_are_viewed_as_cards() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "english_parent", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "english_parent", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小英", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/english/batch",
        headers=headers,
        json={"content_text": "apple\nbanana", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 2,
            "default_content_types": ["englishWord"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["englishWord"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    assert {question["question_stem"] for question in data["questions"]} == {"apple", "banana"}
    assert all(question["question_type"] == "english_word_card" for question in data["questions"])
    assert all(question["question_options"] == [] for question in data["questions"])

    session_id = data["session"]["id"]
    for question in data["questions"]:
        viewed = client.post(
            f"/api/v1/children/{child_id}/sessions/{session_id}/questions/{question['id']}/viewed",
            headers=headers,
            json={"view_duration_ms": 600},
        )
        assert viewed.status_code == 200

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 0
    assert completed.json()["data"]["session"]["completed_questions"] == 2


def _parse_math_answer(stem: str) -> int:
    expr = stem.rsplit(" = ?", 1)[0]
    if " + " in expr:
        a, b = expr.split(" + ")
        return int(a) + int(b)
    if " - " in expr:
        a, b = expr.split(" - ")
        return int(a) - int(b)
    if " × " in expr:
        a, b = expr.split(" × ")
        return int(a) * int(b)
    if " ÷ " in expr:
        a, b = expr.split(" ÷ ")
        return int(a) // int(b)
    raise AssertionError(f"unrecognized stem: {stem}")


def test_math_session_generates_questions_and_judges_answer() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "math_learner", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "math_learner", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小算", "age": 6},
    ).json()["data"]["id"]
    client.put(
        f"/api/v1/children/{child_id}/math-settings",
        headers=headers,
        json={
            "min_value": 1,
            "max_value": 10,
            "operators": ["add", "subtract", "multiply", "divide"],
            "status": 1,
        },
    )
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 5,
            "default_content_types": ["math"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["math"]},
    )
    assert started.status_code == 201
    data = started.json()["data"]
    assert data["session"]["total_questions"] == 5
    questions = data["questions"]
    assert len(questions) == 5
    assert all(q["question_type"] == "math_arithmetic" for q in questions)
    assert all(q["content_type"] == "math" for q in questions)
    assert all(q["question_options"] == [] for q in questions)

    session_id = data["session"]["id"]

    first = questions[0]
    first_answer = _parse_math_answer(first["question_stem"])
    assert first_answer >= 0

    invalid = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": first["id"], "user_answer": "abc"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == 42208

    wrong = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/answers",
        headers=headers,
        json={"session_question_id": first["id"], "user_answer": str(first_answer + 1)},
    )
    assert wrong.status_code == 200
    assert wrong.json()["data"]["is_correct"] is False

    for question in questions[1:]:
        answer = _parse_math_answer(question["question_stem"])
        assert answer >= 0
        resp = client.post(
            f"/api/v1/children/{child_id}/sessions/{session_id}/answers",
            headers=headers,
            json={"session_question_id": question["id"], "user_answer": str(answer)},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_correct"] is True

    completed = client.post(
        f"/api/v1/children/{child_id}/sessions/{session_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["session"]["answered_questions"] == 5
    assert completed.json()["data"]["session"]["correct_questions"] == 4


def test_math_session_requires_settings() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "math_nosettings", "display_name": "Parent", "password": "123456"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"account_name": "math_nosettings", "password": "123456"},
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小算", "age": 6},
    ).json()["data"]["id"]
    # 新建孩子会生成默认算术设置，这里显式停用后再验证会话启动报错
    disabled = client.put(
        f"/api/v1/children/{child_id}/math-settings",
        headers=headers,
        json={"min_value": 0, "max_value": 20, "operators": ["add", "subtract"], "status": 0},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["status"] == 0

    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 3,
            "default_content_types": ["math"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )

    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["math"]},
    )
    assert started.status_code == 404
    assert started.json()["code"] == 40407