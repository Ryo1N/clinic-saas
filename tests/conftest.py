# tests/conftest.py
import base64
import os
import tempfile
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from app.db import init_db


# アプリ読み込み
os.environ.setdefault("BASIC_AUTH_USERNAME", "doctor")
os.environ.setdefault("BASIC_AUTH_PASSWORD", "change-me")

# 一時DBへ差し替え（ローカルsqliteファイル）
TMPDIR = tempfile.mkdtemp(prefix="clinic_saas_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{TMPDIR}/test.db"

from app.main import app
from app.db import init_db

@pytest.fixture(scope="session")
def client():
    init_db()  # テーブル作成＆Doctor初期化
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_header():
    raw = "doctor:change-me".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}

# UTC ISO 生成ユーティリティ（丸め込み付き）
def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

@pytest.fixture
def tomorrow_10_to_noon():
    base = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    # 明日10:00〜12:00（UTC）
    start = (base + timedelta(days=1)).replace(hour=10, minute=0)
    end   = start.replace(hour=12, minute=0)
    return iso(start), iso(end)

@pytest.fixture
def day_window():
    # 直近7日のスロット確認用ウィンドウ
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return iso(start), iso(end)

@pytest.fixture(autouse=True)
def _reset_db_per_test():
    """
    Drops and recreates DB (including Doctor).
    This avoids Availability or Appointments remaining between tests.
    """
    # app.db 側に engine が定義されている前提
    from app.db import engine

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    init_db()  # Doctorレコードの作成など、あなたのinit_dbが行う初期化
