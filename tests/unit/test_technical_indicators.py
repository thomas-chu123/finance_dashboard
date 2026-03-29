"""單元測試 — RSI 及技術指標計算."""
import pytest
import allure
import math

from app.services.technical_indicators import (
    RSICalculator,
    TechnicalIndicators,
    validate_rsi_triggers,
)


@allure.epic("技術分析")
@allure.feature("RSI 計算器")
@pytest.mark.unit
class TestRSICalculator:
    """RSI 計算器測試."""

    @allure.story("基本計算")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_rsi_result_in_valid_range(self, sample_prices_mixed):
        """RSI 結果必須介於 0 至 100 之間."""
        rsi = RSICalculator.calculate_rsi(sample_prices_mixed)
        assert rsi is not None
        assert 0.0 <= rsi <= 100.0

    @allure.story("數據不足")
    @allure.severity(allure.severity_level.NORMAL)
    def test_insufficient_data_returns_none(self):
        """少於 period+1 個數據點時應回傳 None."""
        assert RSICalculator.calculate_rsi([1.0, 2.0], period=14) is None

    @allure.story("數據不足")
    def test_empty_list_returns_none(self):
        """空列表應回傳 None."""
        assert RSICalculator.calculate_rsi([]) is None

    @allure.story("數據不足")
    def test_single_price_returns_none(self):
        """單一價格應回傳 None."""
        assert RSICalculator.calculate_rsi([100.0]) is None

    @allure.story("邊界值")
    def test_nan_in_prices_returns_none(self):
        """包含 NaN 的數據應回傳 None."""
        assert RSICalculator.calculate_rsi([1.0, 2.0, float("nan"), 4.0]) is None

    @allure.story("邊界值")
    @allure.severity(allure.severity_level.NORMAL)
    def test_constant_prices_returns_50(self):
        """恆定不變的價格應回傳 RSI = 50（無漲跌）."""
        prices = [100.0] * 15
        rsi = RSICalculator.calculate_rsi(prices)
        assert rsi == 50.0

    @allure.story("超買偵測")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_all_rising_prices_high_rsi(self, sample_prices_rising):
        """持續上升價格應產生高 RSI（> 70，超買）."""
        rsi = RSICalculator.calculate_rsi(sample_prices_rising, period=14)
        assert rsi is not None
        assert rsi > 70

    @allure.story("超賣偵測")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_all_falling_prices_low_rsi(self, sample_prices_falling):
        """持續下降價格應產生低 RSI（< 30，超賣）."""
        rsi = RSICalculator.calculate_rsi(sample_prices_falling, period=14)
        assert rsi is not None
        assert rsi < 30

    @allure.story("週期設定")
    def test_custom_period_calculation(self, sample_prices_mixed):
        """不同 RSI 週期應都回傳有效範圍內的值."""
        rsi_7 = RSICalculator.calculate_rsi(sample_prices_mixed, period=7)
        rsi_14 = RSICalculator.calculate_rsi(sample_prices_mixed, period=14)
        for rsi in (rsi_7, rsi_14):
            assert rsi is not None
            assert 0.0 <= rsi <= 100.0

    @allure.story("序列計算")
    def test_rsi_series_length_matches_input(self):
        """RSI 序列長度應與輸入一致."""
        prices = list(range(1, 25))
        series = RSICalculator.calculate_rsi_series(prices, period=14)
        assert len(series) == len(prices)

    @allure.story("序列計算")
    def test_rsi_series_first_n_are_none(self):
        """RSI 序列前 period 個值應為 None（尚無足夠歷史數據）."""
        prices = list(range(1, 25))
        series = RSICalculator.calculate_rsi_series(prices, period=14)
        for i in range(14):
            assert series[i] is None

    @allure.story("信號偵測")
    @allure.severity(allure.severity_level.NORMAL)
    def test_is_oversold_thresholds(self):
        """超賣閾值邊界測試."""
        assert RSICalculator.is_oversold(25.0) is True    # 低於 30 → 超賣
        assert RSICalculator.is_oversold(30.0) is False   # 等於 30 → 非超賣
        assert RSICalculator.is_oversold(50.0) is False
        assert RSICalculator.is_oversold(None) is False

    @allure.story("信號偵測")
    @allure.severity(allure.severity_level.NORMAL)
    def test_is_overbought_thresholds(self):
        """超買閾值邊界測試."""
        assert RSICalculator.is_overbought(75.0) is True  # 高於 70 → 超買
        assert RSICalculator.is_overbought(70.0) is False # 等於 70 → 非超買
        assert RSICalculator.is_overbought(50.0) is False
        assert RSICalculator.is_overbought(None) is False

    @allure.story("信號偵測")
    def test_custom_oversold_threshold(self):
        """自訂超賣閾值應正確作用."""
        assert RSICalculator.is_oversold(34.9, threshold=35.0) is True
        assert RSICalculator.is_oversold(35.0, threshold=35.0) is False

    @allure.story("信號偵測")
    def test_custom_overbought_threshold(self):
        """自訂超買閾值應正確作用."""
        assert RSICalculator.is_overbought(65.1, threshold=65.0) is True
        assert RSICalculator.is_overbought(65.0, threshold=65.0) is False


@allure.epic("技術分析")
@allure.feature("通用技術指標")
@pytest.mark.unit
class TestTechnicalIndicators:
    """SMA、Volatility、MACD 測試."""

    @allure.story("移動平均")
    @allure.severity(allure.severity_level.NORMAL)
    def test_moving_average_basic(self):
        """SMA 三期應計算正確平均值."""
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        ma = TechnicalIndicators.calculate_moving_average(prices, period=3)
        assert ma == pytest.approx(4.0)

    @allure.story("移動平均")
    def test_moving_average_insufficient_data(self):
        """數據不足時應回傳 None."""
        assert TechnicalIndicators.calculate_moving_average([1.0], period=5) is None

    @allure.story("波動度")
    @allure.severity(allure.severity_level.NORMAL)
    def test_volatility_constant_prices(self):
        """恆定價格的波動度應為 0."""
        prices = [100.0] * 20
        vol = TechnicalIndicators.calculate_volatility(prices)
        assert vol == pytest.approx(0.0, abs=1e-10)

    @allure.story("波動度")
    def test_volatility_positive_for_varying_prices(self):
        """有變化的價格序列應產生正的年化波動度."""
        prices = [100.0, 102.0, 98.0, 105.0, 101.0, 103.0,
                  99.0, 107.0, 104.0, 106.0, 100.0, 108.0,
                  102.0, 109.0, 103.0, 111.0, 105.0, 112.0,
                  108.0, 115.0, 110.0]
        vol = TechnicalIndicators.calculate_volatility(prices)
        assert vol is not None
        assert vol > 0.0


@allure.epic("技術分析")
@allure.feature("RSI 觸發驗證器")
@pytest.mark.unit
class TestValidateRSITriggers:
    """validate_rsi_triggers 函數測試."""

    @allure.story("超賣觸發")
    def test_trigger_when_rsi_below_threshold(self):
        """RSI 低於下限應觸發."""
        assert validate_rsi_triggers(25.0, rsi_below=30.0, rsi_above=None) is True

    @allure.story("超賣觸發 - 邊界")
    def test_no_trigger_when_rsi_equals_below_threshold(self):
        """RSI 等於下限時應不觸發（嚴格小於）."""
        assert validate_rsi_triggers(30.0, rsi_below=30.0, rsi_above=None) is False

    @allure.story("超買觸發")
    def test_trigger_when_rsi_above_threshold(self):
        """RSI 高於上限應觸發."""
        assert validate_rsi_triggers(75.0, rsi_below=None, rsi_above=70.0) is True

    @allure.story("超買觸發 - 邊界")
    def test_no_trigger_when_rsi_equals_above_threshold(self):
        """RSI 等於上限時應不觸發（嚴格大於）."""
        assert validate_rsi_triggers(70.0, rsi_below=None, rsi_above=70.0) is False

    @allure.story("無閾值")
    def test_no_trigger_when_no_thresholds(self):
        """未設閾值時不應觸發."""
        assert validate_rsi_triggers(50.0, rsi_below=None, rsi_above=None) is False

    @allure.story("None RSI")
    def test_no_trigger_when_rsi_is_none(self):
        """RSI 值為 None 時不應觸發."""
        assert validate_rsi_triggers(None, rsi_below=30.0, rsi_above=70.0) is False

    @allure.story("雙向閾值")
    def test_normal_range_no_trigger(self):
        """RSI 在正常範圍內（30–70）應不觸發."""
        assert validate_rsi_triggers(50.0, rsi_below=30.0, rsi_above=70.0) is False
