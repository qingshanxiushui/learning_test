from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ContentType = Literal["character", "classic", "poem", "idiom", "englishWord", "math"]
ContentStatus = Literal["enabled", "disabled"]
SessionStatus = Literal["in_progress", "completed", "abandoned"]
UserStatus = Literal["active", "disabled"]
MathOperator = Literal["add", "subtract", "multiply", "divide"]

# 以“卡片”形式展示、无需作答的题型（点击“下一个”即视为已学习）
CARD_QUESTION_TYPES: tuple[str, ...] = (
    "character_card",
    "english_word_card",
    "poem_card",
    "idiom_card",
    "classic_card",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id() -> str:
    return str(uuid4())


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:10]}")


class ParentCreate(BaseModel):
    account_name: str = Field(min_length=3, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=100)


class Parent(BaseModel):
    id: str
    account_name: str
    display_name: str
    password: str
    status: UserStatus = "active"
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class LoginRequest(BaseModel):
    account_name: str
    password: str


class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    age: int = Field(ge=3, le=12)
    grade_level: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=255)


class ChildUpdate(ChildCreate):
    status: UserStatus = "active"


class Child(BaseModel):
    id: str
    parent_user_id: str
    name: str
    nickname: str | None = None
    age: int
    grade_level: str | None = None
    avatar_url: str | None = None
    status: UserStatus = "active"
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class RuleCreate(BaseModel):
    question_count: int = Field(ge=1, le=20)
    default_content_types: list[ContentType] = Field(default_factory=list)
    allow_child_select_types: bool = True
    status: int = Field(default=1, ge=0, le=1)


class Rule(BaseModel):
    id: str
    child_id: str
    question_count: int
    default_content_types: list[ContentType]
    allow_child_select_types: bool
    status: int
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class MathSettingsUpsert(BaseModel):
    min_value: int = Field(default=0, ge=0)
    max_value: int = Field(default=20, ge=1)
    operators: list[MathOperator] = Field(default_factory=list)
    status: int = Field(default=1, ge=0, le=1)


class MathSettings(BaseModel):
    id: str
    child_id: str
    min_value: int
    max_value: int
    operators: list[MathOperator]
    status: int
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class ContentCreate(BaseModel):
    content_type: ContentType
    title: str = Field(min_length=1, max_length=100)
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class CharacterBatchCreate(BaseModel):
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class EnglishBatchCreate(BaseModel):
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class PoemBatchCreate(BaseModel):
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class IdiomBatchCreate(BaseModel):
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class ClassicBatchCreate(BaseModel):
    content_text: str = Field(min_length=1)
    pronunciation: str | None = Field(default=None, max_length=100)
    meaning: str | None = Field(default=None, max_length=255)
    example: str | None = Field(default=None, max_length=255)
    difficulty: int = Field(default=1, ge=1, le=3)
    status: ContentStatus = "enabled"
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class ContentUpdate(ContentCreate):
    pass


class ContentStatusUpdate(BaseModel):
    status: ContentStatus


class Content(BaseModel):
    id: str
    child_id: str
    content_type: ContentType
    title: str
    content_text: str
    pronunciation: str | None = None
    meaning: str | None = None
    example: str | None = None
    difficulty: int
    status: ContentStatus
    sort_order: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class Session(BaseModel):
    id: str
    child_id: str
    selected_content_types: list[ContentType] = Field(default_factory=list)
    total_questions: int = 0
    completed_questions: int = 0
    answered_questions: int = 0
    correct_questions: int = 0
    accuracy_rate: float = 0.0
    session_status: SessionStatus = "in_progress"
    started_at: str
    finished_at: str | None = None
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    is_deleted: int = 0


class SessionStart(BaseModel):
    selected_content_types: list[ContentType] = Field(default_factory=list)


class AnswerSubmit(BaseModel):
    session_question_id: str
    user_answer: str = Field(min_length=1)
    answer_duration_ms: int | None = Field(default=None, ge=0)


class CardViewSubmit(BaseModel):
    view_duration_ms: int | None = Field(default=None, ge=0)
