from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}

    def _lock(self, path: Path) -> threading.Lock:
        key = str(path.resolve())
        if key not in self._locks:
            self._locks[key] = threading.Lock()
        return self._locks[key]

    def _full_path(self, rel: str) -> Path:
        path = self.data_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
        return path

    def read_list(self, rel: str) -> list[dict[str, Any]]:
        path = self._full_path(rel)
        with self._lock(path):
            content = path.read_text(encoding="utf-8").strip() or "[]"
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError(f"data file is not a list: {rel}")
            return data

    def write_list(self, rel: str, data: list[dict[str, Any]]) -> None:
        path = self._full_path(rel)
        with self._lock(path):
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            # Windows 下杀软/系统可能短暂锁定临时文件导致 os.replace 偶发 PermissionError，
            # 做有限次重试以保证原子替换写入稳定。
            last_error: Exception | None = None
            for attempt in range(5):
                try:
                    tmp.replace(path)
                    return
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.05 * (attempt + 1))
            if last_error:
                raise last_error
