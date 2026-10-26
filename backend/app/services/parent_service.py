from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any
import unicodedata

from app.core.config import settings
from app.models import (
    CARD_QUESTION_TYPES,
    CharacterBatchCreate,
    Child,
    ChildCreate,
    ChildUpdate,
    Content,
    ContentCreate,
    ContentStatusUpdate,
    ContentUpdate,
    EnglishBatchCreate,
    IdiomBatchCreate,
    Parent,
    ParentCreate,
    PoemBatchCreate,
    Rule,
    RuleCreate,
    Session,
    new_id,
    now_iso,
)
from app.repositories.json_store import JsonStore


class ParentService:
    def __init__(self) -> None:
        self.store = JsonStore(settings.data_dir)
        self._ensure_management_parent()

    def _ensure_management_parent(self) -> None:
        rows = self.store.read_list("parent_users.json")
        for r in rows:
            if r.get("account_name") == settings.management_account_name and r.get("is_deleted", 0) == 0:
                return

        now = now_iso()
        rows.append(
            Parent(
                id=settings.management_user_id,
                account_name=settings.management_account_name,
                display_name=settings.management_display_name,
                password=settings.management_password,
                status="active",
                created_at=now,
                updated_at=now,
            ).model_dump()
        )
        self.store.write_list("parent_users.json", rows)

    def _active(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [r for r in rows if r.get("is_deleted", 0) == 0]

    def create_parent(self, payload: ParentCreate) -> Parent:
        rows = self.store.read_list("parent_users.json")
        if any(r.get("account_name") == payload.account_name and r.get("is_deleted", 0) == 0 for r in rows):
            raise ValueError("account exists")
        now = now_iso()
        item = Parent(
            id=new_id(),
            account_name=payload.account_name,
            display_name=payload.display_name,
            password=payload.password,
            status="active",
            created_at=now,
            updated_at=now,
        ).model_dump()
        rows.append(item)
        self.store.write_list("parent_users.json", rows)
        return Parent(**item)

    def auth_parent(self, account_name: str, password: str) -> Parent | None:
        rows = self._active(self.store.read_list("parent_users.json"))
        for r in rows:
            if r.get("account_name") == account_name and r.get("password") == password:
                return Parent(**r)
        return None

    def get_parent(self, parent_id: str) -> Parent | None:
        rows = self._active(self.store.read_list("parent_users.json"))
        for r in rows:
            if r.get("id") == parent_id:
                return Parent(**r)
        return None

    def list_children(self, parent_id: str, status: str | None, page: int, page_size: int) -> tuple[list[Child], int]:
        rows = [r for r in self._active(self.store.read_list("children.json")) if r.get("parent_user_id") == parent_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return [Child(**r) for r in rows[start:end]], total

    def create_child(self, parent_id: str, payload: ChildCreate) -> Child:
        now = now_iso()
        item = Child(
            id=new_id(),
            parent_user_id=parent_id,
            name=payload.name,
            nickname=payload.nickname,
            age=payload.age,
            grade_level=payload.grade_level,
            avatar_url=payload.avatar_url,
            status="active",
            created_at=now,
            updated_at=now,
        ).model_dump()
        rows = self.store.read_list("children.json")
        rows.append(item)
        self.store.write_list("children.json", rows)
        return Child(**item)

    def get_child(self, parent_id: str, child_id: str) -> Child | None:
        rows = [r for r in self._active(self.store.read_list("children.json")) if r.get("parent_user_id") == parent_id]
        for r in rows:
            if r.get("id") == child_id:
                return Child(**r)
        return None

    def update_child(self, parent_id: str, child_id: str, payload: ChildUpdate) -> Child | None:
        rows = self.store.read_list("children.json")
        for r in rows:
            if r.get("id") == child_id and r.get("parent_user_id") == parent_id and r.get("is_deleted", 0) == 0:
                r.update(payload.model_dump())
                r["updated_at"] = now_iso()
                self.store.write_list("children.json", rows)
                return Child(**r)
        return None

    def delete_child(self, parent_id: str, child_id: str) -> bool:
        rows = self.store.read_list("children.json")
        for r in rows:
            if r.get("id") == child_id and r.get("parent_user_id") == parent_id and r.get("is_deleted", 0) == 0:
                r["is_deleted"] = 1
                r["deleted_at"] = now_iso()
                r["updated_at"] = now_iso()
                self.store.write_list("children.json", rows)
                return True
        return False

    def _content_file(self, content_type: str) -> str:
        return f"contents/{content_type}.json"

    def list_contents(
        self,
        parent_id: str,
        child_id: str,
        page: int,
        page_size: int,
        content_type: str | None,
        status: str | None,
        keyword: str | None,
    ) -> tuple[list[Content], int]:
        self.assert_child_owned(parent_id, child_id)
        types = [content_type] if content_type else ["character", "classic", "poem", "idiom", "englishWord"]
        out: list[dict[str, Any]] = []
        for t in types:
            for r in self._active(self.store.read_list(self._content_file(t))):
                if r.get("child_id") != child_id:
                    continue
                if status and r.get("status") != status:
                    continue
                if keyword and keyword.lower() not in (f"{r.get('title', '')} {r.get('content_text', '')}").lower():
                    continue
                out.append(r)
        out.sort(key=lambda x: (x.get("sort_order", 0), x.get("created_at", "")))
        total = len(out)
        start = (page - 1) * page_size
        end = start + page_size
        return [Content(**r) for r in out[start:end]], total

    def create_content(self, parent_id: str, child_id: str, payload: ContentCreate) -> Content:
        self.assert_child_owned(parent_id, child_id)
        now = now_iso()
        item = Content(
            id=new_id(),
            child_id=child_id,
            content_type=payload.content_type,
            title=payload.title,
            content_text=payload.content_text,
            pronunciation=payload.pronunciation,
            meaning=payload.meaning,
            example=payload.example,
            difficulty=payload.difficulty,
            status=payload.status,
            sort_order=payload.sort_order,
            detail=payload.detail,
            created_at=now,
            updated_at=now,
        ).model_dump()
        rel = self._content_file(payload.content_type)
        rows = self.store.read_list(rel)
        rows.append(item)
        self.store.write_list(rel, rows)
        return Content(**item)

    def batch_upsert_characters(
        self, parent_id: str, child_id: str, payload: CharacterBatchCreate
    ) -> tuple[list[Content], int, int]:
        self.assert_child_owned(parent_id, child_id)
        characters = self._extract_characters(payload.content_text)
        if not characters:
            raise ValueError("content text must contain at least one Chinese character")

        rel = self._content_file("character")
        rows = self.store.read_list(rel)
        existing: dict[str, dict[str, Any]] = {}
        for row in rows:
            if (
                row.get("child_id") == child_id
                and row.get("content_type") == "character"
                and row.get("is_deleted", 0) == 0
            ):
                existing.setdefault(str(row.get("title", "")), row)

        now = now_iso()
        items: list[Content] = []
        created_count = 0
        updated_count = 0
        common = payload.model_dump(exclude={"content_text"})
        for character in characters:
            row = existing.get(character)
            if row is None:
                row = Content(
                    id=new_id(),
                    child_id=child_id,
                    content_type="character",
                    title=character,
                    content_text=character,
                    created_at=now,
                    updated_at=now,
                    **common,
                ).model_dump()
                rows.append(row)
                created_count += 1
            else:
                row.update(common)
                row.update({"title": character, "content_text": character, "updated_at": now})
                updated_count += 1
            items.append(Content(**row))

        self.store.write_list(rel, rows)
        return items, created_count, updated_count

    def batch_upsert_english_words(
        self, parent_id: str, child_id: str, payload: EnglishBatchCreate
    ) -> tuple[list[Content], int, int]:
        self.assert_child_owned(parent_id, child_id)
        words = self._extract_english_words(payload.content_text)
        if not words:
            raise ValueError("content text must contain at least one English word")

        rel = self._content_file("englishWord")
        rows = self.store.read_list(rel)
        existing: dict[str, dict[str, Any]] = {}
        for row in rows:
            if (
                row.get("child_id") == child_id
                and row.get("content_type") == "englishWord"
                and row.get("is_deleted", 0) == 0
            ):
                existing.setdefault(str(row.get("title", "")).lower(), row)

        now = now_iso()
        items: list[Content] = []
        created_count = 0
        updated_count = 0
        common = payload.model_dump(exclude={"content_text"})
        for word in words:
            row = existing.get(word.lower())
            if row is None:
                row = Content(
                    id=new_id(),
                    child_id=child_id,
                    content_type="englishWord",
                    title=word,
                    content_text=word,
                    created_at=now,
                    updated_at=now,
                    **common,
                ).model_dump()
                rows.append(row)
                existing[word.lower()] = row
                created_count += 1
            else:
                row.update(common)
                row.update({"title": word, "content_text": word, "updated_at": now})
                updated_count += 1
            items.append(Content(**row))

        self.store.write_list(rel, rows)
        return items, created_count, updated_count

    def batch_upsert_poems(
        self, parent_id: str, child_id: str, payload: PoemBatchCreate
    ) -> tuple[list[Content], int, int]:
        self.assert_child_owned(parent_id, child_id)
        poems = self._extract_poems(payload.content_text)
        if not poems:
            raise ValueError("content text must contain at least one poem")

        rel = self._content_file("poem")
        rows = self.store.read_list(rel)
        existing: dict[str, dict[str, Any]] = {}
        for row in rows:
            if (
                row.get("child_id") == child_id
                and row.get("content_type") == "poem"
                and row.get("is_deleted", 0) == 0
            ):
                existing.setdefault(str(row.get("title", "")), row)

        now = now_iso()
        items: list[Content] = []
        created_count = 0
        updated_count = 0
        common = payload.model_dump(exclude={"content_text", "detail"})
        for poem in poems:
            title = poem["title"]
            detail = {
                "poem_title": title,
                "dynasty": poem["dynasty"],
                "author": poem["author"],
                "poem_lines": poem["poem_lines"],
            }
            row = existing.get(title)
            if row is None:
                row = Content(
                    id=new_id(),
                    child_id=child_id,
                    content_type="poem",
                    title=title,
                    content_text=poem["content_text"],
                    created_at=now,
                    updated_at=now,
                    detail=detail,
                    **common,
                ).model_dump()
                rows.append(row)
                created_count += 1
            else:
                row.update(common)
                row.update(
                    {
                        "title": title,
                        "content_text": poem["content_text"],
                        "detail": detail,
                        "updated_at": now,
                    }
                )
                updated_count += 1
            items.append(Content(**row))

        self.store.write_list(rel, rows)
        return items, created_count, updated_count

    def batch_upsert_idioms(
        self, parent_id: str, child_id: str, payload: IdiomBatchCreate
    ) -> tuple[list[Content], int, int]:
        self.assert_child_owned(parent_id, child_id)
        idioms = self._extract_idioms(payload.content_text)
        if not idioms:
            raise ValueError("content text must contain at least one idiom")

        rel = self._content_file("idiom")
        rows = self.store.read_list(rel)
        existing: dict[str, dict[str, Any]] = {}
        for row in rows:
            if (
                row.get("child_id") == child_id
                and row.get("content_type") == "idiom"
                and row.get("is_deleted", 0) == 0
            ):
                existing.setdefault(str(row.get("title", "")), row)

        now = now_iso()
        items: list[Content] = []
        created_count = 0
        updated_count = 0
        common = payload.model_dump(exclude={"content_text"})
        for idiom in idioms:
            row = existing.get(idiom)
            if row is None:
                row = Content(
                    id=new_id(),
                    child_id=child_id,
                    content_type="idiom",
                    title=idiom,
                    content_text=idiom,
                    created_at=now,
                    updated_at=now,
                    **common,
                ).model_dump()
                rows.append(row)
                created_count += 1
            else:
                row.update(common)
                row.update({"title": idiom, "content_text": idiom, "updated_at": now})
                updated_count += 1
            items.append(Content(**row))

        self.store.write_list(rel, rows)
        return items, created_count, updated_count

    @staticmethod
    def _extract_poems(content_text: str) -> list[dict[str, Any]]:
        poems: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        body_lines: list[str] = []

        def flush() -> None:
            nonlocal current, body_lines
            if current is not None:
                current["poem_lines"] = ParentService._split_poem_lines("\n".join(body_lines))
                current["content_text"] = "\n".join(body_lines)
                poems.append(current)
            current = None
            body_lines = []

        for raw_line in content_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            header = ParentService._parse_poem_header(line)
            if header is not None:
                flush()
                current = header
                body_lines = []
            elif current is not None:
                body_lines.append(line)

        flush()
        return poems

    @staticmethod
    def _parse_poem_header(line: str) -> dict[str, str] | None:
        match = re.match(r"^《(.+?)》(.*)$", line)
        if not match:
            return None
        title = match.group(1).strip()
        attribution = match.group(2).strip()
        dynasty = ""
        author = ""
        if "·" in attribution:
            dynasty, author = attribution.split("·", 1)
            dynasty = dynasty.strip()
            author = author.strip()
        elif attribution:
            author = attribution
        return {"title": title, "dynasty": dynasty, "author": author}

    @staticmethod
    def _split_poem_lines(body: str) -> list[str]:
        return [part for part in re.split(r"[，。！？；、,.!?;:：\n]+", body) if part.strip()]

    @staticmethod
    def _extract_idioms(content_text: str) -> list[str]:
        idioms: list[str] = []
        seen: set[str] = set()
        for match in re.findall(r"《([^《》]+)》", content_text):
            idiom = match.strip()
            if idiom and idiom not in seen:
                seen.add(idiom)
                idioms.append(idiom)
        return idioms

    @staticmethod
    def _extract_english_words(content_text: str) -> list[str]:
        # 按换行与标点切分，但空格不分割（空格分隔的词组作为整体保留），
        # 同时保留单词内部的连字符/撇号，如 well-known、don't、good morning
        words: list[str] = []
        seen: set[str] = set()
        for token in re.findall(r"[A-Za-z0-9 '’-]+", content_text):
            word = token.strip()
            if word and not word.isdigit() and word.lower() not in seen:
                seen.add(word.lower())
                words.append(word)
        return words

    @staticmethod
    def _extract_characters(content_text: str) -> list[str]:
        characters: list[str] = []
        seen: set[str] = set()
        for character in content_text:
            name = unicodedata.name(character, "")
            is_character = character == "〇" or name.startswith(
                ("CJK UNIFIED IDEOGRAPH-", "CJK COMPATIBILITY IDEOGRAPH-")
            )
            if is_character and character not in seen:
                seen.add(character)
                characters.append(character)
        return characters

    def get_content(self, parent_id: str, child_id: str, content_id: str) -> Content | None:
        self.assert_child_owned(parent_id, child_id)
        for t in ["character", "classic", "poem", "idiom", "englishWord"]:
            rows = self._active(self.store.read_list(self._content_file(t)))
            for r in rows:
                if r.get("id") == content_id and r.get("child_id") == child_id:
                    return Content(**r)
        return None

    def update_content(self, parent_id: str, child_id: str, content_id: str, payload: ContentUpdate) -> Content | None:
        self.assert_child_owned(parent_id, child_id)
        for t in ["character", "classic", "poem", "idiom", "englishWord"]:
            rel = self._content_file(t)
            rows = self.store.read_list(rel)
            changed = False
            for r in rows:
                if r.get("id") == content_id and r.get("child_id") == child_id and r.get("is_deleted", 0) == 0:
                    if t != payload.content_type:
                        r["is_deleted"] = 1
                        r["deleted_at"] = now_iso()
                        changed = True
                        self.store.write_list(rel, rows)
                        return self.create_content(parent_id, child_id, ContentCreate(**payload.model_dump()))
                    r.update(payload.model_dump())
                    r["updated_at"] = now_iso()
                    changed = True
                    self.store.write_list(rel, rows)
                    return Content(**r)
            if changed:
                break
        return None

    def delete_content(self, parent_id: str, child_id: str, content_id: str) -> bool:
        self.assert_child_owned(parent_id, child_id)
        for t in ["character", "classic", "poem", "idiom", "englishWord"]:
            rel = self._content_file(t)
            rows = self.store.read_list(rel)
            for r in rows:
                if r.get("id") == content_id and r.get("child_id") == child_id and r.get("is_deleted", 0) == 0:
                    r["is_deleted"] = 1
                    r["deleted_at"] = now_iso()
                    r["updated_at"] = now_iso()
                    self.store.write_list(rel, rows)
                    return True
        return False

    def update_content_status(
        self, parent_id: str, child_id: str, content_id: str, payload: ContentStatusUpdate
    ) -> Content | None:
        self.assert_child_owned(parent_id, child_id)
        for t in ["character", "classic", "poem", "idiom", "englishWord"]:
            rel = self._content_file(t)
            rows = self.store.read_list(rel)
            for r in rows:
                if r.get("id") == content_id and r.get("child_id") == child_id and r.get("is_deleted", 0) == 0:
                    r["status"] = payload.status
                    r["updated_at"] = now_iso()
                    self.store.write_list(rel, rows)
                    return Content(**r)
        return None

    def get_rule(self, parent_id: str, child_id: str) -> Rule | None:
        self.assert_child_owned(parent_id, child_id)
        rows = self._active(self.store.read_list("learning_rules.json"))
        for r in rows:
            if r.get("child_id") == child_id:
                return Rule(**r)
        return None

    def create_rule(self, parent_id: str, child_id: str, payload: RuleCreate) -> Rule:
        self.assert_child_owned(parent_id, child_id)
        if self.get_rule(parent_id, child_id):
            raise ValueError("rule exists")
        now = now_iso()
        item = Rule(
            id=new_id(),
            child_id=child_id,
            question_count=payload.question_count,
            default_content_types=payload.default_content_types,
            allow_child_select_types=payload.allow_child_select_types,
            status=payload.status,
            created_at=now,
            updated_at=now,
        ).model_dump()
        rows = self.store.read_list("learning_rules.json")
        rows.append(item)
        self.store.write_list("learning_rules.json", rows)
        return Rule(**item)

    def upsert_rule(self, parent_id: str, child_id: str, payload: RuleCreate) -> Rule:
        self.assert_child_owned(parent_id, child_id)
        rows = self.store.read_list("learning_rules.json")
        for r in rows:
            if r.get("child_id") == child_id and r.get("is_deleted", 0) == 0:
                r.update(payload.model_dump())
                r["updated_at"] = now_iso()
                self.store.write_list("learning_rules.json", rows)
                return Rule(**r)
        return self.create_rule(parent_id, child_id, payload)

    def list_sessions(
        self, parent_id: str, child_id: str, page: int, page_size: int, session_status: str | None
    ) -> tuple[list[Session], int]:
        self.assert_child_owned(parent_id, child_id)
        rows = [r for r in self._active(self.store.read_list("sessions/learning_sessions.json")) if r.get("child_id") == child_id]
        if session_status:
            rows = [r for r in rows if r.get("session_status") == session_status]
        rows.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return [Session(**r) for r in rows[start:end]], total

    def get_session(self, parent_id: str, child_id: str, session_id: str) -> Session | None:
        self.assert_child_owned(parent_id, child_id)
        rows = self._active(self.store.read_list("sessions/learning_sessions.json"))
        for r in rows:
            if r.get("id") == session_id and r.get("child_id") == child_id:
                return Session(**r)
        return None

    def get_session_result(self, parent_id: str, child_id: str, session_id: str) -> dict[str, Any] | None:
        session = self.get_session(parent_id, child_id, session_id)
        if not session:
            return None
        questions = [
            q
            for q in self._active(self.store.read_list("sessions/session_questions.json"))
            if q.get("session_id") == session_id
        ]
        answers = [
            a
            for a in self._active(self.store.read_list("sessions/answer_records.json"))
            if a.get("session_id") == session_id
        ]
        answer_map = {a["session_question_id"]: a for a in answers}
        result_answers = []
        for q in sorted(questions, key=lambda x: x.get("question_order", 0)):
            a = answer_map.get(q.get("id"), {})
            is_card = q.get("question_type") in CARD_QUESTION_TYPES
            result_answers.append(
                {
                    "session_question_id": q.get("id"),
                    "question_order": q.get("question_order"),
                    "question_stem": q.get("question_stem"),
                    "user_answer": a.get("user_answer"),
                    "correct_answer": None if is_card else q.get("correct_answer"),
                    "is_correct": None if is_card else bool(a.get("is_correct", 0)),
                    "viewed": bool(q.get("viewed_at")) if is_card else None,
                    "answer_explanation": q.get("answer_explanation"),
                }
            )
        return {"session": session.model_dump(), "answers": result_answers}

    def stats_overview(self, parent_id: str, child_id: str) -> dict[str, Any]:
        self.assert_child_owned(parent_id, child_id)
        sessions = [
            s
            for s in self._active(self.store.read_list("sessions/learning_sessions.json"))
            if s.get("child_id") == child_id and s.get("session_status") == "completed"
        ]
        total_sessions = len(sessions)
        answered_sessions = [s for s in sessions if int(s.get("answered_questions", 0)) > 0]
        avg_acc = (
            round(
                sum(float(s.get("accuracy_rate", 0)) for s in answered_sessions) / len(answered_sessions),
                2,
            )
            if answered_sessions
            else 0.0
        )
        contents, _ = self.list_contents(parent_id, child_id, 1, 100000, None, None, None)
        recent = sorted(sessions, key=lambda x: x.get("finished_at", ""), reverse=True)
        recent_session = recent[0] if recent else None
        return {
            "total_sessions": total_sessions,
            "sessions_last_7_days": total_sessions,
            "average_accuracy_rate": avg_acc,
            "content_count": len(contents),
            "recent_session": {
                "id": recent_session.get("id"),
                "finished_at": recent_session.get("finished_at"),
                "accuracy_rate": recent_session.get("accuracy_rate"),
            }
            if recent_session
            else None,
        }

    def stats_by_content_type(self, parent_id: str, child_id: str) -> list[dict[str, Any]]:
        self.assert_child_owned(parent_id, child_id)
        questions = [
            q
            for q in self._active(self.store.read_list("sessions/session_questions.json"))
            if q.get("content_snapshot", {}).get("child_id", child_id) == child_id or q.get("child_id") == child_id
        ]
        answers = self._active(self.store.read_list("sessions/answer_records.json"))
        answer_map = {a.get("session_question_id"): a for a in answers if a.get("child_id") == child_id}
        counter = defaultdict(lambda: {"total": 0, "correct": 0})
        for q in questions:
            qid = q.get("id")
            ct = q.get("content_type")
            if not ct:
                continue
            ans = answer_map.get(qid)
            if not ans:
                continue
            counter[ct]["total"] += 1
            counter[ct]["correct"] += 1 if int(ans.get("is_correct", 0)) == 1 else 0
        out = []
        for ct, val in counter.items():
            total = val["total"]
            out.append(
                {
                    "content_type": ct,
                    "total_answers": total,
                    "correct_answers": val["correct"],
                    "accuracy_rate": round((val["correct"] / total) * 100, 2) if total else 0,
                }
            )
        return out

    def stats_weak_contents(self, parent_id: str, child_id: str, limit: int, content_type: str | None) -> list[dict[str, Any]]:
        self.assert_child_owned(parent_id, child_id)
        questions = [
            q
            for q in self._active(self.store.read_list("sessions/session_questions.json"))
            if (not content_type or q.get("content_type") == content_type)
        ]
        answers = [
            a
            for a in self._active(self.store.read_list("sessions/answer_records.json"))
            if a.get("child_id") == child_id and int(a.get("is_correct", 0)) == 0
        ]
        q_map = {q.get("id"): q for q in questions}
        wrong_counter: Counter[str] = Counter()
        last_wrong: dict[str, str] = {}
        for a in answers:
            q = q_map.get(a.get("session_question_id"))
            if not q:
                continue
            cid = q.get("content_id")
            wrong_counter[cid] += 1
            last_wrong[cid] = a.get("answered_at")
        contents, _ = self.list_contents(parent_id, child_id, 1, 100000, None, None, None)
        c_map = {c.id: c for c in contents}
        out = []
        for cid, cnt in wrong_counter.most_common(limit):
            c = c_map.get(cid)
            if not c:
                continue
            out.append(
                {
                    "content_id": cid,
                    "title": c.title,
                    "content_type": c.content_type,
                    "wrong_count": cnt,
                    "last_wrong_at": last_wrong.get(cid),
                }
            )
        return out

    def assert_child_owned(self, parent_id: str, child_id: str) -> None:
        if not self.get_child(parent_id, child_id):
            raise LookupError("child not found")


service = ParentService()
