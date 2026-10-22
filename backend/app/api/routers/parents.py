from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, ParentCreate
from app.services.parent_service import service

router = APIRouter(prefix="/parents", tags=["parents"])


@router.post("", response_model=ApiResponse, status_code=201)
def create_parent(payload: ParentCreate) -> ApiResponse:
    try:
        parent = service.create_parent(payload)
    except ValueError:
        raise HTTPException(status_code=409, detail={"code": 40901, "message": "account exists"})
    data = parent.model_dump()
    data.pop("password", None)
    return ApiResponse(data=data)
