"""技術指標計算引擎 - 支持 RSI 及其他指標."""

from typing import List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta


class RSICalculator:
    """
    相對強度指數 (Relative Strength Index) 計算器.
    
    RSI 是一個動量指標，衡量價格變動的速度和變化幅度。
    值在 0-100 之間：
    - RSI < 30: 超賣信號
    - RSI > 70: 超買信號
    """
    
    DEFAULT_PERIOD = 14
    
    @staticmethod
    def calculate_rsi(
        close_prices: List[float],
        period: int = DEFAULT_PERIOD
    ) -> Optional[float]:
        """
        計算相對強度指數 (RSI).
        
        Args:
            close_prices: 從舊到新排序的收盤價列表
            period: RSI 計算週期 (預設: 14)
        
        Returns:
            計算出的 RSI 值 (0-100)，或 None 如果數據不足
            
        Raises:
            ValueError: 如果 period 無效或列表為空
        """
        # 驗證輸入
        if not close_prices or len(close_prices) < 2:
            return None
            
        if period < 2 or period >= len(close_prices):
            return None
        
        # 轉換為 numpy 數組，處理 NaN 值
        prices = np.array(close_prices, dtype=float)
        if np.isnan(prices).any():
            return None
        
        # 計算價格變動
        deltas = np.diff(prices)
        
        # 分離上升和下降
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 計算平均收益和平均損失 (使用簡單移動平均)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        # 避免除以零
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        # 計算相對強度 (RS)
        rs = avg_gain / avg_loss
        
        # 計算 RSI
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    @staticmethod
    def calculate_rsi_series(
        close_prices: List[float],
        period: int = DEFAULT_PERIOD
    ) -> List[Optional[float]]:
        """
        計算一系列 RSI 值.
        
        Args:
            close_prices: 從舊到新排序的收盤價列表
            period: RSI 計算週期 (預設: 14)
        
        Returns:
            RSI 值列表，長度等於輸入列表，前 period 個值為 None
        """
        rsi_values = []
        
        for i in range(len(close_prices)):
            if i < period:
                rsi_values.append(None)
            else:
                rsi = RSICalculator.calculate_rsi(
                    close_prices[:i + 1],
                    period
                )
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def is_oversold(rsi: Optional[float], threshold: float = 30.0) -> bool:
        """
        檢查 RSI 是否超賣.
        
        Args:
            rsi: RSI 值
            threshold: 超賣閾值 (預設: 30)
        
        Returns:
            True 如果 RSI < threshold，否則 False
        """
        return rsi is not None and rsi < threshold
    
    @staticmethod
    def is_overbought(rsi: Optional[float], threshold: float = 70.0) -> bool:
        """
        檢查 RSI 是否超買.
        
        Args:
            rsi: RSI 值
            threshold: 超買閾值 (預設: 70)
        
        Returns:
            True 如果 RSI > threshold，否則 False
        """
        return rsi is not None and rsi > threshold


class TechnicalIndicators:
    """技術指標計合器，提供多種指標計算方法."""
    
    @staticmethod
    def calculate_rsi(
        close_prices: List[float],
        period: int = RSICalculator.DEFAULT_PERIOD
    ) -> Optional[float]:
        """計算最後一個 RSI 值."""
        return RSICalculator.calculate_rsi(close_prices, period)
    
    @staticmethod
    def calculate_moving_average(
        prices: List[float],
        period: int = 20
    ) -> Optional[float]:
        """
        計算簡單移動平均 (SMA).
        
        Args:
            prices: 價格列表
            period: 移動平均週期
        
        Returns:
            最後一個移動平均值，或 None 如果數據不足
        """
        if not prices or len(prices) < period:
            return None
        
        prices_array = np.array(prices[-period:], dtype=float)
        if np.isnan(prices_array).any():
            return None
        
        return float(np.mean(prices_array))
    
    @staticmethod
    def calculate_volatility(
        close_prices: List[float],
        period: int = 20
    ) -> Optional[float]:
        """
        計算波動性 (標準差).
        
        Args:
            close_prices: 收盤價列表
            period: 波動性計算週期
        
        Returns:
            波動性值 (標準差)，或 None 如果數據不足
        """
        if not close_prices or len(close_prices) < period:
            return None
        
        prices_array = np.array(close_prices[-period:], dtype=float)
        if np.isnan(prices_array).any():
            return None
        
        return float(np.std(prices_array))
    
    @staticmethod
    def calculate_macd(
        close_prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Tuple[float, float, float]]:
        """
        計算 MACD (移動平均收斂發散).
        
        Args:
            close_prices: 收盤價列表
            fast_period: 快速 EMA 週期
            slow_period: 慢速 EMA 週期
            signal_period: 信號線週期
        
        Returns:
            (MACD, Signal, Histogram) 元組，或 None 如果數據不足
        """
        if not close_prices or len(close_prices) < slow_period:
            return None
        
        prices_array = np.array(close_prices, dtype=float)
        if np.isnan(prices_array).any():
            return None
        
        # 計算 EMA
        fast_ema = TechnicalIndicators._calculate_ema(prices_array, fast_period)
        slow_ema = TechnicalIndicators._calculate_ema(prices_array, slow_period)
        
        if fast_ema is None or slow_ema is None:
            return None
        
        macd = fast_ema - slow_ema
        signal = TechnicalIndicators._calculate_ema(
            np.array([macd], dtype=float),
            signal_period
        )
        
        if signal is None:
            return None
        
        histogram = macd - signal
        
        return (float(macd), float(signal), float(histogram))
    
    @staticmethod
    def _calculate_ema(
        prices: np.ndarray,
        period: int
    ) -> Optional[float]:
        """計算指數移動平均 (EMA) 的最後一個值."""
        if len(prices) < period:
            return None
        
        # 計算乘數
        multiplier = 2 / (period + 1)
        
        # 初始化 EMA 為簡單移動平均
        ema = np.mean(prices[:period])
        
        # 計算後續 EMA 值
        for i in range(period, len(prices)):
            ema = (prices[i] - ema) * multiplier + ema
        
        return float(ema)


def validate_rsi_triggers(
    rsi_value: Optional[float],
    rsi_below: Optional[float],
    rsi_above: Optional[float]
) -> bool:
    """
    驗證 RSI 是否滿足觸發條件.
    
    Args:
        rsi_value: 當前 RSI 值
        rsi_below: RSI 應低於此值（超賣條件）
        rsi_above: RSI 應高於此值（超買條件）
    
    Returns:
        True 如果滿足任何非 None 的條件
    """
    if rsi_value is None:
        return False
    
    if rsi_below is not None and rsi_value < rsi_below:
        return True
    
    if rsi_above is not None and rsi_value > rsi_above:
        return True
    
    return False
