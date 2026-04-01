"""單元測試 — SearXNG 新聞搜尋服務."""
import pytest
import allure
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.searxng_service import search_news


def _mock_settings(base_url: str = "https://search.skynetapp.org"):
    """建立 mock Settings 物件."""
    s = MagicMock()
    s.searxng_base_url = base_url
    return s


def _searxng_response(results: list[dict]) -> MagicMock:
    """建立 mock httpx Response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"results": results}
    return resp


_SAMPLE_RESULTS = [
    {
        "title": "VTI ETF 今日上漲 1.2%",
        "url": "https://example.com/news/1",
        "content": "先鋒整體市場ETF 受科技股帶動走強",
        "publishedDate": "2026-03-31T08:00:00",
    },
    {
        "title": "美股三大指數收高",
        "url": "https://example.com/news/2",
        "content": "標普500指數攀升至歷史新高",
        "publishedDate": "2026-03-31T07:30:00",
    },
    {
        "title": "聯準會維持利率不變",
        "url": "https://example.com/news/3",
        "content": "Fed 決策符合市場預期，股市正面回應",
        "publishedDate": "2026-03-30T23:00:00",
    },
]


@allure.epic("AI 每日早報")
@allure.feature("SearXNG 搜尋服務")
@pytest.mark.unit
class TestSearchNews:
    """search_news 函式單元測試."""

    @allure.story("正常流程")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.asyncio
    async def test_returns_correct_format(self):
        """正常回應時應回傳含 title/url/description/published_date 欄位的 list."""
        mock_resp = _searxng_response(_SAMPLE_RESULTS)

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock", count=3)

        assert isinstance(result, list)
        assert len(result) == 3
        for item in result:
            assert "title" in item
            assert "url" in item
            assert "description" in item
            assert "published_date" in item

    @allure.story("正常流程")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.asyncio
    async def test_content_field_mapped_to_description(self):
        """SearXNG 的 content 欄位應正確對應到輸出的 description 欄位."""
        mock_resp = _searxng_response(_SAMPLE_RESULTS[:1])

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock", count=1)

        assert result[0]["description"] == "先鋒整體市場ETF 受科技股帶動走強"

    @allure.story("count 限制")
    @pytest.mark.asyncio
    async def test_respects_count_limit(self):
        """結果數量不應超過 count 參數."""
        mock_resp = _searxng_response(_SAMPLE_RESULTS)

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock", count=2)

        assert len(result) == 2

    @allure.story("錯誤處理")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio
    async def test_http_error_returns_empty_list(self):
        """HTTP 500 時應回傳空 list，不拋出例外."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock")

        assert result == []

    @allure.story("錯誤處理")
    @pytest.mark.asyncio
    async def test_no_base_url_returns_empty_list(self):
        """searxng_base_url 未設定時應回傳空 list."""
        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings(base_url="")):
            result = await search_news("VTI ETF stock")

        assert result == []

    @allure.story("錯誤處理")
    @pytest.mark.asyncio
    async def test_timeout_returns_empty_list(self):
        """網路 timeout 時應回傳空 list，不拋出例外."""
        import httpx as httpx_module

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(side_effect=httpx_module.TimeoutException("timeout"))
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock")

        assert result == []

    @allure.story("空結果")
    @pytest.mark.asyncio
    async def test_empty_results_returns_empty_list(self):
        """SearXNG 回傳空 results 陣列時應回傳空 list."""
        mock_resp = _searxng_response([])

        with patch("app.services.searxng_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await search_news("VTI ETF stock")

        assert result == []
