"""單元測試 — Ollama Direct API 摘要服務."""
import pytest
import allure
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ollama_service import generate_market_summary


def _mock_settings(base_url: str = "http://192.168.0.26:11434", model: str = "gpt-oss:20b"):
    """建立 mock Settings 物件."""
    s = MagicMock()
    s.ollama_base_url = base_url
    s.ollama_model = model
    return s


def _ollama_response(content: str = "美股市場今日開盤前整體走勢強勁，VTI ETF 隨大盤上漲。") -> MagicMock:
    """建立 mock httpx Response（舊版 chat/completions 相容格式）."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "choices": [
            {"message": {"content": content}}
        ]
    }
    return resp


_SAMPLE_NEWS = [
    {
        "title": "VTI ETF 今日上漲 1.2%",
        "url": "https://example.com/1",
        "description": "先鋒整體市場ETF 受科技股帶動走強",
        "published_date": "2026-03-31T08:00:00",
    },
    {
        "title": "聯準會維持利率不變",
        "url": "https://example.com/2",
        "description": "Fed 決策符合市場預期，股市正面回應",
        "published_date": "2026-03-31T07:00:00",
    },
]


@allure.epic("AI 每日早報")
@allure.feature("Ollama Direct API 摘要服務")
@pytest.mark.unit
class TestGenerateMarketSummary:
    """generate_market_summary 函式單元測試."""

    @allure.story("正常流程")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self):
        """正常情況下應回傳非空字串."""
        mock_resp = _ollama_response("美股市場今日開盤前整體走勢強勁，VTI ETF 受科技股帶動上漲 1.2%。")

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert isinstance(result, str)
        assert len(result) > 0

    @allure.story("正常流程")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.asyncio
    async def test_returns_summary_content(self):
        """回傳內容應為 choices[0].message.content 的值."""
        expected = "美股市場今日表現亮眼，投資者應關注聯準會後續動向。"
        mock_resp = _ollama_response(expected)

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert result == expected

    @allure.story("無新聞輸入")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio
    async def test_empty_news_returns_empty_string(self):
        """news_items 為空 list 時應回傳 ""，不呼叫 Ollama API."""
        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await generate_market_summary("VTI", "先鋒整體市場ETF", [], 8)

        assert result == ""
        mock_client.post.assert_not_called()

    @allure.story("錯誤處理")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio
    async def test_no_base_url_returns_empty_string(self):
        """ollama_base_url 未設定時應回傳 ""."""
        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings(base_url="")):
            result = await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert result == ""

    @allure.story("錯誤處理")
    @pytest.mark.asyncio
    async def test_http_error_returns_empty_string(self):
        """HTTP 500 時應回傳 ""，不拋出例外."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert result == ""

    @allure.story("錯誤處理")
    @pytest.mark.asyncio
    async def test_timeout_returns_empty_string(self):
        """網路 timeout 時應回傳 ""，不拋出例外."""
        import httpx as httpx_module

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=httpx_module.TimeoutException("timeout"))
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert result == ""

    @allure.story("安全性 — 無認證 header")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.asyncio
    async def test_no_authorization_header_sent(self):
        """呼叫 Ollama Direct API 時不應傳送 Authorization header."""
        mock_resp = _ollama_response("測試摘要")
        captured_headers = {}

        async def capture_post(url, json=None, headers=None, **kwargs):
            captured_headers.update(headers or {})
            return mock_resp

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=capture_post)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, 8)

        assert "Authorization" not in captured_headers

    @allure.story("session_hour 標籤")
    @pytest.mark.asyncio
    async def test_session_hour_8_uses_morning_label(self):
        """session_hour=8 時 prompt 應包含「開盤前早報」."""
        captured_payload = {}

        async def capture_post(url, json=None, headers=None, **kwargs):
            captured_payload.update(json or {})
            return _ollama_response("摘要內容")

        with patch("app.services.ollama_service.get_settings", return_value=_mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=capture_post)
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                await generate_market_summary("VTI", "先鋒整體市場ETF", _SAMPLE_NEWS, session_hour=8)

        messages = captured_payload.get("messages", [])
        assert any("開盤前早報" in m.get("content", "") for m in messages)
