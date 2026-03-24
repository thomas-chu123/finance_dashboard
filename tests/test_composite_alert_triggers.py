"""Phase 2 端到端警報觸發測試 - 複合條件警報檢測."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.scheduler import (
    _check_price_condition,
    _check_rsi_condition,
    _evaluate_trigger_conditions,
)


class TestPriceCondition:
    """價格條件檢查測試."""
    
    def test_price_above_trigger(self):
        """測試價格超過觸發點（above 模式）."""
        assert _check_price_condition(150.0, 100.0, "above") is True
        assert _check_price_condition(100.0, 100.0, "above") is True
        assert _check_price_condition(99.99, 100.0, "above") is False
    
    def test_price_below_trigger(self):
        """測試價格低於觸發點（below 模式）."""
        assert _check_price_condition(50.0, 100.0, "below") is True
        assert _check_price_condition(100.0, 100.0, "below") is True
        assert _check_price_condition(100.01, 100.0, "below") is False
    
    def test_price_invalid_direction(self):
        """測試無效的觸發方向."""
        assert _check_price_condition(100.0, 100.0, "invalid") is False


class TestRSICondition:
    """RSI 條件檢查測試."""
    
    def test_rsi_oversold_trigger(self):
        """測試 RSI 超賣信號（低於 30）."""
        assert _check_rsi_condition(25.0, rsi_below=30.0, rsi_above=None) is True
        assert _check_rsi_condition(30.0, rsi_below=30.0, rsi_above=None) is False
        assert _check_rsi_condition(None, rsi_below=30.0, rsi_above=None) is False
    
    def test_rsi_overbought_trigger(self):
        """測試 RSI 超買信號（高於 70）."""
        assert _check_rsi_condition(75.0, rsi_below=None, rsi_above=70.0) is True
        assert _check_rsi_condition(70.0, rsi_below=None, rsi_above=70.0) is False
        assert _check_rsi_condition(None, rsi_below=None, rsi_above=70.0) is False
    
    def test_rsi_both_conditions(self):
        """測試 RSI 同時設定上下限."""
        # RSI 在中間，都不觸發
        assert _check_rsi_condition(50.0, rsi_below=30.0, rsi_above=70.0) is False
        # RSI 低於下限觸發
        assert _check_rsi_condition(25.0, rsi_below=30.0, rsi_above=70.0) is True
        # RSI 高於上限觸發
        assert _check_rsi_condition(75.0, rsi_below=30.0, rsi_above=70.0) is True
    
    def test_rsi_none_thresholds(self):
        """測試沒有設定閾值的情況."""
        assert _check_rsi_condition(50.0, rsi_below=None, rsi_above=None) is False


class TestCompositeConditions:
    """複合觸發條件測試."""
    
    def test_price_only_mode(self):
        """測試僅限價格觸發模式."""
        # 價格觸發，RSI 不觸發
        assert _evaluate_trigger_conditions(True, False, "price") is True
        # 價格不觸發，RSI 觸發 -> 不應觸發
        assert _evaluate_trigger_conditions(False, True, "price") is False
        # 兩者都觸發 -> 也只檢查價格
        assert _evaluate_trigger_conditions(True, True, "price") is True
    
    def test_rsi_only_mode(self):
        """測試僅限 RSI 觸發模式."""
        # 價格觸發，RSI 不觸發 -> 不應觸發
        assert _evaluate_trigger_conditions(True, False, "rsi") is False
        # 價格不觸發，RSI 觸發 -> 應觸發
        assert _evaluate_trigger_conditions(False, True, "rsi") is True
        # 兩者都觸發 -> 檢查 RSI
        assert _evaluate_trigger_conditions(True, True, "rsi") is True
    
    def test_both_mode(self):
        """測試價格 AND RSI 同時觸發模式."""
        # 都要滿足才能觸發
        assert _evaluate_trigger_conditions(True, True, "both") is True
        assert _evaluate_trigger_conditions(True, False, "both") is False
        assert _evaluate_trigger_conditions(False, True, "both") is False
        assert _evaluate_trigger_conditions(False, False, "both") is False
    
    def test_invalid_trigger_mode(self):
        """測試無效的觸發模式（預設為 price）."""
        assert _evaluate_trigger_conditions(True, False, "invalid") is True
        assert _evaluate_trigger_conditions(False, True, "invalid") is False


class TestCompositeScenarios:
    """複合觸發場景測試."""
    
    def test_scenario_price_only_vti_above_200(self):
        """場景：VTI 價格在 200 以上觸發."""
        current_price = 205.0
        trigger_price = 200.0
        current_rsi = 65.0  # 不觸發 RSI
        
        price_met = _check_price_condition(current_price, trigger_price, "above")
        rsi_met = _check_rsi_condition(current_rsi, rsi_below=30, rsi_above=70)
        
        # 價格模式：價格觸發，RSI 不觸發
        assert _evaluate_trigger_conditions(price_met, rsi_met, "price") is True
    
    def test_scenario_rsi_only_spy_oversold(self):
        """場景：SPY RSI 低於 30 時超賣."""
        current_price = 450.0  # 價格不觸發
        trigger_price = 400.0  # 設定 below
        current_rsi = 25.0  # 超賣
        
        price_met = _check_price_condition(current_price, trigger_price, "below")
        rsi_met = _check_rsi_condition(current_rsi, rsi_below=30, rsi_above=None)
        
        # RSI 模式：價格不觸發，但 RSI 觸發
        assert _evaluate_trigger_conditions(price_met, rsi_met, "rsi") is True
    
    def test_scenario_both_conditions_0050_strong_signal(self):
        """場景：元大台灣 50 同時滿足價格和 RSI 條件."""
        current_price = 85.0  # 高於 80
        trigger_price = 80.0
        current_rsi = 72.0  # 高於 70
        
        price_met = _check_price_condition(current_price, trigger_price, "above")
        rsi_met = _check_rsi_condition(current_rsi, rsi_below=None, rsi_above=70)
        
        # Both 模式：兩個條件都滿足
        assert _evaluate_trigger_conditions(price_met, rsi_met, "both") is True
    
    def test_scenario_both_conditions_partial_signal(self):
        """場景：元大高股息只滿足價格但 RSI 還未確認."""
        current_price = 29.0  # 低於 25
        trigger_price = 25.0
        current_rsi = 40.0  # 中立，未觸發
        
        price_met = _check_price_condition(current_price, trigger_price, "below")
        rsi_met = _check_rsi_condition(current_rsi, rsi_below=30, rsi_above=70)
        
        # Both 模式：價格觸發但 RSI 未觸發，整體不觸發
        assert _evaluate_trigger_conditions(price_met, rsi_met, "both") is False


class TestEdgeCases:
    """邊界情況測試."""
    
    def test_price_exact_trigger_point(self):
        """測試價格恰好在觸發點."""
        assert _check_price_condition(100.0, 100.0, "above") is True
        assert _check_price_condition(100.0, 100.0, "below") is True
    
    def test_rsi_extreme_values(self):
        """測試 RSI 極端值."""
        assert _check_rsi_condition(0.0, rsi_below=30.0, rsi_above=None) is True
        assert _check_rsi_condition(100.0, rsi_below=None, rsi_above=70.0) is True
        assert _check_rsi_condition(50.0, rsi_below=None, rsi_above=None) is False
    
    def test_multiple_updates_simulation(self):
        """模擬多次價格和 RSI 更新."""
        scenarios = [
            # (price, trigger_price, direction, rsi, rsi_below, rsi_above, mode, expected)
            (100.0, 100.0, "above", 40.0, 30.0, 70.0, "price", True),
            (99.9, 100.0, "below", 25.0, 30.0, 70.0, "rsi", True),
            (105.0, 100.0, "above", 75.0, 30.0, 70.0, "both", True),
            (105.0, 100.0, "above", 55.0, 30.0, 70.0, "both", False),
        ]
        
        for price, tprice, direction, rsi, rsi_b, rsi_a, mode, expected in scenarios:
            price_met = _check_price_condition(price, tprice, direction)
            rsi_met = _check_rsi_condition(rsi, rsi_b, rsi_a)
            result = _evaluate_trigger_conditions(price_met, rsi_met, mode)
            assert result == expected, f"Failed for scenario: {locals()}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
