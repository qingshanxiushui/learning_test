from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.security import decode_access_token
from app.services.parent_service import service


def get_current_parent(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": 40101, "message": "token missing"})
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        detail = str(exc)
        if "expired" in detail:
            raise HTTPException(status_code=401, detail={"code": 40103, "message": "token expired"}) from exc
        raise HTTPException(status_code=401, detail={"code": 40102, "message": "token invalid"}) from exc
    parent = service.get_parent(payload.get("user_id", ""))
    if not parent:
        raise HTTPException(status_code=404, detail={"code": 40401, "message": "parent not found"})
    return {"user_id": parent.id, "account_name": parent.account_name, "display_name": parent.display_name}
