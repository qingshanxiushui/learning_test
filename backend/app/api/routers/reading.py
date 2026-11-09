from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_parent
from app.models import ApiResponse, ReadingSettingsUpsert
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/reading-settings", tags=["reading"])


@router.get("", response_model=ApiResponse)
def get_reading_settings(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        settings = service.get_reading_settings(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    data = settings.model_dump(exclude={"is_deleted", "deleted_at"}) if settings else None
    return ApiResponse(data=data)


@router.put("", response_model=ApiResponse)
def update_reading_settings(
    child_id: str, payload: ReadingSettingsUpsert, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        settings = service.upsert_reading_settings(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=settings.model_dump(exclude={"is_deleted", "deleted_at"}))
