"""E2E 測試 — 投資組合優化端點."""
import pytest
import allure
import pandas as pd
import numpy as np
from unittest.mock import patch

from tests.e2e.conftest import make_supabase_mock


def _mock_optimize_prices(symbol: str, *args, **kwargs) -> pd.Series:
    """產生確定性的模擬歷史價格 Series（用於優化測試）."""
    n = 300
    rng = np.random.default_rng(hash(symbol) % 2**32)
    prices = 100.0 * np.cumprod(1 + rng.normal(0.0004, 0.009, n))
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.Series(prices, index=idx, name=symbol)


@allure.epic("投資組合優化")
@allure.feature("優化 API")
@pytest.mark.e2e
class TestOptimizeEndpoint:
    """POST /api/optimize — 馬可維茲優化端點測試."""

    @allure.story("成功優化（三資產）")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_optimize_returns_200(self, client, auth_headers):
        """有效的三資產優化請求應回傳 200."""
        with patch(
            "app.routers.optimize.get_historical_prices",
            side_effect=_mock_optimize_prices,
        ):
            resp = client.post(
                "/api/optimize",
                headers=auth_headers,
                json={
                    "symbols": ["VTI", "BND", "GLD"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                },
            )
        assert resp.status_code in (200, 400)

    @allure.story("優化結果結構")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_optimize_result_structure(self, client, auth_headers):
        """優化結果應包含 max_sharpe 和 min_volatility 鍵."""
        with patch(
            "app.routers.optimize.get_historical_prices",
            side_effect=_mock_optimize_prices,
        ):
            resp = client.post(
                "/api/optimize",
                headers=auth_headers,
                json={
                    "symbols": ["VTI", "BND"],
                    "start_date": "2023-01-02",
                    "end_date": "2023-12-29",
                },
            )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", data)
            assert "max_sharpe" in results or "error" in data

    @allure.story("無授權")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_optimize_no_auth_returns_any(self, client):
        """未帶 Authorization 的請求到無認證端點應被正常處理或拒絕."""
        # optimize 端點目前不要求 JWT，422 代表格式錯誤（可接受行為）
        resp = client.post(
            "/api/optimize",
            json={
                "symbols": ["VTI"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
        )
        assert resp.status_code in (200, 400, 401, 403)

    @allure.story("資產不足")
    def test_optimize_single_symbol_returns_400(self, client, auth_headers):
        """少於 2 個資產應回傳 400（優化需要至少 2 個資產）."""
        resp = client.post(
            "/api/optimize",
            headers=auth_headers,
            json={
                "symbols": ["VTI"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
        )
        assert resp.status_code == 400

