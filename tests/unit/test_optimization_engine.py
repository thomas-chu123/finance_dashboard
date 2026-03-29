"""單元測試 — 馬可維茲投資組合優化引擎."""
import pytest
import allure
import numpy as np
import pandas as pd

from app.services.optimization_engine import run_optimization, _portfolio_performance


@allure.epic("投資組合優化")
@allure.feature("優化引擎")
@pytest.mark.unit
class TestOptimizationEngine:
    """run_optimization 確定性數值測試（直接傳入 DataFrame，無 I/O）."""

    @pytest.fixture
    def simple_prices_df(self):
        """三資產、252 個交易日的模擬價格 DataFrame."""
        rng = np.random.default_rng(42)
        n = 252
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        data = {
            "VTI": 100.0 * np.cumprod(1 + rng.normal(0.0006, 0.010, n)),
            "BND": 100.0 * np.cumprod(1 + rng.normal(0.0002, 0.004, n)),
            "GLD": 100.0 * np.cumprod(1 + rng.normal(0.0004, 0.008, n)),
        }
        return pd.DataFrame(data, index=idx)

    @pytest.fixture
    def two_assets_df(self):
        """最少資產數（2 個）的 DataFrame."""
        rng = np.random.default_rng(99)
        n = 200
        idx = pd.date_range("2023-01-01", periods=n, freq="B")
        data = {
            "A": 100.0 * np.cumprod(1 + rng.normal(0.0005, 0.012, n)),
            "B": 100.0 * np.cumprod(1 + rng.normal(0.0003, 0.006, n)),
        }
        return pd.DataFrame(data, index=idx)

    @allure.story("返回結構")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_result_contains_required_keys(self, simple_prices_df):
        """優化結果應包含 max_sharpe、min_volatility、efficient_frontier、asset_points."""
        result = run_optimization(simple_prices_df)
        assert "error" not in result
        for key in ("max_sharpe", "min_volatility", "efficient_frontier", "asset_points"):
            assert key in result, f"缺少鍵: {key}"

    @allure.story("最大夏普比例")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_max_sharpe_weights_sum_to_one(self, simple_prices_df):
        """最大夏普比例的權重總和應為 100（百分比格式）."""
        result = run_optimization(simple_prices_df)
        weights = list(result["max_sharpe"]["weights"].values())
        assert sum(weights) == pytest.approx(100.0, abs=0.1)

    @allure.story("最小波動")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_min_vol_weights_sum_to_one(self, simple_prices_df):
        """最小波動的權重總和應為 100（百分比格式）."""
        result = run_optimization(simple_prices_df)
        weights = list(result["min_volatility"]["weights"].values())
        assert sum(weights) == pytest.approx(100.0, abs=0.1)

    @allure.story("權重非負")
    def test_weights_non_negative(self, simple_prices_df):
        """所有最優權重應為非負（不允許放空）."""
        result = run_optimization(simple_prices_df)
        for key in ("max_sharpe", "min_volatility"):
            for w in result[key]["weights"].values():
                assert w >= -1e-6, f"{key} 含負權重: {w}"

    @allure.story("最大夏普比例 > 最小波動夏普")
    def test_max_sharpe_better_than_min_vol(self, simple_prices_df):
        """最大夏普的夏普比例應 >= 最小波動的夏普比例."""
        result = run_optimization(simple_prices_df)
        ms_sharpe = result["max_sharpe"].get("sharpe_ratio", 0)
        mv_sharpe = result["min_volatility"].get("sharpe_ratio", 0)
        assert ms_sharpe >= mv_sharpe - 1e-4  # 允許微小數值誤差

    @allure.story("最小波動率 <= 最大夏普波動率")
    def test_min_vol_lower_than_max_sharpe_vol(self, simple_prices_df):
        """最小波動的波動率應 <= 最大夏普的波動率."""
        result = run_optimization(simple_prices_df)
        ms_vol = result["max_sharpe"].get("volatility", 999)
        mv_vol = result["min_volatility"].get("volatility", 999)
        assert mv_vol <= ms_vol + 1e-4

    @allure.story("高效前緣曲線")
    def test_efficient_frontier_has_points(self, simple_prices_df):
        """高效前緣應有數個點."""
        result = run_optimization(simple_prices_df)
        frontier = result["efficient_frontier"]
        assert len(frontier.get("returns", [])) >= 2
        assert len(frontier.get("volatilities", [])) >= 2

    @allure.story("最少資產")
    def test_two_assets_optimization(self, two_assets_df):
        """最少兩個資產應可正常優化."""
        result = run_optimization(two_assets_df)
        assert "error" not in result

    @allure.story("資產不足")
    def test_single_asset_returns_error(self):
        """單一資產應回傳 error（需至少 2 個）."""
        single = pd.DataFrame({"A": [100.0, 101.0, 102.0, 101.0, 103.0] * 50})
        result = run_optimization(single)
        assert "error" in result

    @allure.story("空 DataFrame")
    def test_empty_dataframe_returns_error(self):
        """空 DataFrame 應回傳 error."""
        result = run_optimization(pd.DataFrame())
        assert "error" in result


@allure.epic("投資組合優化")
@allure.feature("投資組合績效計算")
@pytest.mark.unit
class TestPortfolioPerformance:
    """_portfolio_performance 純函數測試."""

    @pytest.fixture
    def two_asset_params(self):
        """兩資產的 mean_returns 與 cov_matrix."""
        mean_returns = pd.Series([0.15, 0.08], index=["A", "B"])  # 年化報酬
        cov_matrix = pd.DataFrame(
            [[0.04, 0.01], [0.01, 0.0225]],
            index=["A", "B"],
            columns=["A", "B"],
        )
        return mean_returns, cov_matrix

    @allure.story("績效計算")
    def test_equal_weight_returns(self, two_asset_params):
        """等權重的期望報酬應為各資產報酬的加權平均."""
        mean_returns, cov_matrix = two_asset_params
        weights = np.array([0.5, 0.5])
        ret, std, sharpe = _portfolio_performance(weights, mean_returns, cov_matrix)
        assert ret == pytest.approx(0.115, abs=1e-10)  # (0.15 + 0.08) / 2

    @allure.story("績效計算")
    def test_sharpe_ratio_positive(self, two_asset_params):
        """正超額報酬應產生正夏普比例."""
        mean_returns, cov_matrix = two_asset_params
        weights = np.array([0.5, 0.5])
        ret, std, sharpe = _portfolio_performance(weights, mean_returns, cov_matrix)
        assert sharpe > 0.0
