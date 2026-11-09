from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import auth, children, contents, math, parents, pinyin, reading, rules, sessions, stats
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
app.include_router(pinyin.router, prefix=settings.api_prefix)
app.include_router(reading.router, prefix=settings.api_prefix)
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


# ---------------------------------------------------------------------------
# 前端 SPA 托管：将 Vite 构建产物（app/web）由 FastAPI 直接提供，
# 实现「后端单端口对外暴露整个应用」的部署方式。
# 仅当构建目录存在时启用；开发期可继续使用 Vite dev server + /api 代理。
# ---------------------------------------------------------------------------
_WEB_DIST_DIR = Path(__file__).parent / "web"
_WEB_INDEX_FILE = _WEB_DIST_DIR / "index.html"

if _WEB_INDEX_FILE.exists():
    _assets_dir = _WEB_DIST_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    async def _spa_root() -> FileResponse:
        """返回 SPA 入口页面。"""
        return FileResponse(_WEB_INDEX_FILE)

    @app.get("/{spa_path:path}", include_in_schema=False)
    async def _spa_fallback(spa_path: str) -> FileResponse:
        """SPA 路由回退：API/docs 之外的路径统一返回 index.html。"""
        reserved_prefixes = ("api", "docs", "redoc", "openapi.json")
        if spa_path.startswith(reserved_prefixes):
            raise HTTPException(status_code=404)
        candidate = (_WEB_DIST_DIR / spa_path).resolve()
        try:
            candidate.relative_to(_WEB_DIST_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=404)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_WEB_INDEX_FILE)
