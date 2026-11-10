from __future__ import annotations

import random
import re
from typing import Any

from pypinyin import Style, pinyin

from app.models import CARD_QUESTION_TYPES, AnswerSubmit, Content, MathSettings, PinyinSettings, Session, SessionStart, new_id, now_iso
from app.services.parent_service import ParentService
from app.services.parent_service import service as parent_service

# 拼音内置内容（家长无需录入，直接按分类启用）
PINYIN_LISTS: dict[str, list[str]] = {
    "initial": "b p m f d t n l g k h j q x zh ch sh r z c s y w".split(),
    "single_final": "a o e i u ü".split(),
    "final": "ai ei ui ao ou iu ie üe er an en in un ün ang eng ing ong".split(),
    "whole_syllable": "zhi chi shi ri zi ci si yi wu yu ye yue yuan yin yun ying".split(),
}

_TONE_MARKS: dict[str, str] = {
    "a": "āáǎà",
    "o": "ōóǒò",
    "e": "ēéěè",
    "i": "īíǐì",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",
}


def _apply_tone(pinyin: str, tone: int) -> str:
    if "a" in pinyin:
        target = "a"
    elif "o" in pinyin:
        target = "o"
    elif "e" in pinyin:
        target = "e"
    else:
        target = ""
        for ch in reversed(pinyin):
            if ch in ("i", "u", "ü"):
                target = ch
                break
        if not target:
            return pinyin
    return pinyin.replace(target, _TONE_MARKS[target][tone], 1)


def _pinyin_annotation(text: str) -> list[str]:
    """按字符返回与 `text` 对齐的拼音（带声调）；非汉字符号/换行返回原字符。

    `errors=list` 必须保留：pypinyin 默认会把连续的空白并入相邻的非汉字 token
    （例如 "， " 会合成一个 token），导致返回列表比字符数短，后续所有拼音整体错位。
    显式拆成单字符可保证长度严格等于 len(text)。
    """
    result: list[str] = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if index > 0:
            result.append("\n")
        for item in pinyin(line, style=Style.TONE, errors=lambda chars: list(chars)):
            result.append(item[0] if item else "")
    if len(result) != len(text):
        # 兜底：宁可退回原字符，也不要让拼音整体错位。
        result = list(text)
    return result


MATH_SYMBOLS: dict[str, str] = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
# 家长启用的运算符在本范围内无合法组合时的回退顺序（除法仅在约束商与除数时恒可行）
_MATH_FALLBACK_ORDER = ("divide", "multiply", "add", "subtract")
# 「含 0 或 1」的算式视为平凡题（如 3 + 0、5 × 1），生成时优先排除，只有无解时才退回
_TRIVIAL_FLOOR = 2
# 除法优先把被除数压到合理量级，但若收紧后可选组合过少，就放宽，避免题目退化成固定一道
_DIVIDE_MIN_COMBOS = 6
# 同一次会话内的去重尝试次数上限，超过后允许重复题面
_MATH_UNIQUE_ATTEMPTS = 24


def _divide_windows(
    divisor_floor: int,
    min_value: int,
    max_value: int,
    dividend_cap: int | None,
    quotient_floor: int,
) -> list[tuple[int, int, int]]:
    """除法窗口：外层为除数 b，内层为商 q（被除数 a = b × q ≤ dividend_cap）。"""
    windows: list[tuple[int, int, int]] = []
    for divisor in range(max(1, divisor_floor), max_value + 1):
        quotient_hi = max_value if dividend_cap is None else min(max_value, dividend_cap // divisor)
        if quotient_floor <= quotient_hi:
            windows.append((divisor, quotient_floor, quotient_hi))
    return windows


def _math_windows(
    operator: str, min_value: int, max_value: int, strict: bool = False
) -> list[tuple[int, int, int]]:
    """枚举「(外层取值, 内层下界, 内层上界)」窗口，用于在合法组合上按权重均匀采样。

    加减乘的外层是操作数 a、内层是 b；除法的外层是除数 b、内层是商。
    strict 为真时排除操作数与结果中出现的 0/1，只保留非平凡的组合。
    空列表表示该运算在当前取值范围内没有满足约束的组合。
    """
    windows: list[tuple[int, int, int]] = []
    outer_floor = max(min_value, _TRIVIAL_FLOOR) if strict else min_value
    inner_floor = max(min_value, _TRIVIAL_FLOOR) if strict else min_value
    if operator in ("add", "subtract"):
        for a in range(outer_floor, max_value + 1):
            if operator == "add":
                inner_lo = max(inner_floor, min_value - a)
                inner_hi = min(max_value, max_value - a)
            else:
                inner_lo = max(inner_floor, a - max_value)
                inner_hi = min(max_value, a - min_value)
                if strict:
                    inner_hi = min(inner_hi, a - _TRIVIAL_FLOOR)
            if inner_lo <= inner_hi:
                windows.append((a, inner_lo, inner_hi))
        return windows
    if operator == "multiply":
        for a in range(outer_floor, max_value + 1):
            if a <= 0:
                if min_value <= 0:
                    windows.append((a, inner_floor, max_value))
                continue
            inner_lo = max(inner_floor, -(-min_value // a))
            inner_hi = min(max_value, max_value // a)
            if inner_lo <= inner_hi:
                windows.append((a, inner_lo, inner_hi))
        return windows
    # 除法：优先让除数为 1 之外的数，并尽量把被除数限制在「不超过 max_value」的量级
    quotient_floor = max(inner_floor, 1)  # 商不为 0，避免出现 0 ÷ b
    divisor_floors = (max(_TRIVIAL_FLOOR, min_value),) if strict else (max(2, min_value), max(1, min_value))
    for divisor_floor in divisor_floors:
        fallback: list[tuple[int, int, int]] = []
        for cap in (max_value, 2 * max_value, 4 * max_value, None):
            candidates = _divide_windows(divisor_floor, min_value, max_value, cap, quotient_floor)
            if not candidates:
                continue
            # 被除数区间收得越窄，可选题目越少；组合数够多就用这个量级
            if sum(hi - lo + 1 for _, lo, hi in candidates) >= _DIVIDE_MIN_COMBOS:
                return candidates
            fallback = fallback or candidates
        if fallback:
            return fallback
    return []


def _resolve_math_triple(operator: str, outer: int, inner: int) -> tuple[int, int, int]:
    """把窗口取值还原为 (操作数 a, 操作数 b, 结果)。"""
    if operator == "add":
        return outer, inner, outer + inner
    if operator == "subtract":
        return outer, inner, outer - inner
    if operator == "multiply":
        return outer, inner, outer * inner
    return outer * inner, outer, inner


def _pick_math_triple(operator: str, windows: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """在窗口上按组合数加权采样，使各操作数分布接近均匀（而不是集中在最小值）。"""
    weights = [inner_hi - inner_lo + 1 for _, inner_lo, inner_hi in windows]
    outer, inner_lo, inner_hi = random.choices(windows, weights=weights)[0]
    return _resolve_math_triple(operator, outer, random.randint(inner_lo, inner_hi))


def _sample_math_triple(
    operator: str, min_value: int, max_value: int
) -> tuple[str, int, int, int]:
    """选出 (运算符, a, b, 结果)：先按非平凡组合采样，无解时放宽到含 0/1 的组合。

    返回值第一个元素可能是回退后的运算符（家长启用的运算在当前范围内无解时）。
    """
    for strict in (True, False):
        for candidate in (operator, *_MATH_FALLBACK_ORDER):
            windows = _math_windows(candidate, min_value, max_value, strict)
            if windows:
                a, b, result = _pick_math_triple(candidate, windows)
                return candidate, a, b, result
    # 取值范围内构造不出任何合法算式（max_value 已被校验为 ≥ 1，正常不会走到）
    return operator, min_value, min_value, min_value


class LearningError(Exception):
    def __init__(self, status_code: int, code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class LearningService:
    def __init__(self, parents: ParentService) -> None:
        self.parents = parents
        self.store = parents.store

    def start_session(self, parent_id: str, child_id: str, payload: SessionStart) -> tuple[Session, list[dict[str, Any]]]:
        try:
            self.parents.assert_child_owned(parent_id, child_id)
        except LookupError as exc:
            raise LearningError(404, 40402, "child not found") from exc

        rule = self.parents.get_rule(parent_id, child_id)
        if not rule or rule.status != 1:
            raise LearningError(404, 40404, "learning rule not found")

        selected_types = payload.selected_content_types
        if selected_types and not rule.allow_child_select_types:
            selected_types = rule.default_content_types
        if not selected_types:
            selected_types = rule.default_content_types

        content_types = [t for t in selected_types if t not in ("math", "pinyin")]
        rule_types = [t for t in ("math", "pinyin") if t in selected_types]

        contents, _ = self.parents.list_contents(parent_id, child_id, 1, 100000, None, "enabled", None)
        if content_types:
            contents = [item for item in contents if item.content_type in content_types]
        else:
            contents = []

        math_settings: MathSettings | None = None
        if "math" in rule_types:
            math_settings = self.parents.get_math_settings(parent_id, child_id)
            if not math_settings or math_settings.status != 1:
                raise LearningError(404, 40407, "math settings not found")

        pinyin_settings: PinyinSettings | None = None
        if "pinyin" in rule_types:
            pinyin_settings = self.parents.get_pinyin_settings(parent_id, child_id)
            if not pinyin_settings or pinyin_settings.status != 1:
                raise LearningError(404, 40408, "pinyin settings not found")

        if not rule_types and not contents:
            raise LearningError(422, 42204, "not enough enabled content to start a session")

        question_count = rule.question_count

        # 将总题量在「内容」与「规则驱动类型（math/pinyin）」之间均分
        slots: list[str] = []
        if content_types:
            slots.append("content")
        slots.extend(rule_types)
        num_slots = len(slots)
        counts: dict[str, int] = {s: question_count // num_slots for s in slots}
        remainder = question_count - sum(counts.values())
        for i in range(remainder):
            counts[slots[i]] += 1

        math_count = counts.get("math", 0)
        pinyin_count = counts.get("pinyin", 0)
        content_count = counts.get("content", 0)

        selected_contents = random.sample(contents, min(content_count, len(contents)))
        shortfall = content_count - len(selected_contents)
        while shortfall > 0:
            distributed = False
            for rt in rule_types:
                if shortfall <= 0:
                    break
                if rt == "math":
                    math_count += 1
                else:
                    pinyin_count += 1
                shortfall -= 1
                distributed = True
            if not distributed:
                break

        now = now_iso()
        session_id = new_id()

        math_questions = (
            self._build_math_questions(session_id, math_settings, math_count, now)
            if math_count > 0
            else []
        )

        pinyin_questions: list[dict[str, Any]] = []
        if pinyin_count > 0:
            pinyin_items = self._pinyin_items(pinyin_settings)
            if not pinyin_items:
                raise LearningError(422, 42209, "no pinyin categories selected")
            sampled_pinyin = random.sample(pinyin_items, min(pinyin_count, len(pinyin_items)))
            pinyin_questions = [
                self._build_pinyin_question(session_id, pinyin_settings, pinyin, category, index, now)
                for index, (pinyin, category) in enumerate(sampled_pinyin, 1)
            ]

        content_questions = [
            self._build_question(session_id, item, index, now)
            for index, item in enumerate(selected_contents, len(math_questions) + len(pinyin_questions) + 1)
        ]
        questions = math_questions + pinyin_questions + content_questions
        random.shuffle(questions)
        for index, question in enumerate(questions, 1):
            question["question_order"] = index

        actual_types: list[str] = []
        if math_count > 0:
            actual_types.append("math")
        if pinyin_count > 0:
            actual_types.append("pinyin")
        for item in selected_contents:
            if item.content_type not in actual_types:
                actual_types.append(item.content_type)

        session = Session(
            id=session_id,
            child_id=child_id,
            selected_content_types=actual_types,
            total_questions=len(questions),
            started_at=now,
            created_at=now,
            updated_at=now,
        )

        sessions = self.store.read_list("sessions/learning_sessions.json")
        sessions.append(session.model_dump())
        self.store.write_list("sessions/learning_sessions.json", sessions)
        stored_questions = self.store.read_list("sessions/session_questions.json")
        stored_questions.extend(questions)
        self.store.write_list("sessions/session_questions.json", stored_questions)
        return session, questions

    def session_questions(self, session_id: str, reveal_answers: bool = True) -> list[dict[str, Any]]:
        questions = [
            row
            for row in self.store.read_list("sessions/session_questions.json")
            if row.get("session_id") == session_id and row.get("is_deleted", 0) == 0
        ]
        questions.sort(key=lambda row: row.get("question_order", 0))
        hidden = {"correct_answer", "answer_explanation", "content_snapshot", "is_deleted", "deleted_at"}
        public = {"content_snapshot", "is_deleted", "deleted_at"}
        excluded = public if reveal_answers else hidden
        return [{key: value for key, value in row.items() if key not in excluded} for row in questions]

    def submit_answer(
        self, parent_id: str, child_id: str, session_id: str, payload: AnswerSubmit
    ) -> dict[str, Any]:
        session, session_rows, session_row = self._active_session(parent_id, child_id, session_id)
        questions = self.store.read_list("sessions/session_questions.json")
        question = next(
            (
                row
                for row in questions
                if row.get("id") == payload.session_question_id and row.get("session_id") == session_id
            ),
            None,
        )
        if not question:
            raise LearningError(404, 40406, "session question not found")
        if question.get("question_type") == "math_arithmetic":
            try:
                user_value = int(str(payload.user_answer).strip())
            except ValueError:
                raise LearningError(422, 42208, "answer must be an integer")
            is_correct = user_value == int(str(question["correct_answer"]).strip())
        else:
            if payload.user_answer not in question.get("question_options", []):
                raise LearningError(422, 42205, "answer must be one of the question options")
            is_correct = payload.user_answer.strip() == str(question["correct_answer"]).strip()

        answers = self.store.read_list("sessions/answer_records.json")
        if any(row.get("session_question_id") == payload.session_question_id and row.get("is_deleted", 0) == 0 for row in answers):
            raise LearningError(409, 40903, "question has already been answered")

        now = now_iso()
        answers.append(
            {
                "id": new_id(),
                "session_question_id": payload.session_question_id,
                "session_id": session_id,
                "child_id": child_id,
                "user_answer": payload.user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": int(is_correct),
                "answer_duration_ms": payload.answer_duration_ms,
                "answered_at": now,
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                "is_deleted": 0,
            }
        )
        self.store.write_list("sessions/answer_records.json", answers)

        answered = session.answered_questions + 1
        correct = session.correct_questions + int(is_correct)
        session_row.update(
            completed_questions=self._completed_count(session_id, questions, answers),
            answered_questions=answered,
            correct_questions=correct,
            accuracy_rate=round(correct / answered * 100, 2),
            updated_at=now,
        )
        self.store.write_list("sessions/learning_sessions.json", session_rows)
        return {
            "session_question_id": payload.session_question_id,
            "is_correct": is_correct,
            "correct_answer": question["correct_answer"],
            "answer_explanation": question.get("answer_explanation"),
            "progress": {
                "completed_questions": session_row["completed_questions"],
                "answered_questions": answered,
                "total_questions": session.total_questions,
                "correct_questions": correct,
                "accuracy_rate": session_row["accuracy_rate"],
            },
        }

    def mark_card_viewed(
        self, parent_id: str, child_id: str, session_id: str, question_id: str, view_duration_ms: int | None
    ) -> dict[str, Any]:
        session, session_rows, session_row = self._active_session(parent_id, child_id, session_id)
        questions = self.store.read_list("sessions/session_questions.json")
        question = next(
            (
                row
                for row in questions
                if row.get("id") == question_id
                and row.get("session_id") == session_id
                and row.get("is_deleted", 0) == 0
            ),
            None,
        )
        if not question:
            raise LearningError(404, 40406, "session question not found")
        if question.get("question_type") not in CARD_QUESTION_TYPES:
            raise LearningError(422, 42206, "question is not a learning card")

        if not question.get("viewed_at"):
            now = now_iso()
            question.update(viewed_at=now, view_duration_ms=view_duration_ms, updated_at=now)
            self.store.write_list("sessions/session_questions.json", questions)
            answers = self.store.read_list("sessions/answer_records.json")
            session_row.update(
                completed_questions=self._completed_count(session_id, questions, answers),
                updated_at=now,
            )
            self.store.write_list("sessions/learning_sessions.json", session_rows)

        return {
            "session_question_id": question_id,
            "viewed_at": question.get("viewed_at"),
            "progress": {
                "completed_questions": int(session_row.get("completed_questions", 0)),
                "total_questions": session.total_questions,
            },
        }

    def complete_session(self, parent_id: str, child_id: str, session_id: str) -> dict[str, Any]:
        session, session_rows, session_row = self._active_session(parent_id, child_id, session_id)
        questions = self.store.read_list("sessions/session_questions.json")
        answers = self.store.read_list("sessions/answer_records.json")
        completed = self._completed_count(session_id, questions, answers)
        if completed < session.total_questions:
            raise LearningError(409, 40904, "all questions must be completed before finishing the session")
        now = now_iso()
        session_row.update(
            completed_questions=completed,
            session_status="completed",
            finished_at=now,
            updated_at=now,
        )
        self.store.write_list("sessions/learning_sessions.json", session_rows)

        wrong_question_ids = {
            row.get("session_question_id")
            for row in self.store.read_list("sessions/answer_records.json")
            if row.get("session_id") == session_id and int(row.get("is_correct", 0)) == 0
        }
        review = []
        for question in self.store.read_list("sessions/session_questions.json"):
            if question.get("id") not in wrong_question_ids:
                continue
            snapshot = question.get("content_snapshot", {})
            review.append(
                {
                    "content_id": question.get("content_id"),
                    "title": snapshot.get("title"),
                    "content_type": question.get("content_type"),
                }
            )
        return {"session": Session(**session_row).model_dump(), "summary": {"need_review_contents": review}}

    @staticmethod
    def _completed_count(
        session_id: str, questions: list[dict[str, Any]], answers: list[dict[str, Any]]
    ) -> int:
        completed_ids = {
            row.get("session_question_id")
            for row in answers
            if row.get("session_id") == session_id and row.get("is_deleted", 0) == 0
        }
        completed_ids.update(
            row.get("id")
            for row in questions
            if row.get("session_id") == session_id
            and row.get("is_deleted", 0) == 0
            and row.get("question_type") in CARD_QUESTION_TYPES
            and row.get("viewed_at")
        )
        return len(completed_ids)

    def _active_session(
        self, parent_id: str, child_id: str, session_id: str
    ) -> tuple[Session, list[dict[str, Any]], dict[str, Any]]:
        try:
            self.parents.assert_child_owned(parent_id, child_id)
        except LookupError as exc:
            raise LearningError(404, 40402, "child not found") from exc
        rows = self.store.read_list("sessions/learning_sessions.json")
        row = next(
            (item for item in rows if item.get("id") == session_id and item.get("child_id") == child_id and item.get("is_deleted", 0) == 0),
            None,
        )
        if not row:
            raise LearningError(404, 40405, "learning session not found")
        session = Session(**row)
        if session.session_status != "in_progress":
            raise LearningError(409, 40903, "learning session is not in progress")
        return session, rows, row

    def _build_question(
        self, session_id: str, content: Content, order: int, now: str
    ) -> dict[str, Any]:
        question_type = {
            "character": "character_card",
            "englishWord": "english_word_card",
            "poem": "poem_card",
            "idiom": "idiom_card",
            "classic": "classic_card",
            "pinyin": "pinyin_card",
        }[content.content_type]
        if content.content_type == "poem":
            stem = self._format_poem(content)
        elif content.content_type == "classic":
            stem = self._format_classic(content)
        else:
            stem = content.title
        return {
            "id": new_id(),
            "session_id": session_id,
            "content_id": content.id,
            "content_type": content.content_type,
            "question_type": question_type,
            "question_stem": stem,
            "question_pinyin": _pinyin_annotation(stem),
            "question_options": [],
            "correct_answer": "",
            "answer_explanation": "",
            "question_order": order,
            "content_snapshot": content.model_dump(),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "is_deleted": 0,
        }

    def _build_math_questions(
        self, session_id: str, settings: MathSettings, count: int, now: str
    ) -> list[dict[str, Any]]:
        """生成 count 道算术题，尽量保证同一次会话内题面不重复。

        去重失败（取值范围太窄，组合数少于题量）或超过尝试上限时允许重复，但始终返回 count 道题。
        """
        questions: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index in range(1, count + 1):
            question = self._build_math_question(session_id, settings, index, now)
            for _ in range(_MATH_UNIQUE_ATTEMPTS):
                if question["question_stem"] not in seen:
                    break
                question = self._build_math_question(session_id, settings, index, now)
            seen.add(question["question_stem"])
            questions.append(question)
        return questions

    def _build_math_question(
        self, session_id: str, settings: MathSettings, order: int, now: str
    ) -> dict[str, Any]:
        operator = random.choice(settings.operators)
        min_value = settings.min_value
        max_value = settings.max_value

        # 最小值/最大值同时约束操作数与结果。
        # 这里不再「先定结果再反推操作数」——那种写法会让小操作数出现的概率成倍偏高
        # （结果 r 的可选 a 只有约 H_r 种，导致 a 的边际分布严重左偏）。
        # 改为先枚举全部满足约束的 (a, b) 组合，再按组合数加权采样，各操作数分布接近均匀。
        # 加减需要 max ≥ 2*min、乘法需要 min² ≤ max 才有组合；所选运算无解时按
        # _MATH_FALLBACK_ORDER 依次换别的运算（除法在约束商与除数时恒有解）。
        # 每个候选运算先尝试排除 0/1 的「非平凡」组合，实在没有再退回全量组合，
        # 这样 3 + 0、5 × 1 这类题目基本不会出现。
        operator, a, b, result = _sample_math_triple(operator, min_value, max_value)

        stem = f"{a} {MATH_SYMBOLS[operator]} {b} = ?"
        return {
            "id": new_id(),
            "session_id": session_id,
            "content_id": None,
            "content_type": "math",
            "question_type": "math_arithmetic",
            "question_stem": stem,
            "question_pinyin": [],
            "question_options": [],
            "correct_answer": str(result),
            "answer_explanation": "",
            "question_order": order,
            "content_snapshot": {
                "title": stem,
                "min_value": min_value,
                "max_value": max_value,
                "operator": operator,
                "operand_a": a,
                "operand_b": b,
            },
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "is_deleted": 0,
        }

    @staticmethod
    def _pinyin_items(settings: PinyinSettings) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        for category in settings.categories:
            for pinyin in PINYIN_LISTS.get(category, []):
                items.append((pinyin, category))
        return items

    def _build_pinyin_question(
        self,
        session_id: str,
        settings: PinyinSettings,
        pinyin: str,
        category: str,
        order: int,
        now: str,
    ) -> dict[str, Any]:
        stem = pinyin
        if settings.with_tone and category != "initial":
            stem = _apply_tone(pinyin, random.randint(0, 3))
        return {
            "id": new_id(),
            "session_id": session_id,
            "content_id": None,
            "content_type": "pinyin",
            "question_type": "pinyin_card",
            "question_stem": stem,
            "question_pinyin": [],
            "question_options": [],
            "correct_answer": "",
            "answer_explanation": "",
            "question_order": order,
            "content_snapshot": {
                "title": stem,
                "pinyin": pinyin,
                "pinyin_category": category,
                "with_tone": settings.with_tone,
            },
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "is_deleted": 0,
        }

    @staticmethod
    def _poem_lines(content: Content) -> list[str]:
        detail = content.detail or {}
        raw = detail.get("poem_lines")
        if isinstance(raw, list):
            return [str(line).strip() for line in raw if str(line).strip()]
        return [str(content.content_text).strip()] if content.content_text else []

    @staticmethod
    def _format_poem(content: Content) -> str:
        detail = content.detail or {}
        dynasty = str(detail.get("dynasty") or "").strip()
        author = str(detail.get("author") or "").strip()
        title = str(content.title or "").strip()
        header = f"《{title}》"
        if dynasty and author:
            header += f"{dynasty}·{author}"
        elif author:
            # 兼容历史数据：朝代缺失时作者字段里可能形如 "唐・李白"
            legacy = re.match(r"^([^·・‧•]+)[·・‧•](.+)$", author)
            if legacy:
                header += f"{legacy.group(1).strip()}·{legacy.group(2).strip()}"
            else:
                header += author
        lines = LearningService._poem_lines(content)
        if lines:
            return f"{header}\n" + "\n".join(lines)
        return header

    @staticmethod
    def _format_classic(content: Content) -> str:
        detail = content.detail or {}
        sentence = str(detail.get("sentence_text") or "").strip()
        next_sentence = str(detail.get("next_sentence") or "").strip()
        if next_sentence:
            return f"{sentence}\n{next_sentence}"
        return sentence or str(content.title or "").strip()


learning_service = LearningService(parent_service)