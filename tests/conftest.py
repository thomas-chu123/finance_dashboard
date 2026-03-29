"""根層 conftest.py — 全域 fixture 與環境設定."""
import sys
import os
from pathlib import Path
import pytest

# ── 確保 backend/ 在 PYTHONPATH（pytest.ini 的 pythonpath 已處理，這是安全後備）
BACKEND_PATH = Path(__file__).parent.parent / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# ── 測試使用的 env 變數（覆蓋 .env，避免讀到正式環境配置）
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/99")  # 測試 DB
os.environ.setdefault("APP_BASE_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def test_jwt_secret() -> str:
    """返回測試用 JWT 密鑰."""
    return "test-secret-key-for-pytest-only"


@pytest.fixture
def sample_prices_rising():
    """模擬持續上升的價格序列（15 個點，可測 RSI 計算）."""
    return [float(i) for i in range(1, 20)]


@pytest.fixture
def sample_prices_falling():
    """模擬持續下降的價格序列."""
    return [float(i) for i in range(20, 0, -1)]


@pytest.fixture
def sample_prices_mixed():
    """模擬振盪的價格序列（適合 RSI 計算）."""
    return [
        44.34, 44.09, 44.15, 43.61, 44.33,
        44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.00,
        45.32, 45.78, 46.12, 45.95, 46.40,
    ]
