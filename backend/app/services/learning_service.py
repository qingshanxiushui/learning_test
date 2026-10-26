from __future__ import annotations

import random
from typing import Any

from app.models import CARD_QUESTION_TYPES, AnswerSubmit, Content, Session, SessionStart, new_id, now_iso
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

        contents, _ = self.parents.list_contents(parent_id, child_id, 1, 100000, None, "enabled", None)
        if selected_types:
            contents = [item for item in contents if item.content_type in selected_types]
        if not contents:
            raise LearningError(422, 42204, "not enough enabled content to start a session")

        selected_contents = random.sample(contents, min(rule.question_count, len(contents)))
        actual_types = list(dict.fromkeys(item.content_type for item in selected_contents))
        now = now_iso()
        session = Session(
            id=new_id(),
            child_id=child_id,
            selected_content_types=actual_types,
            total_questions=len(selected_contents),
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        questions = [self._build_question(session.id, item, index, contents, now) for index, item in enumerate(selected_contents, 1)]

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
        if payload.user_answer not in question.get("question_options", []):
            raise LearningError(422, 42205, "answer must be one of the question options")

        answers = self.store.read_list("sessions/answer_records.json")
        if any(row.get("session_question_id") == payload.session_question_id and row.get("is_deleted", 0) == 0 for row in answers):
            raise LearningError(409, 40903, "question has already been answered")

        is_correct = payload.user_answer.strip() == str(question["correct_answer"]).strip()
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
        self, session_id: str, content: Content, order: int, pool: list[Content], now: str
    ) -> dict[str, Any]:
        if content.content_type in ("character", "englishWord", "poem", "idiom"):
            question_type = {
                "character": "character_card",
                "englishWord": "english_word_card",
                "poem": "poem_card",
                "idiom": "idiom_card",
            }[content.content_type]
            stem = self._format_poem(content) if content.content_type == "poem" else content.title
            answer = ""
            explanation = ""
            options: list[str] = []
        else:
            question_type, stem, answer, explanation = self._question_text(content)
            same_type_pool = [item for item in pool if item.content_type == content.content_type]
            alternatives = [
                self._question_text(item)[2]
                for item in same_type_pool
                if item.id != content.id and self._question_text(item)[2] != answer
            ]
            options = list(dict.fromkeys([answer, *alternatives]))[:3]
            random.shuffle(options)
        return {
            "id": new_id(),
            "session_id": session_id,
            "content_id": content.id,
            "content_type": content.content_type,
            "question_type": question_type,
            "question_stem": stem,
            "question_options": options,
            "correct_answer": answer,
            "answer_explanation": explanation,
            "question_order": order,
            "content_snapshot": content.model_dump(),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "is_deleted": 0,
        }

    def _question_text(self, content: Content) -> tuple[str, str, str, str]:
        detail = content.detail
        if content.content_type == "character":
            pronunciation = str(detail.get("pinyin") or content.pronunciation or "").strip()
            if pronunciation:
                return "pinyin_character_choice", f"哪个汉字读“{pronunciation}”？", content.title, content.meaning or content.content_text
            if content.meaning:
                return "meaning_choice", f"“{content.title}”是什么意思？", content.meaning, content.example or content.content_text

        if content.content_type == "classic":
            sentence = str(detail.get("sentence_text") or content.content_text).strip()
            next_sentence = str(detail.get("next_sentence") or "").strip()
            if next_sentence:
                return "next_line_choice", f"“{sentence}”下一句是什么？", next_sentence, content.meaning or content.title
            if content.meaning:
                return "meaning_choice", f"“{sentence}”是什么意思？", content.meaning, content.title

        return "content_choice", f"请选择《{content.title}》的学习内容", content.content_text, content.meaning or content.example or content.title

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


learning_service = LearningService(parent_service)