"""RSI 計算與快取服務 - 為警報系統提供高效的 RSI 更新."""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
import redis
import json

from app.database import get_supabase
from app.services.market_data import get_historical_prices
from app.services.technical_indicators import RSICalculator

logger = logging.getLogger(__name__)

# Redis 快取配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# 快取鍵前綴和 TTL
RSI_CACHE_PREFIX = "rsi:"
RSI_CACHE_TTL = 300  # 5 分鐘
HISTORICAL_PRICES_CACHE_PREFIX = "prices:"
HISTORICAL_PRICES_CACHE_TTL = 3600  # 1 小時

# 最小數據點數
MIN_DATA_POINTS = 14


class RSICacheService:
    """RSI 計算與快取服務."""
    
    def __init__(self):
        """初始化 Redis 連接."""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            # 測試連接
            self.redis_client.ping()
            logger.info("✓ Redis 連接成功")
        except Exception as e:
            logger.warning(f"⚠ Redis 連接失敗: {e}，將使用內存緩存")
            self.redis_client = None
    
    def _get_cache_key(self, symbol: str) -> str:
        """生成 RSI 快取鍵."""
        return f"{RSI_CACHE_PREFIX}{symbol.upper()}"
    
    def _get_prices_cache_key(self, symbol: str) -> str:
        """生成歷史價格快取鍵."""
        return f"{HISTORICAL_PRICES_CACHE_PREFIX}{symbol.upper()}"
    
    async def calculate_and_cache_rsi(
        self,
        symbol: str,
        category: str,
        period: int = 14,
        force_refresh: bool = False
    ) -> Optional[float]:
        """
        計算並快取 RSI 值.
        
        Args:
            symbol: 資產代碼
            category: 資產類別 (us_etf, tw_etf, 等)
            period: RSI 計算週期
            force_refresh: 是否忽略快取強制重新計算
        
        Returns:
            計算的 RSI 值，或 None 如果計算失敗
        """
        # 嘗試從快取獲取
        if not force_refresh:
            cached_rsi = self._get_from_cache(symbol)
            if cached_rsi is not None:
                logger.debug(f"RSI 快取命中: {symbol} = {cached_rsi}")
                return cached_rsi
        
        # 獲取歷史價格
        close_prices = await self._fetch_or_cache_prices(symbol, category)
        if not close_prices or len(close_prices) < MIN_DATA_POINTS:
            logger.warning(f"無法獲取足夠的歷史數據: {symbol} ({len(close_prices or [])} 點)")
            return None
        
        # 計算 RSI
        rsi = RSICalculator.calculate_rsi(close_prices, period=period)
        
        if rsi is not None:
            # 緩存 RSI 值
            self._cache_rsi(symbol, rsi)
            logger.info(f"✓ RSI 計算完成: {symbol} = {rsi:.2f}")
        
        return rsi
    
    async def _fetch_or_cache_prices(
        self,
        symbol: str,
        category: str,
        days: int = 30
    ) -> Optional[List[float]]:
        """
        獲取或快取歷史閉盤價.
        
        Args:
            symbol: 資產代碼
            category: 資產類別
            days: 需要的歷史天數
        
        Returns:
            收盤價列表 (從舊到新排序)
        """
        cache_key = self._get_prices_cache_key(symbol)
        
        # 嘗試從快取獲取
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"價格快取命中: {symbol}")
            return json.loads(cached)
        
        try:
            # 計算日期範圍
            from datetime import datetime, timedelta, timezone
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=days + 10)  # 多獲取 10 天以應對市場休市
            
            # 獲取歷史數據
            prices_series = await get_historical_prices(
                symbol, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            
            if prices_series is not None and len(prices_series) > 0:
                prices = prices_series.tolist()
                if prices:
                    # 緩存價格
                    self._cache_prices(cache_key, prices)
                    logger.info(f"已獲取 {symbol} 的 {len(prices)} 天歷史價格")
                    return prices
            
            logger.warning(f"無法獲取歷史價格: {symbol}")
            return None
        
        except Exception as e:
            logger.error(f"獲取歷史價格失敗: {symbol} - {type(e).__name__}: {e}")
            return None
    
    def _cache_rsi(self, symbol: str, rsi: float) -> None:
        """快取 RSI 值."""
        key = self._get_cache_key(symbol)
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    RSI_CACHE_TTL,
                    json.dumps({"value": rsi, "timestamp": datetime.now(timezone.utc).isoformat()})
                )
            # 也要更新到數據庫
            logger.debug(f"RSI 值已緩存: {symbol}")
        except Exception as e:
            logger.error(f"RSI 緩存失敗: {symbol} - {e}")
    
    def _cache_prices(self, key: str, prices: List[float]) -> None:
        """快取歷史價格."""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    HISTORICAL_PRICES_CACHE_TTL,
                    json.dumps(prices)
                )
            logger.debug(f"價格已緩存: {key}")
        except Exception as e:
            logger.error(f"價格緩存失敗: {key} - {e}")
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """從快取獲取數據."""
        try:
            if self.redis_client:
                return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"快取查詢失敗: {key} - {e}")
        return None
    
    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """
        清除快取.
        
        Args:
            symbol: 特定資產代碼，或 None 清除全部
        
        Returns:
            成功清除返回 True
        """
        try:
            if not self.redis_client:
                return False
            
            if symbol:
                # 清除特定資產的快取
                keys = [
                    self._get_cache_key(symbol),
                    self._get_prices_cache_key(symbol)
                ]
                for key in keys:
                    self.redis_client.delete(key)
                logger.info(f"已清除 {symbol} 的快取")
            else:
                # 清除所有 RSI 快取
                pattern = f"{RSI_CACHE_PREFIX}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                logger.info(f"已清除所有 RSI 快取 ({len(keys)} 鍵)")
            
            return True
        except Exception as e:
            logger.error(f"清除快取失敗: {e}")
            return False


class RSICalculationService:
    """RSI 計算服務 - 更新數據庫中的 RSI 值."""
    
    def __init__(self):
        """初始化服務."""
        self.cache_service = RSICacheService()
        self.sb = get_supabase()
    
    async def update_rsi_for_tracked_index(
        self,
        tracking_id: str,
        symbol: str,
        category: str,
        rsi_period: int = 14,
        force_refresh: bool = False
    ) -> bool:
        """
        為單個追蹤項目更新 RSI 值.
        
        Args:
            tracking_id: 追蹤記錄 ID
            symbol: 資產代碼
            category: 資產類別
            rsi_period: RSI 計算週期
            force_refresh: 是否強制重新計算，忽略快取
        
        Returns:
            成功返回 True
        """
        try:
            # 計算 RSI
            rsi = await self.cache_service.calculate_and_cache_rsi(
                symbol,
                category,
                period=rsi_period,
                force_refresh=force_refresh
            )
            
            if rsi is None:
                logger.warning(f"無法計算 RSI: {symbol}")
                return False
            
            # 更新數據庫
            update_data = {
                "current_rsi": round(rsi, 2),
                "rsi_updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            res = self.sb.table("tracked_indices").update(update_data).eq(
                "id", tracking_id
            ).execute()
            
            if res.data:
                logger.info(f"✓ 已更新 RSI: {symbol} (ID: {tracking_id}) = {rsi:.2f}")
                return True
            else:
                logger.error(f"數據庫更新失敗: {tracking_id}")
                return False
        
        except Exception as e:
            logger.error(f"更新 RSI 失敗: {tracking_id} - {e}")
            return False
    
    async def update_all_active_rsi(self) -> Dict[str, int]:
        """
        更新所有活躍追蹤項目的 RSI.
        
        Returns:
            包含成功/失敗計數的字典
        """
        try:
            # 獲取所有需要 RSI 計算的活躍追蹤項目
            res = self.sb.table("tracked_indices").select(
                "id, symbol, category, rsi_period"
            ).eq("is_active", True).in_(
                "trigger_mode", ["rsi", "both"]
            ).execute()
            
            if not res.data:
                logger.info("無活躍的 RSI 觸發項目")
                return {"success": 0, "failed": 0}
            
            # 並行更新 RSI
            tasks = [
                self.update_rsi_for_tracked_index(
                    item["id"],
                    item["symbol"],
                    item["category"],
                    item.get("rsi_period", 14)
                )
                for item in res.data
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 統計結果
            success_count = sum(1 for r in results if r is True)
            failed_count = len(results) - success_count
            
            logger.info(f"RSI 批量更新完成: {success_count} 成功, {failed_count} 失敗")
            
            return {
                "success": success_count,
                "failed": failed_count,
                "total": len(res.data)
            }
        
        except Exception as e:
            logger.error(f"批量更新 RSI 失敗: {e}")
            return {"success": 0, "failed": 0, "error": str(e)}
    
    async def check_rsi_trigger(
        self,
        symbol: str,
        current_rsi: Optional[float],
        rsi_below: Optional[float],
        rsi_above: Optional[float]
    ) -> bool:
        """
        檢查 RSI 是否滿足觸發條件.
        
        Args:
            symbol: 資產代碼
            current_rsi: 當前 RSI 值
            rsi_below: 超賣閾值
            rsi_above: 超買閾值
        
        Returns:
            滿足任何條件返回 True
        """
        if current_rsi is None:
            return False
        
        triggered = False
        
        if rsi_below is not None and current_rsi < rsi_below:
            logger.debug(f"RSI 超賣觸發: {symbol} ({current_rsi:.2f} < {rsi_below})")
            triggered = True
        
        if rsi_above is not None and current_rsi > rsi_above:
            logger.debug(f"RSI 超買觸發: {symbol} ({current_rsi:.2f} > {rsi_above})")
            triggered = True
        
        return triggered
    
    async def get_historical_rsi_data(
        self,
        symbol: str,
        category: str,
        rsi_period: int = 14,
        days: int = 30
    ) -> Optional[Dict[str, List]]:
        """
        獲取歷史 RSI 數據 (帶日期).
        
        Args:
            symbol: 資產代碼
            category: 資產類別
            rsi_period: RSI 計算週期
            days: 要返回的歷史天數
        
        Returns:
            包含日期和RSI值列表的字典，或 None 如果失敗
            格式: {"dates": ["2024-03-20", ...], "rsi_values": [45.2, ...]}
        """
        try:
            from app.services.market_data import get_historical_prices
            from app.services.technical_indicators import RSICalculator
            import pandas as pd
            
            # 計算需要的日曆天數：days 個有效交易日 RSI + rsi_period 預熱
            # 交易日約為日曆天的 5/7，再加 14 天 buffer（假日/長假）
            calendar_days_needed = int((days + rsi_period) * 7 / 5) + 14
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=calendar_days_needed)
            
            logger.debug(f"獲取 {symbol} 的歷史價格: {start_date} 到 {end_date} (需要 {calendar_days_needed} 日曆天以確保足夠交易日)")

            # RSI 計算使用還原價格（adjusted），避免除息造成假訊號
            prices_series = await get_historical_prices(
                symbol, start_date.isoformat(), end_date.isoformat(), adjusted=True
            )
            
            if prices_series is None or prices_series.empty:
                logger.warning(f"無法獲取 {symbol} 的歷史價格")
                return None
            
            # 圖表顯示使用實際收盤價（unadjusted），對應券商與 Yahoo Finance 顯示的數值
            display_prices_series = await get_historical_prices(
                symbol, start_date.isoformat(), end_date.isoformat(), adjusted=False
            )
            # 若未還原價格獲取失敗，退回使用還原價格
            if display_prices_series is None or display_prices_series.empty:
                logger.warning(f"無法獲取 {symbol} 實際收盤價，退回使用還原價格")
                display_prices_series = prices_series
            
            close_prices = prices_series.tolist()
            
            if len(close_prices) < rsi_period + 1:
                logger.warning(f"歷史數據不足: {symbol} 只有 {len(close_prices)} 天")
                return None
            
            # 計算 RSI 序列（使用還原價格）
            rsi_values = RSICalculator.calculate_rsi_series(close_prices, period=rsi_period)
            
            # 對齊 adjusted index 與 display prices（以日期索引取值，缺失時退回 adjusted）
            dates_list = prices_series.index.tolist()
            display_close_list = [
                float(display_prices_series.get(date, adj_price))
                for date, adj_price in zip(dates_list, close_prices)
            ]
            
            # 濾除 RSI 預熱期的 None，只保留有效數值的資料點
            valid_pairs = [
                (date, rsi, display_price)
                for date, rsi, display_price in zip(dates_list, rsi_values, display_close_list)
                if rsi is not None
            ]
            
            # 只取最近 days 天的有效資料
            valid_pairs = valid_pairs[-days:]
            
            # 轉換日期格式
            formatted_data = []
            for date, rsi, display_price in valid_pairs:
                date_str = pd.Timestamp(date).strftime('%m/%d') if hasattr(date, 'strftime') else str(date)
                formatted_data.append({
                    "date": date_str,
                    "rsi": round(rsi, 2),
                    "price": round(display_price, 4)
                })
            
            logger.info(f"✓ 獲取 RSI 歷史數據完成: {symbol}, {len(formatted_data)} 天")
            
            # 分開日期和值用於前端圖表
            dates = [item["date"] for item in formatted_data]
            values = [item["rsi"] for item in formatted_data]
            prices = [item["price"] for item in formatted_data]
            
            return {
                "symbol": symbol,
                "period": rsi_period,
                "dates": dates,
                "rsi_values": values,
                "prices": prices
            }
        
        except Exception as e:
            logger.error(f"獲取歷史 RSI 數據失敗: {symbol} - {type(e).__name__}: {e}")
            return None


# 全局實例
_cache_service = None
_calculation_service = None


def get_rsi_cache_service() -> RSICacheService:
    """獲取 RSI 快取服務實例."""
    global _cache_service
    if _cache_service is None:
        _cache_service = RSICacheService()
    return _cache_service


def get_rsi_calculation_service() -> RSICalculationService:
    """獲取 RSI 計算服務實例."""
    global _calculation_service
    if _calculation_service is None:
        _calculation_service = RSICalculationService()
    return _calculation_service
