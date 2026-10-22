from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Tests must never touch the real data/ directory. app.core.config resolves
# DATA_DIR at import time, so point it at a throwaway temp folder before any
# app module is imported (conftest is imported before test modules).
_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="child-learning-tests-"))
os.environ["DATA_DIR"] = str(_TEST_DATA_DIR)
atexit.register(shutil.rmtree, _TEST_DATA_DIR, ignore_errors=True)

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402


@pytest.fixture(autouse=True)
def clean_data_dir():
    data_dir = Path(settings.data_dir)
    assert data_dir == _TEST_DATA_DIR, (
        f"settings.data_dir ({data_dir}) does not point to the test data "
        "dir; refusing to wipe it to protect real data"
    )
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    yield
