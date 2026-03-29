"""單元測試 — 排程器複合警報觸發條件（純函數）."""
import pytest
import allure

from app.scheduler import (
    _check_price_condition,
    _check_rsi_condition,
    _evaluate_trigger_conditions,
)


@allure.epic("警報系統")
@allure.feature("價格條件判斷")
@pytest.mark.unit
class TestCheckPriceCondition:
    """_check_price_condition 純函數測試."""

    @allure.story("above 方向")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("current,trigger,expected", [
        (150.0, 100.0, True),   # 超過觸發點
        (100.0, 100.0, True),   # 等於觸發點（包含等號）
        (99.99, 100.0, False),  # 低於觸發點
    ])
    def test_price_above_direction(self, current, trigger, expected):
        """above 模式：current >= trigger 才觸發."""
        assert _check_price_condition(current, trigger, "above") is expected

    @allure.story("below 方向")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("current,trigger,expected", [
        (50.0, 100.0, True),    # 低於觸發點
        (100.0, 100.0, True),   # 等於觸發點（包含等號）
        (100.01, 100.0, False), # 超過觸發點
    ])
    def test_price_below_direction(self, current, trigger, expected):
        """below 模式：current <= trigger 才觸發."""
        assert _check_price_condition(current, trigger, "below") is expected

    @allure.story("無效方向")
    def test_invalid_direction_returns_false(self):
        """無效方向字串應安全回傳 False."""
        assert _check_price_condition(100.0, 100.0, "invalid") is False

    @allure.story("無效方向")
    def test_unknown_direction_returns_false(self):
        """空字串方向應回傳 False."""
        assert _check_price_condition(100.0, 100.0, "") is False


@allure.epic("警報系統")
@allure.feature("RSI 條件判斷")
@pytest.mark.unit
class TestCheckRSICondition:
    """_check_rsi_condition 純函數測試."""

    @allure.story("超賣條件")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("rsi,rsi_below,expected", [
        (25.0, 30.0, True),   # 嚴格小於下限 → 觸發
        (30.0, 30.0, False),  # 等於下限 → 不觸發（嚴格）
        (35.0, 30.0, False),  # 超過下限 → 不觸發
        (None, 30.0, False),  # RSI 為 None → 不觸發
    ])
    def test_oversold_condition(self, rsi, rsi_below, expected):
        """超賣條件（rsi < rsi_below）邊界測試."""
        assert _check_rsi_condition(rsi, rsi_below=rsi_below, rsi_above=None) is expected

    @allure.story("超買條件")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("rsi,rsi_above,expected", [
        (75.0, 70.0, True),   # 嚴格大於上限 → 觸發
        (70.0, 70.0, False),  # 等於上限 → 不觸發（嚴格）
        (65.0, 70.0, False),  # 低於上限 → 不觸發
        (None, 70.0, False),  # RSI 為 None → 不觸發
    ])
    def test_overbought_condition(self, rsi, rsi_above, expected):
        """超買條件（rsi > rsi_above）邊界測試."""
        assert _check_rsi_condition(rsi, rsi_below=None, rsi_above=rsi_above) is expected

    @allure.story("雙向閾值")
    def test_both_thresholds_set(self):
        """同時設定上下限，任一觸發即算觸發."""
        assert _check_rsi_condition(25.0, rsi_below=30.0, rsi_above=70.0) is True   # 超賣
        assert _check_rsi_condition(75.0, rsi_below=30.0, rsi_above=70.0) is True   # 超買
        assert _check_rsi_condition(50.0, rsi_below=30.0, rsi_above=70.0) is False  # 正常

    @allure.story("無閾值")
    def test_no_thresholds_returns_false(self):
        """未設任何 RSI 閾值時應回傳 False."""
        assert _check_rsi_condition(50.0, rsi_below=None, rsi_above=None) is False


@allure.epic("警報系統")
@allure.feature("複合觸發邏輯")
@pytest.mark.unit
class TestEvaluateTriggerConditions:
    """_evaluate_trigger_conditions 複合觸發邏輯測試."""

    @allure.story("price 模式")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("price_met,rsi_met,expected", [
        (True, False, True),   # 只需價格觸發
        (False, True, False),  # RSI 觸發但 price 模式不算
        (True, True, True),
        (False, False, False),
    ])
    def test_price_only_mode(self, price_met, rsi_met, expected):
        """price 模式：只看價格條件."""
        assert _evaluate_trigger_conditions(price_met, rsi_met, "price") is expected

    @allure.story("rsi 模式")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("price_met,rsi_met,expected", [
        (False, True, True),   # 只需 RSI 觸發
        (True, False, False),  # 價格觸發但 rsi 模式不算
        (True, True, True),
        (False, False, False),
    ])
    def test_rsi_only_mode(self, price_met, rsi_met, expected):
        """rsi 模式：只看 RSI 條件."""
        assert _evaluate_trigger_conditions(price_met, rsi_met, "rsi") is expected

    @allure.story("both 模式（AND）")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("price_met,rsi_met,expected", [
        (True, True, True),    # 兩者皆觸發 → 觸發
        (True, False, False),  # 只有價格 → 不觸發
        (False, True, False),  # 只有 RSI → 不觸發
        (False, False, False),
    ])
    def test_both_mode_and_logic(self, price_met, rsi_met, expected):
        """both 模式：AND 邏輯，兩者同時滿足才觸發."""
        assert _evaluate_trigger_conditions(price_met, rsi_met, "both") is expected

    @allure.story("either 模式（OR）")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("price_met,rsi_met,expected", [
        (True, False, True),   # 只有價格 → 觸發
        (False, True, True),   # 只有 RSI → 觸發
        (True, True, True),    # 兩者皆觸發 → 觸發
        (False, False, False),
    ])
    def test_either_mode_or_logic(self, price_met, rsi_met, expected):
        """either 模式：OR 邏輯，任一滿足即觸發."""
        assert _evaluate_trigger_conditions(price_met, rsi_met, "either") is expected
