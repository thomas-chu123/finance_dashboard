"""E2E 測試 — 市場數據端點."""
import asyncio
import pytest
import allure
from unittest.mock import patch, AsyncMock


def _mock_fetch_quote(meta: dict) -> dict:
    """返回一個假的行情 dict，格式與 _fetch_quote 相同."""
    return {
        "symbol": meta["symbol"],
        "name": meta.get("name", meta["symbol"]),
        "category": "us_etf",
        "price": 250.0,
        "change": 1.5,
        "prev_close": 248.5,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "error": None,
    }


@allure.epic("市場數據")
@allure.feature("行情 API")
@pytest.mark.e2e
class TestMarketQuotes:
    """GET & POST /api/market/quotes — 市場行情查詢."""

    @allure.story("預設行情清單")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_default_quotes_returns_200(self, client):
        """不帶 symbols 參數應回傳預設清單 200."""
        with patch(
            "app.routers.market._fetch_quote",
            side_effect=_mock_fetch_quote,
        ):
            resp = client.get("/api/market/quotes")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @allure.story("單一股票行情")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_single_quote_returns_list(self, client):
        """帶 symbols=VTI 應回傳含一個元素的 list."""
        with patch(
            "app.routers.market._fetch_quote",
            side_effect=_mock_fetch_quote,
        ):
            resp = client.get("/api/market/quotes?symbols=VTI")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["symbol"] == "VTI"

    @allure.story("多支股票行情")
    def test_get_multiple_quotes(self, client):
        """帶 symbols=VTI,BND 應回傳含兩個元素的 list."""
        with patch(
            "app.routers.market._fetch_quote",
            side_effect=_mock_fetch_quote,
        ):
            resp = client.get("/api/market/quotes?symbols=VTI,BND")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        symbols = [d["symbol"] for d in data]
        assert "VTI" in symbols
        assert "BND" in symbols

    @allure.story("POST 批次行情")
    def test_post_quotes_batch(self, client):
        """POST /api/market/quotes 批次查詢應回傳清單."""
        with patch(
            "app.routers.market._fetch_quote",
            side_effect=_mock_fetch_quote,
        ):
            resp = client.post(
                "/api/market/quotes",
                json=[
                    {"symbol": "VTI", "name": "Vanguard Total Stock"},
                    {"symbol": "BND", "name": "Vanguard Bond"},
                ],
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2


@allure.epic("市場數據")
@allure.feature("股票代碼查詢")
@pytest.mark.e2e
class TestMarketSymbols:
    """GET /api/market/symbols & /api/market/symbol-catalog."""

    @allure.story("可用代碼清單")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_symbols_returns_200(self, client):
        """GET /api/market/symbols 應回傳 200 及分類結構."""
        tw_mock = [{"symbol": "0050.TW", "name": "元大台灣50"}]
        us_mock = [{"symbol": "VTI", "name": "Vanguard Total Stock"}]
        idx_mock = [{"symbol": "^GSPC", "name": "S&P 500"}]

        async def _tw():
            return tw_mock

        async def _us():
            return us_mock

        with (
            patch("app.routers.market.fetch_tw_etf_list", new=_tw),
            patch("app.routers.market.fetch_us_etf_list", new=_us),
            patch("app.routers.market.get_index_list", return_value=idx_mock),
        ):
            resp = client.get("/api/market/symbols")
        assert resp.status_code == 200
        data = resp.json()
        assert "tw_etf" in data
        assert "us_etf" in data
        assert "index" in data

    @allure.story("Symbol Catalog")
    def test_symbol_catalog_returns_dict(self, client):
        """GET /api/market/symbol-catalog 應回傳 200 及 dict."""
        resp = client.get("/api/market/symbol-catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert len(data) > 0
