"""RSI 技術指標計算單元測試."""

import pytest
import math
from app.services.technical_indicators import (
    RSICalculator,
    TechnicalIndicators,
    validate_rsi_triggers
)


class TestRSICalculator:
    """RSI 計算器測試."""
    
    def test_rsi_calculation_basic(self):
        """測試基本 RSI 計算."""
        # 模擬 14 個收盤價，數據應該提供足夠的上升和下降
        prices = [
            44.34, 44.09, 44.15, 43.61, 44.33,
            44.83, 45.10, 45.42, 45.84, 46.08,
            45.89, 46.03, 45.61, 46.28, 46.00
        ]
        
        rsi = RSICalculator.calculate_rsi(prices)
        
        # 驗證 RSI 在有效範圍內
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_insufficient_data(self):
        """測試數據不足的情況."""
        prices = [1.0, 2.0]
        rsi = RSICalculator.calculate_rsi(prices, period=14)
        assert rsi is None
    
    def test_rsi_empty_list(self):
        """測試空列表."""
        rsi = RSICalculator.calculate_rsi([])
        assert rsi is None
    
    def test_rsi_single_price(self):
        """測試單一價格."""
        rsi = RSICalculator.calculate_rsi([100.0])
        assert rsi is None
    
    def test_rsi_with_nan(self):
        """測試包含 NaN 的數據."""
        prices = [1.0, 2.0, float('nan'), 4.0]
        rsi = RSICalculator.calculate_rsi(prices)
        assert rsi is None
    
    def test_rsi_constant_prices(self):
        """測試恆定價格（沒有變化）."""
        prices = [100.0] * 15
        rsi = RSICalculator.calculate_rsi(prices)
        # 恆定價格應該返回 50（中立）
        assert rsi == 50.0
    
    def test_rsi_all_rising_prices(self):
        """測試持續上升的價格."""
        prices = list(range(1, 20))  # [1, 2, 3, ..., 19]
        rsi = RSICalculator.calculate_rsi(prices, period=14)
        # 全部上升應該導致高 RSI
        assert rsi is not None
        assert rsi > 70  # 應該超買
    
    def test_rsi_all_falling_prices(self):
        """測試持續下降的價格."""
        prices = list(range(20, 0, -1))  # [20, 19, 18, ..., 1]
        rsi = RSICalculator.calculate_rsi(prices, period=14)
        # 全部下降應該導致低 RSI
        assert rsi is not None
        assert rsi < 30  # 應該超賣
    
    def test_rsi_custom_period(self):
        """測試自定義週期."""
        # 使用振盪的價格而不是單調遞增的價格來測試不同的週期效果
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108, 107, 109, 108, 110, 109, 111, 110, 112, 111, 113]
        rsi_14 = RSICalculator.calculate_rsi(prices, period=14)
        rsi_7 = RSICalculator.calculate_rsi(prices, period=7)
        
        assert rsi_14 is not None
        assert rsi_7 is not None
        # 驗證兩者都是有效的 RSI 值
        assert 0 <= rsi_14 <= 100
        assert 0 <= rsi_7 <= 100
    
    def test_rsi_series_calculation(self):
        """測試 RSI 序列計算."""
        prices = list(range(1, 25))
        rsi_series = RSICalculator.calculate_rsi_series(prices, period=14)
        
        # 驗證長度
        assert len(rsi_series) == len(prices)
        
        # 前 14 個應該是 None
        for i in range(14):
            assert rsi_series[i] is None
        
        # 後續值應該是浮點數或 None
        for i in range(14, len(rsi_series)):
            assert rsi_series[i] is None or isinstance(rsi_series[i], float)
    
    def test_is_oversold(self):
        """測試超賣信號."""
        # RSI < 30 應該是超賣
        assert RSICalculator.is_oversold(25.0) is True
        assert RSICalculator.is_oversold(30.0) is False
        assert RSICalculator.is_oversold(50.0) is False
        assert RSICalculator.is_oversold(None) is False
    
    def test_is_overbought(self):
        """測試超買信號."""
        # RSI > 70 應該是超買
        assert RSICalculator.is_overbought(75.0) is True
        assert RSICalculator.is_overbought(70.0) is False
        assert RSICalculator.is_overbought(50.0) is False
        assert RSICalculator.is_overbought(None) is False
    
    def test_is_oversold_custom_threshold(self):
        """測試自定義超賣閾值."""
        assert RSICalculator.is_oversold(35.0, threshold=35.0) is False
        assert RSICalculator.is_oversold(34.9, threshold=35.0) is True
    
    def test_is_overbought_custom_threshold(self):
        """測試自定義超買閾值."""
        assert RSICalculator.is_overbought(65.0, threshold=65.0) is False
        assert RSICalculator.is_overbought(65.1, threshold=65.0) is True


class TestTechnicalIndicators:
    """通用技術指標測試."""
    
    def test_calculate_moving_average_basic(self):
        """測試基本移動平均計算."""
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        ma = TechnicalIndicators.calculate_moving_average(prices, period=3)
        # (3 + 4 + 5) / 3 = 4.0
        assert ma == 4.0
    
    def test_calculate_moving_average_insufficient_data(self):
        """測試數據不足的移動平均."""
        prices = [1.0, 2.0]
        ma = TechnicalIndicators.calculate_moving_average(prices, period=5)
        assert ma is None
    
    def test_calculate_volatility_basic(self):
        """測試基本波動性計算."""
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        vol = TechnicalIndicators.calculate_volatility(prices, period=5)
        assert vol is not None
        assert vol > 0
    
    def test_calculate_volatility_constant_prices(self):
        """測試恆定價格的波動性."""
        prices = [5.0] * 10
        vol = TechnicalIndicators.calculate_volatility(prices, period=5)
        # 恆定價格應該有零波動
        assert vol == 0.0
    
    def test_calculate_volatility_insufficient_data(self):
        """測試數據不足的波動性."""
        prices = [1.0, 2.0]
        vol = TechnicalIndicators.calculate_volatility(prices, period=5)
        assert vol is None


class TestValidateRSITriggers:
    """RSI 觸發條件驗證測試."""
    
    def test_validate_rsi_below_trigger(self):
        """測試 RSI 低於閾值觸發."""
        assert validate_rsi_triggers(25.0, rsi_below=30.0, rsi_above=None) is True
        assert validate_rsi_triggers(35.0, rsi_below=30.0, rsi_above=None) is False
    
    def test_validate_rsi_above_trigger(self):
        """測試 RSI 高於閾值觸發."""
        assert validate_rsi_triggers(75.0, rsi_below=None, rsi_above=70.0) is True
        assert validate_rsi_triggers(65.0, rsi_below=None, rsi_above=70.0) is False
    
    def test_validate_rsi_both_conditions(self):
        """測試兩個 RSI 條件."""
        # RSI 既低於下限又高於上限應該觸發任一條件
        assert validate_rsi_triggers(25.0, rsi_below=30.0, rsi_above=70.0) is True
        assert validate_rsi_triggers(75.0, rsi_below=30.0, rsi_above=70.0) is True
        assert validate_rsi_triggers(50.0, rsi_below=30.0, rsi_above=70.0) is False
    
    def test_validate_rsi_none_value(self):
        """測試 None RSI 值."""
        assert validate_rsi_triggers(None, rsi_below=30.0, rsi_above=None) is False
    
    def test_validate_rsi_no_conditions(self):
        """測試沒有觸發條件."""
        assert validate_rsi_triggers(50.0, rsi_below=None, rsi_above=None) is False
    
    def test_validate_rsi_boundary_values(self):
        """測試邊界值."""
        # 若 RSI 等於閾值，不應觸發
        assert validate_rsi_triggers(30.0, rsi_below=30.0, rsi_above=None) is False
        assert validate_rsi_triggers(70.0, rsi_below=None, rsi_above=70.0) is False


class TestRSIEdgeCases:
    """RSI 邊界情況測試."""
    
    def test_rsi_with_very_large_numbers(self):
        """測試非常大的價格數字."""
        prices = [100000 + i * 1000 for i in range(20)]
        rsi = RSICalculator.calculate_rsi(prices)
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_with_very_small_numbers(self):
        """測試非常小的價格數字."""
        prices = [0.0001 + i * 0.00001 for i in range(20)]
        rsi = RSICalculator.calculate_rsi(prices)
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_with_negative_numbers(self):
        """測試負價格數字（不真實但測試魯棒性）."""
        prices = [-10.0 + i for i in range(20)]
        rsi = RSICalculator.calculate_rsi(prices)
        # 應該仍然計算有效的 RSI
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_alternating_prices(self):
        """測試振盪價格."""
        prices = [100.0, 95.0, 100.0, 95.0] * 5
        rsi = RSICalculator.calculate_rsi(prices)
        # 振盪應該產生中立的 RSI
        assert rsi is not None
        assert 40 < rsi < 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
