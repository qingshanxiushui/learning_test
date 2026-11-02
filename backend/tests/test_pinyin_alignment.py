"""注音对齐与内容清洗的回归测试。

两类历史缺陷：
1. pypinyin 默认把连续空白并入相邻的非汉字 token，返回列表比字符数短，
   使「拼音整体右移」；修复方式见 LearningService._pinyin_annotation。
2. 入库文本里残留的半角/全角空格既造成注音错位，也会进入卡片正文；
   修复方式见 ParentService._strip_inner_space。
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import Content
from app.services.learning_service import LearningService, _pinyin_annotation

SPACED_CLASSIC = "曰春夏，曰秋冬。此四时， 运不穷。"
LEGACY_POEM_HEADER = "《画鸡》明・唐寅 唐伯虎\n头上红冠不用裁\n满身雪白走将来"


def test_pinyin_annotation_always_matches_character_count() -> None:
    cases = [
        "地大物博",
        "apple",
        "door   window",
        SPACED_CLASSIC,
        LEGACY_POEM_HEADER,
        "《静夜思》唐·李白\n床前明月光",
        "   ",
        "",
    ]
    for text in cases:
        annotated = _pinyin_annotation(text)
        assert len(annotated) == len(text), text


def test_pinyin_annotation_keeps_characters_in_place_after_space() -> None:
    annotated = _pinyin_annotation(SPACED_CLASSIC)
    assert annotated[12] == " "
    assert annotated[13] == "yùn"
    assert annotated[15] == "qióng"
    assert annotated[16] == "。"


def test_math_and_pinyin_cards_never_carry_pinyin_annotation() -> None:
    """算术与拼音卡片按设计不标注拼音，question_pinyin 必须为空数组。"""
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "no_pinyin_parent", "display_name": "Parent", "password": "123456"},
    )
    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"account_name": "no_pinyin_parent", "password": "123456"},
        ).json()["data"]["access_token"]
    }
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小算", "age": 6},
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
            "question_count": 4,
            "default_content_types": ["math", "pinyin"],
            "allow_child_select_types": True,
            "status": 1,
        },
    )
    started = client.post(
        f"/api/v1/children/{child_id}/sessions",
        headers=headers,
        json={"selected_content_types": ["math", "pinyin"]},
    )
    assert started.status_code == 201
    questions = started.json()["data"]["questions"]
    assert questions
    for question in questions:
        assert question["question_type"] in ("math_arithmetic", "pinyin_card")
        assert question["question_pinyin"] == []


def test_annotation_parent_reports_aligned_pinyin_for_spaced_classic() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "align_parent", "display_name": "Parent", "password": "123456"},
    )
    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"account_name": "align_parent", "password": "123456"},
        ).json()["data"]["access_token"]
    }
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小齐", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/classics/batch",
        headers=headers,
        json={"content_text": f"{SPACED_CLASSIC}\n曰南北，曰西东。", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    client.put(
        f"/api/v1/children/{child_id}/rules",
        headers=headers,
        json={
            "question_count": 1,
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
    question = started.json()["data"]["questions"][0]
    stem = question["question_stem"]
    # 行内空白在入库时已被清掉，注音必须与正文等长且逐字对应
    assert " " not in stem
    assert question["question_pinyin"] is not None
    assert len(question["question_pinyin"]) == len(stem)
    assert question["question_pinyin"][stem.index("运")] == "yùn"


def test_classic_import_strips_inner_space_and_normalizes_body() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "space_parent", "display_name": "Parent", "password": "123456"},
    )
    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"account_name": "space_parent", "password": "123456"},
        ).json()["data"]["access_token"]
    }
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小空", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/classics/batch",
        headers=headers,
        json={"content_text": f"{SPACED_CLASSIC}\n曰南北，曰西东。", "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    record = imported.json()["data"]["list"][0]
    assert record["title"] == "曰春夏，曰秋冬。此四时，运不穷。"
    assert record["detail"]["sentence_text"] == "曰春夏，曰秋冬。此四时，运不穷。"
    assert record["detail"]["next_sentence"] == "曰南北，曰西东。"


def test_poem_import_accepts_katakana_middle_dot_header() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "header_parent", "display_name": "Parent", "password": "123456"},
    )
    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"account_name": "header_parent", "password": "123456"},
        ).json()["data"]["access_token"]
    }
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小诗", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/poems/batch",
        headers=headers,
        json={"content_text": LEGACY_POEM_HEADER, "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
    record = imported.json()["data"]["list"][0]
    # U+30FB 也必须被识别为朝代/作者分隔符，且署名里的空格要被清掉
    assert record["detail"]["dynasty"] == "明"
    assert record["detail"]["author"] == "唐寅唐伯虎"
    assert record["detail"]["poem_lines"] == ["头上红冠不用裁", "满身雪白走将来"]
    assert record["content_text"] == "头上红冠不用裁\n满身雪白走将来"


def test_poem_card_stem_aligns_with_pinyin() -> None:
    client = TestClient(app)
    client.post(
        "/api/v1/parents",
        json={"account_name": "poem_align_parent", "display_name": "Parent", "password": "123456"},
    )
    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"account_name": "poem_align_parent", "password": "123456"},
        ).json()["data"]["access_token"]
    }
    child_id = client.post(
        "/api/v1/children",
        headers=headers,
        json={"name": "小画", "age": 6},
    ).json()["data"]["id"]
    imported = client.post(
        f"/api/v1/children/{child_id}/contents/poems/batch",
        headers=headers,
        json={"content_text": LEGACY_POEM_HEADER, "difficulty": 1, "status": "enabled"},
    )
    assert imported.status_code == 201
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
    question = started.json()["data"]["questions"][0]
    stem = question["question_stem"]
    assert stem.splitlines()[0] == "《画鸡》明·唐寅唐伯虎"
    assert "满身雪白走将来" in stem
    assert len(question["question_pinyin"]) == len(stem)


def test_shipped_poem_and_classic_data_is_renderable() -> None:
    """真实的 data/contents/*.json 必须满足：注音与正文等长、中文内容无行内空白、标题不重复。"""
    repo_root = Path(__file__).resolve().parents[2]
    for file_name, content_type in (("poem.json", "poem"), ("classic.json", "classic")):
        path = repo_root / "data" / "contents" / file_name
        if not path.exists():
            continue
        records = [
            record
            for record in json.loads(path.read_text(encoding="utf-8"))
            if not record.get("is_deleted", 0)
        ]
        titles = [str(record["title"]) for record in records]
        assert len(titles) == len(set(titles)), f"{file_name} 存在重复标题: {titles}"

        seen_stems: set[str] = set()
        for record in records:
            content = Content(**record)
            assert " " not in content.content_text, f"{file_name} {content.title} 正文含空格"
            stem = (
                LearningService._format_poem(content)
                if content_type == "poem"
                else LearningService._format_classic(content)
            )
            assert stem not in seen_stems, f"{file_name} {content.title} 卡片正文重复"
            seen_stems.add(stem)
            assert len(_pinyin_annotation(stem)) == len(stem), f"{file_name} {content.title} 注音错位"
