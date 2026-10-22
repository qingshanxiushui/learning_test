from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_parent
from app.models import ApiResponse, RuleCreate
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/rules", tags=["rules"])


@router.get("", response_model=ApiResponse)
def get_rule(child_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        rule = service.get_rule(current["user_id"], child_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    if not rule:
        raise HTTPException(status_code=404, detail={"code": 40404, "message": "rule not found"})
    return ApiResponse(data=rule.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.post("", response_model=ApiResponse, status_code=201)
def create_rule(child_id: str, payload: RuleCreate, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        rule = service.create_rule(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError:
        raise HTTPException(status_code=409, detail={"code": 40902, "message": "rule exists"})
    return ApiResponse(data=rule.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.put("", response_model=ApiResponse)
def update_rule(child_id: str, payload: RuleCreate, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        rule = service.upsert_rule(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=rule.model_dump(exclude={"is_deleted", "deleted_at"}))
