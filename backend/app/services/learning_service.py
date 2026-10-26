from __future__ import annotations

import random
from typing import Any

from app.models import CARD_QUESTION_TYPES, AnswerSubmit, Content, MathSettings, Session, SessionStart, new_id, now_iso
from app.services.parent_service import ParentService
from app.services.parent_service import service as parent_service


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

        content_types = [t for t in selected_types if t != "math"]
        math_selected = "math" in selected_types

        contents, _ = self.parents.list_contents(parent_id, child_id, 1, 100000, None, "enabled", None)
        if content_types:
            contents = [item for item in contents if item.content_type in content_types]
        else:
            contents = []

        math_settings: MathSettings | None = None
        if math_selected:
            math_settings = self.parents.get_math_settings(parent_id, child_id)
            if not math_settings or math_settings.status != 1:
                raise LearningError(404, 40407, "math settings not found")

        if not math_selected and not contents:
            raise LearningError(422, 42204, "not enough enabled content to start a session")

        question_count = rule.question_count
        math_count = 0
        content_count = 0
        if math_selected and contents:
            num_types = len(selected_types)
            math_count = max(1, -(-question_count // num_types))
            content_count = question_count - math_count
        elif math_selected:
            math_count = question_count
        else:
            content_count = question_count

        selected_contents = random.sample(contents, min(content_count, len(contents)))
        shortfall = content_count - len(selected_contents)
        if math_selected and shortfall > 0:
            math_count += shortfall

        now = now_iso()
        session_id = new_id()

        math_questions = (
            [self._build_math_question(session_id, math_settings, index, now) for index in range(1, math_count + 1)]
            if math_selected
            else []
        )
        content_questions = [
            self._build_question(session_id, item, index, now)
            for index, item in enumerate(selected_contents, len(math_questions) + 1)
        ]
        questions = math_questions + content_questions
        random.shuffle(questions)
        for index, question in enumerate(questions, 1):
            question["question_order"] = index

        actual_types: list[str] = []
        if math_selected and math_count > 0:
            actual_types.append("math")
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

    def _build_math_question(
        self, session_id: str, settings: MathSettings, order: int, now: str
    ) -> dict[str, Any]:
        operator = random.choice(settings.operators)
        min_value = settings.min_value
        max_value = settings.max_value
        symbols = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}

        if operator == "add":
            a = random.randint(min_value, max_value)
            b = random.randint(min_value, max_value)
            result = a + b
        elif operator == "subtract":
            a = random.randint(min_value, max_value)
            b = random.randint(min_value, max_value)
            if a < b:
                a, b = b, a
            result = a - b
        elif operator == "multiply":
            a = random.randint(min_value, max_value)
            b = random.randint(min_value, max_value)
            result = a * b
        else:
            b = random.randint(max(1, min_value), max_value)
            quotient = random.randint(min_value, max_value)
            a = b * quotient
            result = quotient

        stem = f"{a} {symbols[operator]} {b} = ?"
        return {
            "id": new_id(),
            "session_id": session_id,
            "content_id": None,
            "content_type": "math",
            "question_type": "math_arithmetic",
            "question_stem": stem,
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