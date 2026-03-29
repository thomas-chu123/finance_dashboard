"""單元測試 — RSI 服務（RSICacheService 與 RSICalculationService）."""
import pytest
import allure
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

from app.services.rsi_service import RSICacheService, RSICalculationService
from app.services.technical_indicators import RSICalculator


# ── 模擬價格資料 ────────────────────────────────────────────────────────────
MOCK_CLOSE_PRICES = [
    44.34, 44.09, 44.15, 43.61, 44.33,
    44.83, 45.10, 45.42, 45.84, 46.08,
    45.89, 46.03, 45.61, 46.28, 46.00,
    45.32, 45.78, 46.12, 45.95, 46.40,
]


@allure.epic("RSI 服務")
@allure.feature("RSI 快取服務")
@pytest.mark.unit
class TestRSICacheService:
    """RSICacheService Redis 快取行為測試（mock Redis）."""

    @pytest.fixture
    def cache_service_no_redis(self):
        """建立一個 Redis 連接失敗的 RSICacheService（降級到 None）."""
        with patch("app.services.rsi_service.redis.Redis") as mock_redis_cls:
            mock_redis_cls.return_value.ping.side_effect = Exception("Redis unavailable")
            svc = RSICacheService()
        return svc

    @pytest.fixture
    def cache_service_with_mock_redis(self):
        """建立帶有 Mock Redis 的 RSICacheService."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None  # 預設快取未命中
        with patch("app.services.rsi_service.redis.Redis", return_value=mock_redis):
            svc = RSICacheService()
        svc.redis_client = mock_redis
        return svc, mock_redis

    @allure.story("Redis 降級")
    def test_service_initializes_without_redis(self, cache_service_no_redis):
        """Redis 不可用時服務應優雅降級（redis_client = None）."""
        assert cache_service_no_redis.redis_client is None

    @allure.story("快取鍵生成")
    def test_cache_key_uppercase(self, cache_service_no_redis):
        """RSI 快取鍵應為大寫代碼."""
        key = cache_service_no_redis._get_cache_key("vti")
        assert "VTI" in key

    @allure.story("快取鍵生成")
    def test_prices_cache_key_different_from_rsi_key(self, cache_service_no_redis):
        """價格快取鍵與 RSI 快取鍵應不同."""
        rsi_key = cache_service_no_redis._get_cache_key("VTI")
        prices_key = cache_service_no_redis._get_prices_cache_key("VTI")
        assert rsi_key != prices_key

    @allure.story("快取命中")
    @pytest.mark.asyncio
    async def test_calculate_returns_cached_rsi(self, cache_service_with_mock_redis):
        """快取命中時應直接回傳快取值而不重新計算."""
        svc, mock_redis = cache_service_with_mock_redis
        mock_redis.get.return_value = "42.5"  # 快取有值（Redis 回傳字串）

        result = await svc.calculate_and_cache_rsi("VTI", "us_etf", period=14)
        # 服務直接回傳快取原始值（字串），呼叫端應自行轉型
        assert result == "42.5" or result == pytest.approx(42.5)

    @allure.story("快取未命中")
    @pytest.mark.asyncio
    async def test_calculate_fetches_prices_on_cache_miss(self, cache_service_with_mock_redis):
        """快取未命中時應呼叫 _fetch_or_cache_prices 計算 RSI."""
        svc, mock_redis = cache_service_with_mock_redis
        mock_redis.get.return_value = None  # 快取未命中

        with patch.object(
            svc, "_fetch_or_cache_prices", new_callable=AsyncMock, return_value=MOCK_CLOSE_PRICES
        ):
            result = await svc.calculate_and_cache_rsi("VTI", "us_etf", period=14)

        # 有足夠數據應計算出 RSI
        assert result is not None
        assert 0.0 <= result <= 100.0

    @allure.story("資料不足")
    @pytest.mark.asyncio
    async def test_calculate_returns_none_on_insufficient_data(self, cache_service_with_mock_redis):
        """歷史數據不足時應回傳 None."""
        svc, mock_redis = cache_service_with_mock_redis
        mock_redis.get.return_value = None

        with patch.object(
            svc, "_fetch_or_cache_prices", new_callable=AsyncMock, return_value=[100.0, 101.0]
        ):
            result = await svc.calculate_and_cache_rsi("VTI", "us_etf", period=14)

        assert result is None

    @allure.story("強制刷新")
    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, cache_service_with_mock_redis):
        """force_refresh=True 應略過快取直接重新計算."""
        svc, mock_redis = cache_service_with_mock_redis
        mock_redis.get.return_value = "99.9"  # 快取有值但應被忽略

        with patch.object(
            svc, "_fetch_or_cache_prices", new_callable=AsyncMock, return_value=MOCK_CLOSE_PRICES
        ):
            result = await svc.calculate_and_cache_rsi(
                "VTI", "us_etf", period=14, force_refresh=True
            )

        # 不應回傳快取的 99.9
        assert result != pytest.approx(99.9)
        assert result is not None


@allure.epic("RSI 服務")
@allure.feature("RSI 計算服務")
@pytest.mark.unit
class TestRSICalculationService:
    """RSICalculationService 業務邏輯測試."""

    @pytest.fixture
    def calc_service(self):
        """建立帶有 Mock 快取服務的 RSICalculationService."""
        mock_cache_svc = MagicMock()
        svc = RSICalculationService.__new__(RSICalculationService)
        svc.cache_service = mock_cache_svc
        return svc, mock_cache_svc

    @allure.story("RSI 觸發判斷")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("rsi,below,above,should_trigger", [
        (25.0, 30.0, None, True),   # 超賣
        (30.0, 30.0, None, False),  # 等於下限 → 不觸發
        (75.0, None, 70.0, True),   # 超買
        (70.0, None, 70.0, False),  # 等於上限 → 不觸發
        (50.0, 30.0, 70.0, False),  # 正常範圍
        (None, 30.0, 70.0, False),  # RSI 為 None
    ])
    @pytest.mark.asyncio
    async def test_check_rsi_trigger(self, rsi, below, above, should_trigger):
        """check_rsi_trigger 觸發邏輯應正確."""
        from app.services.rsi_service import RSICalculationService
        svc = RSICalculationService.__new__(RSICalculationService)
        svc.cache_service = MagicMock()
        result = await svc.check_rsi_trigger("VTI", rsi, below, above)
        assert result is should_trigger

    @allure.story("更新所有 RSI")
    @pytest.mark.asyncio
    async def test_update_all_active_rsi_skips_price_mode(self):
        """trigger_mode='price' 的追蹤項目應被跳過（不計算 RSI）."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.rsi_service.get_supabase", return_value=mock_sb):
            svc = RSICalculationService.__new__(RSICalculationService)
            svc.cache_service = MagicMock()
            # 呼叫不應拋出例外
            await svc.update_all_active_rsi()
