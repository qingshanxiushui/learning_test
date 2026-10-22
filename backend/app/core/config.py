from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Child Learning Assistant API"
    api_prefix: str = "/api/v1"
    token_expire_seconds: int = 7200
    secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret-key")
    data_dir: Path = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[3] / "data"))
    management_account_name: str = os.getenv("MANAGEMENT_ACCOUNT_NAME", "admin")
    management_password: str = os.getenv("MANAGEMENT_PASSWORD", "dqshuchen")
    management_display_name: str = os.getenv("MANAGEMENT_DISPLAY_NAME", "Administrator")
    management_user_id: str = os.getenv("MANAGEMENT_USER_ID", "parent_admin")
    cors_allow_origins: tuple[str, ...] = tuple(_csv_env("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"))


settings = Settings()
