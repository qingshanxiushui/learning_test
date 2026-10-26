from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_parent
from app.models import (
    ApiResponse,
    CharacterBatchCreate,
    ClassicBatchCreate,
    ContentCreate,
    ContentStatusUpdate,
    ContentUpdate,
    EnglishBatchCreate,
    IdiomBatchCreate,
    PoemBatchCreate,
)
from app.services.parent_service import service

router = APIRouter(prefix="/children/{child_id}/contents", tags=["contents"])


@router.get("", response_model=ApiResponse)
def list_contents(
    child_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    content_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    sort_by: str | None = None,
    sort_order: str = Query(default="asc"),
    current=Depends(get_current_parent),
) -> ApiResponse:
    try:
        items, total = service.list_contents_with_stats(
            current["user_id"], child_id, page, page_size, content_type, status, keyword, sort_by, sort_order
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data={"list": items, "pagination": {"page": page, "page_size": page_size, "total": total}})


@router.post("", response_model=ApiResponse, status_code=201)
def create_content(child_id: str, payload: ContentCreate, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        item = service.create_content(current["user_id"], child_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    return ApiResponse(data=item.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.post("/characters/batch", response_model=ApiResponse, status_code=201)
def batch_upsert_characters(
    child_id: str, payload: CharacterBatchCreate, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        items, created_count, updated_count = service.batch_upsert_characters(
            current["user_id"], child_id, payload
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42206, "message": str(exc)}) from exc
    return ApiResponse(
        data={
            "list": [item.model_dump(exclude={"is_deleted", "deleted_at"}) for item in items],
            "created_count": created_count,
            "updated_count": updated_count,
            "total_count": len(items),
        }
    )


@router.post("/english/batch", response_model=ApiResponse, status_code=201)
def batch_upsert_english_words(
    child_id: str, payload: EnglishBatchCreate, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        items, created_count, updated_count = service.batch_upsert_english_words(
            current["user_id"], child_id, payload
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42206, "message": str(exc)}) from exc
    return ApiResponse(
        data={
            "list": [item.model_dump(exclude={"is_deleted", "deleted_at"}) for item in items],
            "created_count": created_count,
            "updated_count": updated_count,
            "total_count": len(items),
        }
    )


@router.post("/poems/batch", response_model=ApiResponse, status_code=201)
def batch_upsert_poems(
    child_id: str, payload: PoemBatchCreate, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        items, created_count, updated_count = service.batch_upsert_poems(
            current["user_id"], child_id, payload
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42206, "message": str(exc)}) from exc
    return ApiResponse(
        data={
            "list": [item.model_dump(exclude={"is_deleted", "deleted_at"}) for item in items],
            "created_count": created_count,
            "updated_count": updated_count,
            "total_count": len(items),
        }
    )


@router.post("/idioms/batch", response_model=ApiResponse, status_code=201)
def batch_upsert_idioms(
    child_id: str, payload: IdiomBatchCreate, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        items, created_count, updated_count = service.batch_upsert_idioms(
            current["user_id"], child_id, payload
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42206, "message": str(exc)}) from exc
    return ApiResponse(
        data={
            "list": [item.model_dump(exclude={"is_deleted", "deleted_at"}) for item in items],
            "created_count": created_count,
            "updated_count": updated_count,
            "total_count": len(items),
        }
    )


@router.post("/classics/batch", response_model=ApiResponse, status_code=201)
def batch_upsert_classics(
    child_id: str, payload: ClassicBatchCreate, current=Depends(get_current_parent)
) -> ApiResponse:
    try:
        items, created_count, updated_count = service.batch_upsert_classics(
            current["user_id"], child_id, payload
        )
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": 42206, "message": str(exc)}) from exc
    return ApiResponse(
        data={
            "list": [item.model_dump(exclude={"is_deleted", "deleted_at"}) for item in items],
            "created_count": created_count,
            "updated_count": updated_count,
            "total_count": len(items),
        }
    )


@router.get("/{content_id}", response_model=ApiResponse)
def get_content(child_id: str, content_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        item = service.get_content(current["user_id"], child_id, content_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    if not item:
        raise HTTPException(status_code=404, detail={"code": 40403, "message": "content not found"})
    return ApiResponse(data=item.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.put("/{content_id}", response_model=ApiResponse)
def update_content(child_id: str, content_id: str, payload: ContentUpdate, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        item = service.update_content(current["user_id"], child_id, content_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    if not item:
        raise HTTPException(status_code=404, detail={"code": 40403, "message": "content not found"})
    return ApiResponse(data=item.model_dump(exclude={"is_deleted", "deleted_at"}))


@router.delete("/{content_id}", response_model=ApiResponse)
def delete_content(child_id: str, content_id: str, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        ok = service.delete_content(current["user_id"], child_id, content_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    if not ok:
        raise HTTPException(status_code=404, detail={"code": 40403, "message": "content not found"})
    return ApiResponse(data={"deleted": True})


@router.patch("/{content_id}/status", response_model=ApiResponse)
def patch_content_status(child_id: str, content_id: str, payload: ContentStatusUpdate, current=Depends(get_current_parent)) -> ApiResponse:
    try:
        item = service.update_content_status(current["user_id"], child_id, content_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail={"code": 40402, "message": "child not found"})
    if not item:
        raise HTTPException(status_code=404, detail={"code": 40403, "message": "content not found"})
    return ApiResponse(data=item.model_dump(exclude={"is_deleted", "deleted_at"}))
