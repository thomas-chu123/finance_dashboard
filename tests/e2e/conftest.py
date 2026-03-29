"""E2E conftest.py — FastAPI TestClient 與 Mock 基礎設施."""
import sys
import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# ── 確保 backend 模組可存取
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "backend"))

# ── 設定測試環境變數（必須在 app import 之前）
os.environ["SECRET_KEY"] = "test-e2e-secret-key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["APP_BASE_URL"] = "http://localhost:5173"


# ── Supabase Mock 工廠 ────────────────────────────────────────────────────────

def make_supabase_mock(rows: list = None) -> MagicMock:
    """
    建立一個通用的 Supabase Mock，預設回傳空資料列表。
    
    Args:
        rows: 模擬 .data 回傳值（預設為空列表）
    
    設計重點：read 與 write 操作使用獨立的 mock 鏈，避免互相干擾。
    """
    rows = rows or []

    # ── 讀取操作 mock（select 鏈）───────────────────────────────────────────
    read_result = MagicMock()
    read_result.data = rows

    read_query = MagicMock()
    read_query.execute.return_value = read_result
    read_query.select.return_value = read_query
    read_query.eq.return_value = read_query
    read_query.neq.return_value = read_query
    read_query.in_.return_value = read_query
    read_query.order.return_value = read_query
    read_query.limit.return_value = read_query

    # ── 寫入操作 mock（insert / update / delete / upsert 鏈）────────────────
    write_result = MagicMock()
    # write 操作也回傳相同的 rows，讓 response_model 驗證可以通過
    write_result.data = rows if rows else [{"id": "mock-write-id"}]

    write_query = MagicMock()
    write_query.execute.return_value = write_result
    write_query.eq.return_value = write_query
    write_query.neq.return_value = write_query
    write_query.select.return_value = write_query

    # ── 表格 Mock，區分 select 起點與 write 起點 ─────────────────────────────
    table_mock = MagicMock()
    table_mock.select.return_value = read_query     # SELECT 進入 read chain
    table_mock.insert.return_value = write_query    # INSERT 進入 write chain
    table_mock.update.return_value = write_query    # UPDATE 進入 write chain
    table_mock.delete.return_value = write_query    # DELETE 進入 write chain
    table_mock.upsert.return_value = write_query    # UPSERT 進入 write chain

    mock_sb = MagicMock()
    mock_sb.table.return_value = table_mock
    # 暴露底層方便個別測試覆寫
    mock_sb._read_result = read_result
    mock_sb._write_result = write_result
    mock_sb._read_query = read_query
    mock_sb._write_query = write_query
    mock_sb._table = table_mock
    return mock_sb


# ── JWT 令牌工廠 ─────────────────────────────────────────────────────────────

def make_test_token(user_id: str = "test-user-001", email: str = "test@example.com") -> str:
    """為測試建立有效的 JWT 令牌."""
    from app.security import create_access_token
    from datetime import timedelta
    return create_access_token(
        {"sub": user_id, "email": email},
        expires_delta=timedelta(hours=1),
    )


# ── 共用 Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_user_id() -> str:
    return "test-user-001"


@pytest.fixture(scope="session")
def auth_headers(test_user_id: str) -> dict:
    """回傳含有效 JWT 的 Authorization 標頭."""
    token = make_test_token(user_id=test_user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def app_client() -> Generator:
    """
    建立全域 FastAPI TestClient（Session 範圍）。
    - 使用 InMemoryBackend 取代 Redis
    - Mock get_supabase() 避免真實 DB 連線
    - 停用 APScheduler
    """
    # 初始化 FastAPICache 為 InMemoryBackend（在 import app 前必須設好）
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend
    FastAPICache.init(InMemoryBackend(), prefix="test-cache")

    mock_sb = make_supabase_mock()

    with patch("app.database.get_supabase", return_value=mock_sb), \
         patch("app.scheduler.start_scheduler"), \
         patch("app.scheduler.scheduler") as mock_scheduler:
        mock_scheduler.running = False

        from app.main import app
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


@pytest.fixture
def client(app_client) -> TestClient:
    """為每個測試提供 TestClient（重用 session 範圍的 app）."""
    return app_client


@pytest.fixture
def mock_sb():
    """提供乾淨的 Supabase Mock（每個測試獨立）."""
    return make_supabase_mock()


# ── 追蹤項目測試資料 ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_tracking_row() -> dict:
    """模擬 Supabase 回傳的追蹤項目資料列."""
    return {
        "id": "tracking-001",
        "user_id": "test-user-001",
        "symbol": "VTI",
        "name": "Vanguard Total Stock",
        "category": "us_etf",
        "trigger_price": 250.0,
        "trigger_direction": "above",
        "current_price": 255.0,
        "trigger_mode": "price",
        "rsi_period": 14,
        "current_rsi": None,
        "rsi_below": None,
        "rsi_above": None,
        "notify_channel": "email",
        "is_active": True,
        "alert_triggered": False,
        "last_notified_at": None,
        "notes": None,
        "created_at": "2024-01-01T00:00:00Z",
    }
