from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import auth, children, contents, math, parents, rules, sessions, stats
from app.core.config import settings
from app.models import ApiResponse

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(parents.router, prefix=settings.api_prefix)
app.include_router(children.router, prefix=settings.api_prefix)
app.include_router(contents.router, prefix=settings.api_prefix)
app.include_router(rules.router, prefix=settings.api_prefix)
app.include_router(math.router, prefix=settings.api_prefix)
app.include_router(sessions.router, prefix=settings.api_prefix)
app.include_router(stats.router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": exc.status_code, "message": str(exc.detail)}
    response = ApiResponse(code=int(detail.get("code", exc.status_code)), message=str(detail.get("message", "error")), data=None)
    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    response = ApiResponse(code=50001, message="internal server error", data=None)
    return JSONResponse(status_code=500, content=response.model_dump())
