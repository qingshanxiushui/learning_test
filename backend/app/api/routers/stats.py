from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_parent
from app.models import ApiResponse
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/stats", tags=["stats"])


@router.get("/overview", response_model=ApiResponse)
def overview(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        data = service.stats_overview(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=data)


@router.get("/by-content-type", response_model=ApiResponse)
def by_content_type(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        data = service.stats_by_content_type(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=data)


@router.get("/weak-contents", response_model=ApiResponse)
def weak_contents(
    child_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    content_type: str | None = None,
    current=Depends(get_current_parent),
) -> ApiResponse:
    try:
        data = service.stats_weak_contents(current["user_id"], child_id, limit, content_type)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=data)
