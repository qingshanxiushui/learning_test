from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_parent
from app.core.security import create_access_token
from app.models import ApiResponse, LoginRequest
from app.services.parent_service import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest) -> ApiResponse:
    user = service.auth_parent(payload.account_name, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail={"code": 40102, "message": "account or password invalid"})
    token = create_access_token({"user_id": user.id, "account_name": user.account_name})
    return ApiResponse(
        data={
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 7200,
            "user": {"id": user.id, "account_name": user.account_name, "display_name": user.display_name},
        }
    )


@router.get("/me", response_model=ApiResponse)
def me(current=Depends(get_current_parent)) -> ApiResponse:
    return ApiResponse(data={"id": current["user_id"], "account_name": current["account_name"], "display_name": current["display_name"], "status": "active"})
