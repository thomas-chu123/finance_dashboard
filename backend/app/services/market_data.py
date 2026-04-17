import logging
import os
import httpx
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from app.config import get_settings

logger = logging.getLogger(__name__)

FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"

# Note: FINMIND_API_TOKEN 使用延遲讀取（在函數中讀取）
# 而不是模塊級別讀取，以確保 Pydantic 環境變數已加載
def _get_finmind_token() -> Optional[str]:
    """延遲讀取 FinMind API token（從 Pydantic Settings），確保環境變數已加載。"""
    settings = get_settings()
    token = settings.finmind_api
    return token if token and token != "your_finmind_api_token" else None

# Popular index symbols mapping
SYMBOL_MAP = {
    "VIX": "^VIX",
    "OIL": "CL=F",
    "CRUDE_OIL": "CL=F",
    "BRENT": "BZ=F",
    "GOLD": "GC=F",
    "TAIEX": "^TWII",
}

# RSI 代理映射：當符號本身無歷史數據時，使用相關性高的代理符號計算 RSI
# WTX& = 台指數夜盤，yfinance 無歷史數據，使用 ^TWII (TAIEX) 作為代理
RSI_PROXY_MAP = {
    "WTX&": "^TWII",
}

# 完整的符號目錄（SSOT - Single Source of Truth）
# 儲存所有支援的符號、映射、類別和顯示信息
SYMBOL_CATALOG = {
    # 指數
    "TAIEX": {
        "symbol": "TAIEX",
        "yahoo_symbol": "^TWII",
        "url_path": "quote/%5ETWII",
        "name_zh": "台灣加權股價指數",
        "name_en": "Taiwan Weighted Stock Index",
        "category": "index",
        "domain": "tw.stock.yahoo.com"
    },
    "WTX&": {
        "symbol": "WTX&",
        "yahoo_symbol": "WTX&",
        "url_path": "future/WTX&",
        "name_zh": "台指數夜盤",
        "name_en": "Taiwan Index Night Session",
        "category": "index",
        "domain": "tw.stock.yahoo.com"
    },
    # VIX (波動指數)
    "VIX": {
        "symbol": "VIX",
        "yahoo_symbol": "^VIX",
        "url_path": "quote/%5EVIX",
        "name_zh": "CBOE 波動指數",
        "name_en": "CBOE Volatility Index (VIX)",
        "category": "vix",
        "domain": "finance.yahoo.com"
    },
    # 期貨
    "GOLD": {
        "symbol": "GOLD",
        "yahoo_symbol": "GC=F",
        "url_path": "quote/GC=F",
        "name_zh": "黃金期貨",
        "name_en": "Gold Futures",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "OIL": {
        "symbol": "OIL",
        "yahoo_symbol": "CL=F",
        "url_path": "quote/CL=F",
        "name_zh": "WTI 原油期貨",
        "name_en": "WTI Crude Oil Futures",
        "category": "oil",
        "domain": "finance.yahoo.com"
    },
    "BRENT": {
        "symbol": "BRENT",
        "yahoo_symbol": "BZ=F",
        "url_path": "quote/BZ%3DF",
        "name_zh": "布倫特原油期貨",
        "name_en": "Brent Crude Oil Futures",
        "category": "oil",
        "domain": "finance.yahoo.com"
    },
    # 全球指數
    "^GSPC": {
        "symbol": "^GSPC",
        "yahoo_symbol": "^GSPC",
        "url_path": "quote/%5EGSPC",
        "name_zh": "S&P 500 指數",
        "name_en": "S&P 500 Index",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^IXIC": {
        "symbol": "^IXIC",
        "yahoo_symbol": "^IXIC",
        "url_path": "quote/%5EIXIC",
        "name_zh": "納斯達克綜合指數",
        "name_en": "Nasdaq Composite",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^DJI": {
        "symbol": "^DJI",
        "yahoo_symbol": "^DJI",
        "url_path": "quote/%5EDJI",
        "name_zh": "道瓊工業平均指數",
        "name_en": "Dow Jones Industrial Average",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^N225": {
        "symbol": "^N225",
        "yahoo_symbol": "^N225",
        "url_path": "quote/%5EN225",
        "name_zh": "日經 225 指數",
        "name_en": "Nikkei 225",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^STOXX50E": {
        "symbol": "^STOXX50E",
        "yahoo_symbol": "^STOXX50E",
        "url_path": "quote/%5ESTOXX50E",
        "name_zh": "歐洲 Stoxx 50 指數",
        "name_en": "Euro Stoxx 50",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^FTSE": {
        "symbol": "^FTSE",
        "yahoo_symbol": "^FTSE",
        "url_path": "quote/%5EFTSE",
        "name_zh": "富時 100 指數",
        "name_en": "FTSE 100",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
    "^HSI": {
        "symbol": "^HSI",
        "yahoo_symbol": "^HSI",
        "url_path": "quote/%5EHSI",
        "name_zh": "香港恆生指數",
        "name_en": "Hang Seng Index",
        "category": "index",
        "domain": "finance.yahoo.com"
    },
}

TW_SUFFIXES = {".TW", ".TWO"}


def _to_yf_symbol(symbol: str) -> str:
    """Convert symbol to yfinance format."""
    upper = symbol.upper()
    if upper in SYMBOL_MAP:
        return SYMBOL_MAP[upper]
    # Taiwan ETF: append .TW if numeric
    if symbol.replace("-", "").replace("B", "").isdigit():
        return f"{symbol}.TW"
    return symbol


def _is_taiwan_stock(symbol: str) -> bool:
    """Detect if a symbol is a Taiwan stock/ETF."""
    if symbol.isdigit() or any(symbol.upper().endswith(s) for s in TW_SUFFIXES):
        return True
    return False


def get_symbol_currency(symbol: str) -> str:
    """Identify the currency of a symbol (USD or TWD)."""
    if _is_taiwan_stock(symbol):
        return "TWD"
    if symbol.upper() in ["TAIEX", "^TWII"]:
        return "TWD"
    # Exchange rates like TWD=X are USD-based (1 USD = X TWD)
    # But currently they are symbols themselves.
    return "USD"


def _clean_tw_symbol(symbol: str) -> str:
    """Remove .TW or .TWO for FinMind API."""
    return symbol.split(".")[0]


async def fetch_finmind_adjusted_prices(
    symbol: str, start_date: str, end_date: str
) -> pd.Series:
    """Fetch adjusted prices from FinMind API (TaiwanStockPriceAdj)."""
    return await _fetch_finmind_prices(symbol, start_date, end_date, dataset="TaiwanStockPriceAdj")


async def fetch_finmind_unadjusted_prices(
    symbol: str, start_date: str, end_date: str
) -> pd.Series:
    """
    Fetch unadjusted (raw) closing prices from FinMind API (TaiwanStockPrice - Free Tier).
    
    Note: This dataset returns raw close prices without dividend/split adjustments.
    Used as backup when yfinance fails (extremely rare).
    """
    return await _fetch_finmind_prices(symbol, start_date, end_date, dataset="TaiwanStockPrice")


async def _fetch_finmind_prices(
    symbol: str, start_date: str, end_date: str, dataset: str
) -> pd.Series:
    """
    Internal helper: Fetch closing prices from FinMind API for specified dataset.
    
    Datasets:
      - TaiwanStockPriceAdj: Adjusted prices (dividends + splits) - Requires paid tier
      - TaiwanStockPrice: Raw prices (unadjusted) - Free tier, used as backup
    """
    token = _get_finmind_token()
    if not token:
        logger.warning("[MarketData] FinMind_API token not found in environment.")
        return pd.Series(dtype=float)

    clean_sym = _clean_tw_symbol(symbol)
    params = {
        "dataset": dataset,
        "data_id": clean_sym,
        "start_date": start_date,
        "end_date": end_date,
        "token": token,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(FINMIND_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != 200 or not data.get("data"):
                logger.warning(f"[MarketData] FinMind returned no data for {clean_sym} ({dataset}): {data.get('msg')}")
                return pd.Series(dtype=float)

            df = pd.DataFrame(data["data"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            
            price_col = "close" if "close" in df.columns else df.columns[0]
            series = df[price_col].astype(float)
            series.index = series.index.normalize()
            return series.rename(symbol)
    except Exception as e:
        logger.error(f"[MarketData] FinMind error for {symbol} ({dataset}): {e}")
        return pd.Series(dtype=float)


async def scrape_yahoo_tw_futures(symbol: str) -> dict:
    """Scrape live futures price from Yahoo Finance Taiwan, e.g. for WTX&."""
    url = f"https://tw.stock.yahoo.com/future/{symbol.replace('&', '%26')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            price = None
            prev_close = None
            
            price_spans = soup.find_all('span', class_=lambda c: c and 'Fz(32px)' in c)
            if price_spans:
                try:
                    price = float(price_spans[0].text.replace(',', ''))
                except ValueError:
                    pass
                
            li_elements = soup.find_all('li', class_=lambda c: c and 'price-detail-item' in c)
            for li in li_elements:
                if '昨收' in li.text:
                    spattr = li.find_all('span')
                    if len(spattr) >= 2:
                        val_text = spattr[1].text.replace(',', '')
                        try:
                            prev_close = float(val_text)
                        except ValueError:
                            pass
                            
            if price is not None:
                return {
                    "symbol": symbol,
                    "price": price,
                    "prev_close": prev_close,
                    "change": price - prev_close if prev_close is not None else 0.0,
                    "success": True
                }
            else:
                logger.warning(f"[MarketData] Could not find price in HTML for {symbol}")
    except Exception as e:
        logger.error(f"[MarketData] scrape_yahoo_tw_futures error for {symbol}: {e}")
        
    return {
        "symbol": symbol,
        "price": None,
        "prev_close": None,
        "change": 0.0,
        "success": False
    }


async def get_quote_data(symbol: str, category: str) -> dict:
    """Fetch current price and previous close for a given symbol."""
    if symbol == "WTX&":
        return await scrape_yahoo_tw_futures(symbol)

    yf_symbol = _to_yf_symbol(symbol)
    ticker = yf.Ticker(yf_symbol)
    
    # Method 1: fast_info (preferred for quotes)
    try:
        fi = ticker.fast_info
        # Try different ways to access fast_info fields
        last_price = getattr(fi, 'last_price', None)
        prev_close = getattr(fi, 'previous_close', None)
        
        if last_price is not None and prev_close is not None:
            lp = float(last_price)
            pc = float(prev_close)
            return {
                "symbol": symbol,
                "price": lp,
                "prev_close": pc,
                "change": lp - pc,
                "success": True
            }
    except Exception as e:
        logger.warning(f"[MarketData] fast_info failed for {yf_symbol}: {e}")

    # Method 2: history(period="5d") fallback
    try:
        # Use history to get the last two closed/partial bars
        df = await asyncio.to_thread(ticker.history, period="5d")
        if not df.empty:
            valid_closes = df["Close"].dropna()
            if len(valid_closes) >= 2:
                # Most recent row is current (if open) or today's close (if closed)
                # Second to last row is the previous day's close
                cp = float(valid_closes.iloc[-1])
                pc = float(valid_closes.iloc[-2])
                return {
                    "symbol": symbol,
                    "price": cp,
                    "prev_close": pc,
                    "change": cp - pc,
                    "success": True
                }
            elif len(valid_closes) == 1:
                cp = float(valid_closes.iloc[-1])
                return {
                    "symbol": symbol,
                    "price": cp,
                    "prev_close": None,
                    "change": 0.0,
                    "success": True
                }
    except Exception as e:
        logger.error(f"[MarketData] history fallback failed for {yf_symbol}: {e}")

    return {
        "symbol": symbol,
        "price": None,
        "prev_close": None,
        "change": 0.0,
        "success": False
    }


async def get_current_price(symbol: str, category: str) -> Optional[float]:
    """Fetch current price for a given symbol (backwards compatibility)."""
    data = await get_quote_data(symbol, category)
    return data.get("price")


async def get_historical_prices(
    symbol: str, start_date: str, end_date: str, adjusted: bool = True
) -> pd.Series:
    """Return daily close price series.
    
    Args:
        symbol: 資產代碼
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        adjusted: True 返回還原價格（用於 RSI/技術指標計算），
                  False 返回實際收盤價（用於圖表顯示，對應券商數據）
    """
    import time
    start_time = time.time()

    # Priority 1: yfinance (Primary data source for all symbols)
    # yfinance provides auto-adjusted prices (dividends + splits included)
    # 若符號本身無歷史數據，使用代理符號（例如 WTX& → ^TWII）
    rsi_proxy = RSI_PROXY_MAP.get(symbol.upper())
    if rsi_proxy:
        logger.info(f"[MarketData] {symbol} 無歷史數據，使用 RSI 代理: {rsi_proxy}")
        symbol_for_yf = rsi_proxy
    else:
        symbol_for_yf = symbol

    try:
        yf_symbol = _to_yf_symbol(symbol_for_yf)
        ticker = yf.Ticker(yf_symbol)
        if adjusted:
            # auto_adjust=True: Close 欄位已還原除息、分割（用於計算 RSI）
            hist = await asyncio.to_thread(ticker.history, start=start_date, end=end_date, auto_adjust=True)
            price_col = "Close"
        else:
            # auto_adjust=False: Close 為實際收盤價，Adj Close 為還原價
            hist = await asyncio.to_thread(ticker.history, start=start_date, end=end_date, auto_adjust=False)
            price_col = "Close"
        duration = time.time() - start_time
        if hist.empty:
            logger.info(f"[MarketData] No yfinance data for {symbol} ({duration:.2f}s)")
            return pd.Series(dtype=float)
            
        # 時區標準化：以交易所本地時間的日期為準，避免轉成 UTC 造成日期偏移
        # 台灣股票（Asia/Taipei = UTC+8）：若轉 UTC 則當日 0:00+08:00 → 前日 16:00 UTC → 日期少一天
        # 美股（America/New_York）：轉 UTC 不影響日期（當日 04:00 UTC）
        if hist.index.tz is not None:
            if _is_taiwan_stock(symbol):
                hist.index = hist.index.tz_convert("Asia/Taipei").tz_localize(None)
            else:
                hist.index = hist.index.tz_convert("America/New_York").tz_localize(None)
        hist.index = hist.index.normalize()
        
        # ⚠️ 檢測可能的拆股延遲問題（特別是台灣 ETF）
        if adjusted and _is_taiwan_stock(symbol):
            lag_info = detect_stock_split_lag(symbol, hist)
            if lag_info["has_lag"]:
                logger.warning(
                    f"[MarketData] ALERT: Stock split lag detected for {symbol} (yfinance): {lag_info['details']}"
                )
        
        logger.info(f"[MarketData] yfinance fetched {len(hist)} days for {symbol} (adjusted={adjusted}, {duration:.2f}s)")
        return hist[price_col].rename(symbol)
    except Exception as e:
        logger.error(f"[MarketData] yfinance error for {symbol}: {e}")
        
        # Priority 2: FinMind TaiwanStockPrice (Backup for Taiwan stocks if yfinance fails)
        # 使用 FinMind 免費層 TaiwanStockPrice（未調整價格）作為備份
        finmind_token = _get_finmind_token()
        if _is_taiwan_stock(symbol) and finmind_token:
            logger.info(f"[MarketData] yfinance failed, attempting FinMind backup for: {symbol}")
            series = await fetch_finmind_unadjusted_prices(symbol, start_date, end_date)
            if not series.empty:
                duration = time.time() - start_time
                logger.info(f"[MarketData] FinMind (backup) fetched {len(series)} days for {symbol} ({duration:.2f}s)")
                return series
        
        return pd.Series(dtype=float)


def detect_stock_split_lag(symbol: str, hist: pd.DataFrame) -> dict:
    """
    檢測 Close 和 Adj Close 是否存在異常差異，表示可能有拆股延遲問題。
    
    通過分析調整倍數的變化來判斷：
    - 正常情況：比率變化小（只受股息影響）
    - 異常情況：比率突變（表示拆股信息可能未及時更新）
    
    Returns:
        {
            "has_lag": bool,
            "adjustment_ratio_mean": float,
            "adjustment_ratio_std": float,
            "last_ratio": float,
            "details": str
        }
    """
    if hist.empty or "Close" not in hist.columns or "Adj Close" not in hist.columns:
        return {
            "has_lag": False,
            "adjustment_ratio_mean": 0,
            "adjustment_ratio_std": 0,
            "last_ratio": 0,
            "details": "Insufficient data to detect stock split lag"
        }
    
    try:
        # 計算調整倍數（Adj Close / Close）
        # 正常情況：倍數接近 1（或略低，因為有股息調整）
        # 異常情況：倍數突變（表示拆股）
        adjustment_ratio = (hist["Adj Close"] / hist["Close"]).replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(adjustment_ratio) < 2:
            return {
                "has_lag": False,
                "adjustment_ratio_mean": 0,
                "adjustment_ratio_std": 0,
                "last_ratio": 0,
                "details": "Insufficient historical data"
            }
        
        ratio_mean = adjustment_ratio.mean()
        ratio_std = adjustment_ratio.std()
        ratio_last = adjustment_ratio.iloc[-1]
        ratio_max = adjustment_ratio.max()
        ratio_min = adjustment_ratio.min()
        
        # 判定邏輯：
        # 1. 標準差 > 0.1 表示可能有拆股變化
        # 2. 最近比率與平均值差異 > 5% 表示最近可能有異常
        recent_change = abs(ratio_last - ratio_mean) / ratio_mean if ratio_mean != 0 else 0
        
        has_lag = ratio_std > 0.1 or recent_change > 0.05
        
        details = (
            f"ratio_mean={ratio_mean:.6f}, ratio_std={ratio_std:.6f}, "
            f"ratio_range=[{ratio_min:.6f}, {ratio_max:.6f}], "
            f"recent_ratio={ratio_last:.6f}, recent_change={recent_change:.2%}"
        )
        
        if has_lag:
            logger.warning(f"[MarketData] Stock split lag detected for {symbol}: {details}")
        
        return {
            "has_lag": has_lag,
            "adjustment_ratio_mean": ratio_mean,
            "adjustment_ratio_std": ratio_std,
            "last_ratio": ratio_last,
            "details": details
        }
    
    except Exception as e:
        logger.error(f"[MarketData] Error detecting stock split lag for {symbol}: {e}")
        return {
            "has_lag": False,
            "adjustment_ratio_mean": 0,
            "adjustment_ratio_std": 0,
            "last_ratio": 0,
            "details": f"Error: {str(e)}"
        }


async def fetch_tw_etf_list() -> list[dict]:
    """Fetch Taiwan ETF list — primarily from Supabase, populated by daily sync job."""
    try:
        from app.database import get_supabase
        sb = get_supabase()
        
        all_rows = []
        page_size = 1000
        start = 0
        while True:
            res = sb.table("tw_etf_list").select("symbol, name").order("symbol").range(start, start + page_size - 1).execute()
            if not res.data:
                break
            all_rows.extend(res.data)
            if len(res.data) < page_size:
                break
            start += page_size
            
        if all_rows:
            return [
                {
                    # Normalise: ensure .TW suffix so profile saves use consistent format
                    "symbol": row["symbol"] if row["symbol"].endswith((".TW", ".TWO")) else row["symbol"] + ".TW",
                    "name": row["name"],  # 相容性：用於 backtest/optimize/montecarlo
                    "name_zh": row["name"],  # 轉換為 name_zh 欄位 (用於搜尋)
                    "name_en": "",
                    "category": "tw_etf",
                    "yahoo_symbol": row["symbol"] if row["symbol"].endswith((".TW", ".TWO")) else row["symbol"] + ".TW"
                }
                for row in all_rows
            ]
        logger.warning("[MarketData] tw_etf_list table is empty — triggering one-time sync from TWSE.")
    except Exception as e:
        logger.error(f"[MarketData] Failed to query tw_etf_list from Supabase: {e}")

    # Table is empty or DB unavailable: run a live sync and then retry
    try:
        from app.services.tw_etf_sync import sync_tw_etf_list
        await sync_tw_etf_list()
        from app.database import get_supabase
        sb = get_supabase()
        res = sb.table("tw_etf_list").select("symbol, name").order("symbol").execute()
        if res.data:
            return [
                {
                    "symbol": row["symbol"] if row["symbol"].endswith((".TW", ".TWO")) else row["symbol"] + ".TW",
                    "name_zh": row["name"],  # 轉換為 name_zh 欄位
                    "name_en": "",
                    "category": "tw_etf",
                    "yahoo_symbol": row["symbol"] if row["symbol"].endswith((".TW", ".TWO")) else row["symbol"] + ".TW"
                }
                for row in res.data
            ]
    except Exception as e:
        logger.error(f"[MarketData] Live TWSE sync also failed: {e}")

    # Last-resort minimal fallback
    logger.warning("[MarketData] Returning minimal hardcoded TW ETF fallback.")
    return [
        {"symbol": "0050.TW", "name_zh": "元大台灣50", "name_en": "Yuanta Taiwan 50", "category": "tw_etf", "yahoo_symbol": "0050.TW"},
        {"symbol": "0056.TW", "name_zh": "元大高股息", "name_en": "Yuanta High Dividend ETF", "category": "tw_etf", "yahoo_symbol": "0056.TW"},
        {"symbol": "00878.TW", "name_zh": "國泰永續高股息", "name_en": "Cathay Sustainable High Dividend ETF", "category": "tw_etf", "yahoo_symbol": "00878.TW"},
        {"symbol": "006208.TW", "name_zh": "富邦台50", "name_en": "Fubon Taiwan Top 50 ETF", "category": "tw_etf", "yahoo_symbol": "006208.TW"},
    ]


async def fetch_us_etf_list() -> list[dict]:
    """Fetch US ETF list — primarily from Supabase, populated by daily sync job."""
    try:
        from app.database import get_supabase
        sb = get_supabase()
        
        all_rows = []
        page_size = 1000
        start = 0
        while True:
            res = sb.table("us_etf_list").select("symbol, name").order("symbol").range(start, start + page_size - 1).execute()
            if not res.data:
                break
            all_rows.extend(res.data)
            if len(res.data) < page_size:
                break
            start += page_size
            
        if all_rows:
            return [
                {
                    "symbol": row["symbol"],
                    "name": row["name"],  # 相容性：用於 backtest/optimize/montecarlo
                    "name_zh": row["name"],  # 轉換為 name_zh 欄位 (用於搜尋)
                    "name_en": row["name"],
                    "category": "us_etf",
                    "yahoo_symbol": row["symbol"]
                }
                for row in all_rows
            ]
        logger.warning("[MarketData] us_etf_list table is empty — triggering one-time sync from NASDAQ.")
    except Exception as e:
        logger.error(f"[MarketData] Failed to query us_etf_list from Supabase: {e}")

    # Table is empty or DB unavailable: run a live sync and then retry
    try:
        from app.services.us_etf_sync import sync_us_etf_list
        await sync_us_etf_list()
        from app.database import get_supabase
        sb = get_supabase()
        res = sb.table("us_etf_list").select("symbol, name").order("symbol").execute()
        if res.data:
            return [
                {
                    "symbol": row["symbol"],
                    "name_zh": row["name"],  # 轉換為 name_zh 欄位
                    "name_en": row["name"],
                    "category": "us_etf",
                    "yahoo_symbol": row["symbol"]
                }
                for row in res.data
            ]
    except Exception as e:
        logger.error(f"[MarketData] Live NASDAQ sync also failed: {e}")

    # Last-resort minimal fallback
    logger.warning("[MarketData] Returning minimal hardcoded US ETF fallback.")
    return [
        {"symbol": "SPY", "name_zh": "SPDR S&P 500 ETF", "name_en": "SPDR S&P 500 ETF", "category": "us_etf", "yahoo_symbol": "SPY"},
        {"symbol": "QQQ", "name_zh": "Invesco QQQ", "name_en": "Invesco QQQ (Nasdaq-100)", "category": "us_etf", "yahoo_symbol": "QQQ"},
        {"symbol": "VTI", "name_zh": "Vanguard Total Stock Market", "name_en": "Vanguard Total Stock Market", "category": "us_etf", "yahoo_symbol": "VTI"},
        {"symbol": "VOO", "name_zh": "Vanguard S&P 500", "name_en": "Vanguard S&P 500", "category": "us_etf", "yahoo_symbol": "VOO"},
        {"symbol": "IWM", "name_zh": "iShares Russell 2000", "name_en": "iShares Russell 2000", "category": "us_etf", "yahoo_symbol": "IWM"},
        {"symbol": "GLD", "name_zh": "SPDR Gold Shares", "name_en": "SPDR Gold Shares", "category": "us_etf", "yahoo_symbol": "GLD"},
        {"symbol": "TLT", "name_zh": "iShares Treasury Bond", "name_en": "iShares 20+ Year Treasury Bond", "category": "us_etf", "yahoo_symbol": "TLT"},
    ]


def get_index_list() -> list[dict]:
    """Return tracked index/commodity symbols."""
    return [
        {"symbol": "VIX", "name": "CBOE Volatility Index (VIX)", "category": "vix"},
        {"symbol": "OIL", "name": "WTI Crude Oil Futures", "category": "oil"},
        {"symbol": "BRENT", "name": "Brent Crude Oil Futures", "category": "oil"},
        {"symbol": "GOLD", "name": "Gold Futures", "category": "index"},
        {"symbol": "^GSPC", "name": "S&P 500 Index", "category": "index"},
        {"symbol": "^IXIC", "name": "Nasdaq Composite", "category": "index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "category": "index"},
        {"symbol": "^N225", "name": "Nikkei 225", "category": "index"},
        {"symbol": "^STOXX50E", "name": "Euro Stoxx 50", "category": "index"},
        {"symbol": "^FTSE", "name": "FTSE 100", "category": "index"},
        {"symbol": "^HSI", "name": "Hang Seng Index", "category": "index"},
        {"symbol": "TAIEX", "name": "台灣加權股價指數", "category": "index"},
        {"symbol": "WTX&", "name": "台指數夜盤", "category": "index"},
        # Crypto symbols
        {"symbol": "BTC-USD", "name": "Bitcoin (BTC)", "category": "crypto"},
        {"symbol": "ETH-USD", "name": "Ethereum (ETH)", "category": "crypto"},
        {"symbol": "SOL-USD", "name": "Solana (SOL)", "category": "crypto"},
        {"symbol": "USDT-USD", "name": "Tether (USDT)", "category": "crypto"},
        # Exchange rates
        {"symbol": "TWD=X", "name": "美元/新台幣", "category": "exchange"},
        {"symbol": "TWDJPY=X", "name": "新台幣/日圓", "category": "exchange"},
        {"symbol": "TWDEUR=X", "name": "新台幣/歐元", "category": "exchange"},
        {"symbol": "CNYTWD=X", "name": "人民幣/新台幣", "category": "exchange"},
    ]


async def get_fund_list() -> list[dict]:
    """Return tracked mutual fund symbols."""
    return [
        {"symbol": "0P000019VL", "name": "聯博-全球非投資等級債券基金AT股美元", "category": "funds"},
    ]
