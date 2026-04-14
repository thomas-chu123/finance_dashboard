"""單元測試 — 回測引擎（純函數 + mock 整合測試）."""
import pytest
import allure
import asyncio
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, patch

from app.services.backtest_engine import (
    _annualized_return,
    _max_drawdown,
    _sharpe_ratio,
    _sortino_ratio,
    _beta,
    _var_historical,
    _cvar,
    run_backtest,
    RISK_FREE_RATE,
)


# ── 測試資料工廠 ─────────────────────────────────────────────────────────────

def _make_prices(n: int = 252, start: float = 100.0, daily_return: float = 0.001) -> pd.Series:
    """產生具有固定日報酬的模擬價格序列."""
    prices = [start * (1 + daily_return) ** i for i in range(n)]
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.Series(prices, index=idx)


def _make_returns(n: int = 252, mean: float = 0.001, std: float = 0.01, seed: int = 42) -> pd.Series:
    """產生常態分布的日報酬序列."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mean, std, n))


# ── 純函數測試 ────────────────────────────────────────────────────────────────

@allure.epic("回測引擎")
@allure.feature("純計算函數")
@pytest.mark.unit
class TestBacktestPureFunctions:
    """回測引擎純函數測試（無 I/O）."""

    @allure.story("年化報酬率")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_annualized_return_basic(self):
        """100% 累積報酬在 2 年約等於 41.4% CAGR."""
        result = _annualized_return(1.0, years=2.0)
        assert result == pytest.approx((2.0 ** 0.5) - 1, rel=1e-6)

    @allure.story("年化報酬率")
    def test_annualized_return_zero_years(self):
        """年數為 0 時應回傳 0（避免除以零）."""
        assert _annualized_return(0.5, years=0) == 0.0

    @allure.story("年化報酬率")
    def test_annualized_return_negative_years(self):
        """年數為負時應回傳 0."""
        assert _annualized_return(0.5, years=-1) == 0.0

    @allure.story("最大回撤")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_max_drawdown_no_drawdown(self):
        """持續上漲的序列最大回撤應為 0."""
        prices = _make_prices(50, daily_return=0.001)
        dd = _max_drawdown(prices)
        assert dd == pytest.approx(0.0, abs=1e-10)

    @allure.story("最大回撤")
    def test_max_drawdown_known_value(self):
        """從 100 跌至 50 再回升至 60，最大回撤應為 -50%."""
        prices = pd.Series([100.0, 80.0, 60.0, 50.0, 55.0, 60.0])
        dd = _max_drawdown(prices)
        assert dd == pytest.approx(-0.5, rel=1e-6)

    @allure.story("夏普比例")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_sharpe_ratio_positive_for_positive_excess_return(self):
        """正超額報酬應產生正夏普比例."""
        returns = _make_returns(n=500, mean=0.0015, std=0.01)
        sharpe = _sharpe_ratio(returns)
        assert sharpe > 0.0

    @allure.story("夏普比例")
    def test_sharpe_ratio_zero_vol_returns_zero(self):
        """零報酬序列（均值與波動度皆為 0）應回傳 0.0."""
        returns = pd.Series([0.0] * 252)  # 所有報酬為 0 → std=0 → 觸發保護邏輯
        sharpe = _sharpe_ratio(returns)
        assert sharpe == 0.0

    @allure.story("索提諾比例")
    def test_sortino_ratio_positive_for_positive_return(self):
        """正報酬、有下行波動時索提諾應為正值."""
        returns = _make_returns(n=500, mean=0.001, std=0.015)
        sortino = _sortino_ratio(returns)
        assert sortino > 0.0

    @allure.story("Beta")
    def test_beta_perfect_correlation(self):
        """完全正相關的組合 beta 應接近 1.0."""
        r = _make_returns(n=200, mean=0.001, std=0.01)
        beta = _beta(r, r)  # 和自已比較
        assert beta == pytest.approx(1.0, rel=1e-4)

    @allure.story("Beta")
    def test_beta_insufficient_data_returns_one(self):
        """少於 10 個數據點應回傳預設值 1.0."""
        r = pd.Series([0.01] * 5)
        assert _beta(r, r) == 1.0

    @allure.story("VaR")
    @allure.severity(allure.severity_level.NORMAL)
    def test_var_historical_is_negative(self):
        """歷史 VaR（95%）對常態分布應為負值."""
        returns = _make_returns(n=252)
        var = _var_historical(returns, confidence=0.95)
        assert var < 0.0

    @allure.story("CVaR")
    def test_cvar_worse_than_var(self):
        """CVaR 應比 VaR 更差（更負）."""
        returns = _make_returns(n=252)
        var = _var_historical(returns, confidence=0.95)
        cvar = _cvar(returns, confidence=0.95)
        assert cvar <= var


# ── 整合測試（mock get_historical_prices）────────────────────────────────────

@allure.epic("回測引擎")
@allure.feature("run_backtest 整合測試")
@pytest.mark.unit
class TestRunBacktest:
    """run_backtest 非同步函數整合測試（mock 市場數據）."""

    def _mock_prices(self, symbol: str, *args, **kwargs) -> pd.Series:
        """產生確定性的模擬歷史價格 Series（與 get_historical_prices 回傳格式一致）."""
        n = 500
        rng = np.random.default_rng(hash(symbol) % 2**32)
        prices = 100.0 * np.cumprod(1 + rng.normal(0.0005, 0.01, n))
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        return pd.Series(prices, index=idx, name="Close")

    @allure.story("正常雙資產回測")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.asyncio
    async def test_run_backtest_returns_metrics(self):
        """run_backtest 應回傳包含關鍵指標欄位的結果."""
        items = [
            {"symbol": "VTI", "weight": 70.0, "name": "Vanguard Total", "category": "us_etf"},
            {"symbol": "BND", "weight": 30.0, "name": "Vanguard Bond", "category": "us_etf"},
        ]
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=self._mock_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            result = await run_backtest(
                items, "2022-01-01", "2023-12-31", initial_amount=100000.0
            )

        assert "error" not in result
        metrics = result.get("metrics", {})
        for key in ("cagr", "sharpe_ratio", "max_drawdown", "total_return"):
            assert key in metrics, f"metrics 缺少欄位: {key}"

    @allure.story("結果包含時間序列")
    @pytest.mark.asyncio
    async def test_run_backtest_contains_series(self):
        """run_backtest 應包含 portfolio_value_series 時間序列."""
        items = [
            {"symbol": "SPY", "weight": 100.0, "name": "S&P 500", "category": "us_etf"},
        ]
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=self._mock_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            result = await run_backtest(items, "2022-01-01", "2023-12-31")

        assert "portfolio_value_series" in result
        assert len(result["portfolio_value_series"]) > 0

    @allure.story("空資產清單")
    @pytest.mark.asyncio
    async def test_run_backtest_empty_items_returns_error(self):
        """空資產清單應在 router 層被攔截（此處測試引擎行為）."""
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=self._mock_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            result = await run_backtest([], "2022-01-01", "2023-12-31")
        # 引擎應回傳 error 或空結果
        assert "error" in result or result == {} or not result.get("metrics")

    @allure.story("資產貢獻匹配")
    @pytest.mark.asyncio
    async def test_asset_contributions_sum_equals_final_amount(self):
        """資產期末值加總應等於投資組合最終值（精確匹配）."""
        items = [
            {"symbol": "VTI", "weight": 40.0, "name": "Vanguard Total", "category": "us_etf"},
            {"symbol": "BND", "weight": 35.0, "name": "Vanguard Bond", "category": "us_etf"},
            {"symbol": "VEA", "weight": 25.0, "name": "Vanguard International", "category": "us_etf"},
        ]
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=self._mock_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            result = await run_backtest(
                items, "2022-01-01", "2023-12-31", initial_amount=100000.0
            )

        assert "error" not in result
        metrics = result.get("metrics", {})
        asset_contributions = result.get("asset_contributions", {})
        
        final_amount = metrics.get("final_amount", 0)
        # 使用新的 final_value 欄位計算期末值之和
        contrib_sum = sum([v.get("final_value", 0) for v in asset_contributions.values()])
        
        # 資產期末值加總應精確等於最終值（允許浮點誤差）
        assert abs(final_amount - contrib_sum) < 0.02, \
            f"Final amount {final_amount} != sum of contributions {contrib_sum}"
