from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_parent
from app.models import ApiResponse, ChildCreate, ChildUpdate
from app.services.parent_service import service

router = APIRouter(prefix="/children", tags=["children"])


@router.get("", response_model=ApiResponse)
def list_children(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = None,
    current=Depends(get_current_parent),
) -> ApiResponse:
    items, total = service.list_children(current["user_id"], status, page, page_size)
    return ApiResponse(data={"list": [i.model_dump(exclude={"is_deleted", "deleted_at"}) for i in items], "pagination": {"page": page, "page_size": page_size, "total": total}})


@router.post("", response_model=ApiResponse, status_code=201)
def create_child(payload: ChildCreate, current=Depends(get_current_parent)) -> ApiResponse:
    child = service.create_child(current["user_id"], payload)
    return ApiResponse(data=child.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.get("/{child_id}", response_model=ApiResponse)
def get_child(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    child = service.get_child(current["user_id"], child_id)
    if not child:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=child.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.put("/{child_id}", response_model=ApiResponse)
def update_child(child_id: str, payload: ChildUpdate, current=Depends(get_current_parent)) -> ApiResponse:
    child = service.update_child(current["user_id"], child_id, payload)
    if not child:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=child.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.delete("/{child_id}", response_model=ApiResponse)
def delete_child(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    deleted = service.delete_child(current["user_id"], child_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data={"deleted": True})
