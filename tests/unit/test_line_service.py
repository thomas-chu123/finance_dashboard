"""單元測試 — LINE 通知服務（build_alert_message 訊息內容）."""
import pytest
import allure

from app.services.line_service import (
    build_alert_message,
    _fmt_threshold,
    _build_rsi_condition_label,
)


# ── 共用參數 ─────────────────────────────────────────────────────────────────
_BASE = dict(
    symbol="0050.TW",
    name="元大台灣50",
    current_price=195.5,
    trigger_price=190.0,
    trigger_direction="above",
    tracking_id="track-tw-001",
)


@allure.epic("通知服務")
@allure.feature("LINE 警報訊息")
@pytest.mark.unit
class TestBuildAlertMessage:
    """build_alert_message 訊息建立測試."""

    @allure.story("基本內容")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_message_contains_symbol(self):
        """訊息應包含股票代碼."""
        msg = build_alert_message(**_BASE, trigger_mode="price")
        assert "0050.TW" in msg

    @allure.story("基本內容")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_message_contains_name(self):
        """訊息應包含資產名稱."""
        msg = build_alert_message(**_BASE, trigger_mode="price")
        assert "元大台灣50" in msg

    @allure.story("基本內容")
    def test_message_contains_current_price(self):
        """訊息應包含目前價格."""
        msg = build_alert_message(**_BASE, trigger_mode="price")
        assert "195.50" in msg

    @allure.story("通知停止連結")
    def test_message_contains_stop_link(self):
        """訊息應包含停止通知的連結（含 tracking_id）."""
        msg = build_alert_message(**_BASE, trigger_mode="price")
        assert "track-tw-001" in msg
        assert "stop-notification" in msg

    @allure.story("price 模式")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_price_mode_label(self):
        """price 模式訊息應顯示「價格觸發」."""
        msg = build_alert_message(**_BASE, trigger_mode="price")
        assert "價格" in msg

    @allure.story("rsi 模式 - 超賣")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsi_oversold_signal_in_message(self):
        """RSI 超賣時訊息應包含超賣信號."""
        msg = build_alert_message(
            **_BASE,
            trigger_mode="rsi",
            current_rsi=22.0,
            rsi_below=30.0,
        )
        assert "超賣" in msg

    @allure.story("rsi 模式 - 超買")
    def test_rsi_overbought_signal_in_message(self):
        """RSI 超買時訊息應包含超買信號."""
        msg = build_alert_message(
            **_BASE,
            trigger_mode="rsi",
            current_rsi=78.0,
            rsi_above=70.0,
        )
        assert "超買" in msg

    @allure.story("rsi 模式 - 正常範圍")
    def test_rsi_normal_range_signal(self):
        """RSI 在正常範圍內應顯示正常信號."""
        msg = build_alert_message(
            **_BASE,
            trigger_mode="either",
            current_rsi=50.0,
            rsi_below=30.0,
            rsi_above=70.0,
            price_condition_met=True,
            rsi_condition_met=False,
        )
        # RSI 顯示時不應有超賣/超買
        assert "正常範圍" in msg or "50.00" in msg

    @allure.story("both 模式")
    def test_both_mode_label(self):
        """both 模式訊息應提及「價格及 RSI」."""
        msg = build_alert_message(
            **_BASE,
            trigger_mode="both",
            current_rsi=25.0,
            rsi_below=30.0,
            price_condition_met=True,
            rsi_condition_met=True,
        )
        assert "價格及 RSI" in msg or ("價格" in msg and "RSI" in msg)

    @allure.story("either 模式 - 僅 RSI 觸發")
    def test_either_mode_rsi_only(self):
        """either 模式只有 RSI 觸發時，訊息應顯示 RSI 觸發."""
        msg = build_alert_message(
            **_BASE,
            trigger_mode="either",
            current_rsi=25.0,
            rsi_below=30.0,
            price_condition_met=False,
            rsi_condition_met=True,
        )
        assert "RSI" in msg

    @allure.story("Return 型別")
    def test_returns_string(self):
        """build_alert_message 應回傳字串."""
        result = build_alert_message(**_BASE, trigger_mode="price")
        assert isinstance(result, str)

    @allure.story("無 RSI 數據")
    def test_no_rsi_data_no_rsi_line(self):
        """未提供 current_rsi 時訊息不應包含 RSI 行."""
        msg = build_alert_message(**_BASE, trigger_mode="price", current_rsi=None)
        assert "RSI (14)" not in msg


@allure.epic("通知服務")
@allure.feature("LINE 輔助函數")
@pytest.mark.unit
class TestLineServiceHelpers:
    """LINE 服務輔助函數測試."""

    @allure.story("_fmt_threshold 整數格式")
    @pytest.mark.parametrize("value,expected", [
        (30.0, "30"),
        (70.0, "70"),
        (30.5, "30.5"),
        (0.1, "0.1"),
    ])
    def test_fmt_threshold_formatting(self, value, expected):
        """_fmt_threshold 應以最小必要小數位格式化數字."""
        assert _fmt_threshold(value) == expected

    @allure.story("_build_rsi_condition_label 超賣")
    def test_rsi_condition_label_oversold(self):
        """低於下限時應顯示「跌破」描述."""
        label = _build_rsi_condition_label(current_rsi=20.0, rsi_below=30.0, rsi_above=None)
        assert "跌破" in label or "30" in label

    @allure.story("_build_rsi_condition_label 超買")
    def test_rsi_condition_label_overbought(self):
        """高於上限時應顯示「突破」描述."""
        label = _build_rsi_condition_label(current_rsi=80.0, rsi_below=None, rsi_above=70.0)
        assert "突破" in label or "70" in label

    @allure.story("_build_rsi_condition_label 雙向")
    def test_rsi_condition_label_both_thresholds_no_current(self):
        """未提供 current_rsi 時雙向閾值應顯示完整描述."""
        label = _build_rsi_condition_label(current_rsi=None, rsi_below=30.0, rsi_above=70.0)
        assert "30" in label and "70" in label
