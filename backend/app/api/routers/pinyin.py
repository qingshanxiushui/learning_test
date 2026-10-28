from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_parent
from app.models import ApiResponse, PinyinSettingsUpsert
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/pinyin-settings", tags=["pinyin"])


@router.get("", response_model=ApiResponse)
def get_pinyin_settings(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        settings = service.get_pinyin_settings(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    data = settings.model_dump(exclude={"is_deleted", "deleted_at"}) if settings else None
    return ApiResponse(data=data)


@router.put("", response_model=ApiResponse)
def update_pinyin_settings(
    child_id: str, payload: PinyinSettingsUpsert, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        settings = service.upsert_pinyin_settings(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42209, "message": str(exc)}) from exc
    return ApiResponse(data=settings.model_dump(exclude={"is_deleted", "deleted_at"}))
