from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_parent
from app.models import AnswerSubmit, ApiResponse, CardViewSubmit, SessionStart
from app.services.learning_service import LearningError, learning_service
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/sessions", tags=["sessions"])
CurrentParent = Annotated[dict[str, str], Depends(get_current_parent)]


def _raise_learning_error(exc: LearningError) -> None:
    raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc


@router.post("", response_model=ApiResponse, status_code=201)
def start_session(child_id: str, payload: SessionStart, current: CurrentParent) -> ApiResponse:
    try:
        session, _ = learning_service.start_session(current["user_id"], child_id, payload)
    except LearningError as exc:
        _raise_learning_error(exc)
    return ApiResponse(
        data={
            "session": session.model_dump(exclude={"is_deleted", "deleted_at"}),
            "questions": learning_service.session_questions(session.id, reveal_answers=False),
        }
    )


@router.get("", response_model=ApiResponse)
def list_sessions(
    child_id: str,
    current: CurrentParent,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session_status: str | None = None,
) -> ApiResponse:
    try:
        items, total = service.list_sessions(current["user_id"], child_id, page, page_size, session_status)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"}) from exc
    return ApiResponse(data={"list": [i.model_dump(exclude={"is_deleted", "deleted_at"}) for i in items], "pagination": {"page": page, "page_size": page_size, "total": total}})


@router.get("/{session_id}", response_model=ApiResponse)
def get_session(child_id: str, session_id: str, current: CurrentParent) -> ApiResponse:
    try:
        item = service.get_session(current["user_id"], child_id, session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"}) from exc
    if not item:
        raise HTTPException(status_code=404, detail={"code": 40405, "message": "session not found"})
    return ApiResponse(
        data={
            "session": item.model_dump(exclude={"is_deleted", "deleted_at"}),
            "questions": learning_service.session_questions(
                session_id, reveal_answers=item.session_status == "completed"
            ),
        }
    )


@router.post("/{session_id}/answers", response_model=ApiResponse)
def submit_answer(child_id: str, session_id: str, payload: AnswerSubmit, current: CurrentParent) -> ApiResponse:
    try:
        result = learning_service.submit_answer(current["user_id"], child_id, session_id, payload)
    except LearningError as exc:
        _raise_learning_error(exc)
    return ApiResponse(data=result)


@router.post("/{session_id}/questions/{question_id}/viewed", response_model=ApiResponse)
def mark_card_viewed(
    child_id: str,
    session_id: str,
    question_id: str,
    payload: CardViewSubmit,
    current: CurrentParent,
) -> ApiResponse:
    try:
        result = learning_service.mark_card_viewed(
            current["user_id"], child_id, session_id, question_id, payload.view_duration_ms
        )
    except LearningError as exc:
        _raise_learning_error(exc)
    return ApiResponse(data=result)


@router.post("/{session_id}/complete", response_model=ApiResponse)
def complete_session(child_id: str, session_id: str, current: CurrentParent) -> ApiResponse:
    try:
        result = learning_service.complete_session(current["user_id"], child_id, session_id)
    except LearningError as exc:
        _raise_learning_error(exc)
    return ApiResponse(data=result)


@router.get("/{session_id}/result", response_model=ApiResponse)
def get_session_result(child_id: str, session_id: str, current: CurrentParent) -> ApiResponse:
    try:
        item = service.get_session_result(current["user_id"], child_id, session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"}) from exc
    if not item:
        raise HTTPException(status_code=404, detail={"code": 40405, "message": "session not found"})
    return ApiResponse(data=item)
