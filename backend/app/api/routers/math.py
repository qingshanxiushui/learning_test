from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_parent
from app.models import ApiResponse, MathSettingsUpsert
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/math-settings", tags=["math"])


@router.get("", response_model=ApiResponse)
def get_math_settings(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        settings = service.get_math_settings(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    data = settings.model_dump(exclude={"is_deleted", "deleted_at"}) if settings else None
    return ApiResponse(data=data)


@router.put("", response_model=ApiResponse)
def update_math_settings(
    child_id: str, payload: MathSettingsUpsert, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        settings = service.upsert_math_settings(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42207, "message": str(exc)}) from exc
    return ApiResponse(data=settings.model_dump(exclude={"is_deleted", "deleted_at"}))
