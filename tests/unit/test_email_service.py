"""單元測試 — Email 通知服務（build_alert_email 訊息內容）."""
import pytest
import allure

from app.services.email_service import build_alert_email


# ── 共用參數 ─────────────────────────────────────────────────────────────────
_BASE = dict(
    symbol="VTI",
    name="Vanguard Total Stock",
    category="us_etf",
    current_price=255.0,
    trigger_price=250.0,
    trigger_direction="above",
    tracking_id="track-001",
)


@allure.epic("通知服務")
@allure.feature("Email 警報內容")
@pytest.mark.unit
class TestBuildAlertEmail:
    """build_alert_email 訊息建立測試."""

    @allure.story("price 模式")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_price_mode_subject_contains_symbol(self):
        """price 模式 Email 標題應包含股票代碼."""
        subject, body = build_alert_email(**_BASE, trigger_mode="price")
        assert "VTI" in subject

    @allure.story("price 模式")
    def test_price_mode_subject_contains_price(self):
        """price 模式 Email 標題應包含觸發價格."""
        subject, body = build_alert_email(**_BASE, trigger_mode="price")
        assert "250" in subject or "250.00" in subject

    @allure.story("price 模式 - below")
    def test_price_below_subject_contains_break_below(self):
        """跌破方向的標題應包含「跌破」."""
        subject, body = build_alert_email(
            **{**_BASE, "trigger_direction": "below"}, trigger_mode="price"
        )
        assert "跌破" in subject

    @allure.story("price 模式 - above")
    def test_price_above_subject_contains_break_above(self):
        """突破方向的標題應包含「突破」."""
        subject, body = build_alert_email(**_BASE, trigger_mode="price")
        assert "突破" in subject

    @allure.story("rsi 模式")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsi_mode_subject_describes_rsi(self):
        """rsi 模式標題應描述 RSI 觸發條件."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="rsi",
            current_rsi=25.0,
            rsi_below=30.0,
        )
        assert "RSI" in subject or "rsi" in subject.lower()

    @allure.story("rsi 模式")
    def test_rsi_body_contains_rsi_value(self):
        """Email 正文應包含 RSI 當前數值."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="rsi",
            current_rsi=25.0,
            rsi_below=30.0,
        )
        assert "25.00" in body or "25" in body

    @allure.story("both 模式（AND）")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_both_mode_subject_mentions_both(self):
        """both 模式標題應提及價格及 RSI 均已觸發."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="both",
            current_rsi=25.0,
            rsi_below=30.0,
            price_condition_met=True,
            rsi_condition_met=True,
        )
        assert "RSI" in subject or "及" in subject

    @allure.story("either 模式（OR）- 僅價格觸發")
    def test_either_mode_price_only_triggered(self):
        """either 模式只有價格觸發時，標題應偏向價格描述."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="either",
            current_rsi=50.0,
            rsi_below=30.0,
            price_condition_met=True,
            rsi_condition_met=False,
        )
        assert "250" in subject or "突破" in subject

    @allure.story("either 模式（OR）- 僅 RSI 觸發")
    def test_either_mode_rsi_only_triggered(self):
        """either 模式只有 RSI 觸發時，標題應偏向 RSI 描述."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="either",
            current_rsi=25.0,
            rsi_below=30.0,
            price_condition_met=False,
            rsi_condition_met=True,
        )
        assert "RSI" in subject

    @allure.story("Body HTML 結構")
    def test_body_is_html_string(self):
        """Email 正文應為 HTML 字串（含基本 HTML 標籤）."""
        subject, body = build_alert_email(**_BASE, trigger_mode="price")
        assert isinstance(body, str)
        assert "<" in body and ">" in body

    @allure.story("Return 型別")
    def test_returns_tuple_of_two_strings(self):
        """build_alert_email 應回傳 (str, str) 元組."""
        result = build_alert_email(**_BASE, trigger_mode="price")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, str) for v in result)

    @allure.story("超賣信號顏色")
    def test_rsi_oversold_uses_red_accent(self):
        """超賣信號（rsi < rsi_below）的 Email 應帶紅色強調色。"""
        subject, body = build_alert_email(
            **{**_BASE, "trigger_direction": "below"},
            trigger_mode="rsi",
            current_rsi=20.0,
            rsi_below=30.0,
            price_condition_met=False,
            rsi_condition_met=True,
        )
        assert "#ef4444" in body  # 紅色

    @allure.story("超買信號顏色")
    def test_rsi_overbought_uses_green_accent(self):
        """超買信號（rsi > rsi_above）的 Email 應帶綠色強調色."""
        subject, body = build_alert_email(
            **_BASE,
            trigger_mode="rsi",
            current_rsi=80.0,
            rsi_above=70.0,
            price_condition_met=False,
            rsi_condition_met=True,
        )
        assert "#22c55e" in body  # 綠色
