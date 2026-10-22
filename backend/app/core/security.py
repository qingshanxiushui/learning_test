from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.core.config import settings


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(payload: dict[str, Any], expire_seconds: int | None = None) -> str:
    now = int(time.time())
    exp = now + (expire_seconds or settings.token_expire_seconds)
    body = {**payload, "iat": now, "exp": exp}
    body_raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    body_enc = _b64_encode(body_raw)
    sig = hmac.new(settings.secret_key.encode("utf-8"), body_enc.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body_enc}.{sig}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        body_enc, sig = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("invalid token format") from exc

    expected = hmac.new(settings.secret_key.encode("utf-8"), body_enc.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid token signature")

    payload = json.loads(_b64_decode(body_enc))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expired")
    return payload
