"""E2E 測試 — 回測端點."""
import pytest
import allure
import pandas as pd
import numpy as np
from unittest.mock import patch, AsyncMock

from tests.e2e.conftest import make_supabase_mock


def _mock_backtest_prices(symbol: str, *args, **kwargs) -> pd.Series:
    """產生確定性的模擬歷史價格 Series（與 get_historical_prices 回傳格式一致）."""
    n = 500
    rng = np.random.default_rng(hash(symbol) % 2**32)
    prices = 100.0 * np.cumprod(1 + rng.normal(0.0005, 0.01, n))
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.Series(prices, index=idx, name="Close")


@allure.epic("回測系統")
@allure.feature("回測 API")
@pytest.mark.e2e
class TestRunBacktest:
    """POST /api/backtest/run 端點測試."""

    @allure.story("成功回測（雙資產）")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_run_backtest_returns_200(self, client, auth_headers):
        """有效的雙資產回測請求應回傳 200 及指標."""
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=_mock_backtest_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            resp = client.post(
                "/api/backtest/run",
                headers=auth_headers,
                json={
                    "items": [
                        {"symbol": "VTI", "name": "Vanguard", "weight": 70.0, "category": "us_etf"},
                        {"symbol": "BND", "name": "Bond", "weight": 30.0, "category": "us_etf"},
                    ],
                    "start_date": "2022-01-01",
                    "end_date": "2023-12-31",
                    "initial_amount": 100000,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data

    @allure.story("回測指標完整性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_backtest_response_contains_key_metrics(self, client, auth_headers):
        """回測結果應包含必要的金融指標欄位."""
        with patch(
            "app.services.backtest_engine.get_historical_prices",
            side_effect=_mock_backtest_prices,
        ), patch(
            "app.services.backtest_engine.get_symbol_currency",
            return_value="USD",
        ):
            resp = client.post(
                "/api/backtest/run",
                headers=auth_headers,
                json={
                    "items": [{"symbol": "SPY", "name": "S&P500", "weight": 100.0, "category": "us_etf"}],
                    "start_date": "2022-01-01",
                    "end_date": "2023-06-30",
                },
            )
        assert resp.status_code == 200
        metrics = resp.json().get("metrics", {})
        for key in ("cagr", "sharpe_ratio", "max_drawdown", "total_return"):
            assert key in metrics, f"缺少指標欄位: {key}"

    @allure.story("無授權")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_run_backtest_no_auth_rejected(self, client):
        """未帶 Authorization 應被拒絕."""
        resp = client.post(
            "/api/backtest/run",
            json={
                "items": [{"symbol": "VTI", "name": "V", "weight": 100.0, "category": "us_etf"}],
                "start_date": "2022-01-01",
                "end_date": "2023-01-01",
            },
        )
        assert resp.status_code in (401, 403, 422)

    @allure.story("空資產清單")
    def test_backtest_empty_items_returns_400(self, client, auth_headers):
        """空資產清單應回傳 400."""
        resp = client.post(
            "/api/backtest/run",
            headers=auth_headers,
            json={"items": [], "start_date": "2022-01-01", "end_date": "2023-01-01"},
        )
        assert resp.status_code == 400

    @allure.story("權重總和錯誤")
    def test_backtest_wrong_weight_sum_returns_400(self, client, auth_headers):
        """權重總和不等於 100% 應回傳 400."""
        resp = client.post(
            "/api/backtest/run",
            headers=auth_headers,
            json={
                "items": [
                    {"symbol": "VTI", "name": "V", "weight": 60.0, "category": "us_etf"},
                    {"symbol": "BND", "name": "B", "weight": 20.0, "category": "us_etf"},
                ],
                "start_date": "2022-01-01",
                "end_date": "2023-01-01",
            },
        )
        assert resp.status_code == 400

    @allure.story("超過最大資產數")
    def test_backtest_too_many_items_returns_400(self, client, auth_headers):
        """超過 10 個資產應回傳 400."""
        items = [
            {"symbol": f"STOCK{i}", "name": f"Stock {i}", "weight": 9.0, "category": "us_etf"}
            for i in range(12)
        ]
        resp = client.post(
            "/api/backtest/run",
            headers=auth_headers,
            json={"items": items, "start_date": "2022-01-01", "end_date": "2023-01-01"},
        )
        assert resp.status_code == 400


@allure.epic("回測系統")
@allure.feature("回測投資組合管理")
@pytest.mark.e2e
class TestBacktestPortfolios:
    """GET /api/backtest — 列出儲存的投資組合."""

    @allure.story("列出投資組合")
    def test_list_portfolios_returns_200(self, client, auth_headers):
        """合法授權取得投資組合清單應回傳 200."""
        mock_sb = make_supabase_mock(rows=[])
        with patch("app.routers.backtest.get_supabase", return_value=mock_sb):
            resp = client.get("/api/backtest", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
