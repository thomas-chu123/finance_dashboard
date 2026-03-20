import logging
import os
import httpx
import yfinance as yf
import pandas as pd
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
FINMIND_API_TOKEN = os.getenv("FinMind_API")

# Popular index symbols mapping
SYMBOL_MAP = {
    "VIX": "^VIX",
    "OIL": "CL=F",
    "CRUDE_OIL": "CL=F",
    "BRENT": "BZ=F",
    "GOLD": "GC=F",
    "TAIEX": "^TWII",
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


def _clean_tw_symbol(symbol: str) -> str:
    """Remove .TW or .TWO for FinMind API."""
    return symbol.split(".")[0]


async def fetch_finmind_adjusted_prices(
    symbol: str, start_date: str, end_date: str
) -> pd.Series:
    """Fetch adjusted prices from FinMind API (TaiwanStockPriceAdj)."""
    if not FINMIND_API_TOKEN:
        logger.warning("[MarketData] FinMind_API token not found in environment.")
        return pd.Series(dtype=float)

    clean_sym = _clean_tw_symbol(symbol)
    params = {
        "dataset": "TaiwanStockPriceAdj",
        "data_id": clean_sym,
        "start_date": start_date,
        "end_date": end_date,
        "token": FINMIND_API_TOKEN,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(FINMIND_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != 200 or not data.get("data"):
                logger.warning(f"[MarketData] FinMind returned no data for {clean_sym}: {data.get('msg')}")
                return pd.Series(dtype=float)

            df = pd.DataFrame(data["data"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            
            # TaiwanStockPriceAdj usually has 'close' as the adjusted price
            # Verify if it uses 'close' or 'adj_close'
            price_col = "close" if "close" in df.columns else df.columns[0]
            series = df[price_col].astype(float)
            series.index = series.index.normalize()
            return series.rename(symbol)
    except Exception as e:
        logger.error(f"[MarketData] FinMind error for {symbol}: {e}")
        return pd.Series(dtype=float)


async def get_quote_data(symbol: str, category: str) -> dict:
    """Fetch current price and previous close for a given symbol."""
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
    symbol: str, start_date: str, end_date: str
) -> pd.Series:
    """Return daily adjusted close price series."""
    import time
    start_time = time.time()

    # Priority 1: FinMind for Taiwan stocks if token is present
    if _is_taiwan_stock(symbol) and FINMIND_API_TOKEN:
        logger.info(f"[MarketData] Using FinMind for Taiwan adjusted prices: {symbol}")
        series = await fetch_finmind_adjusted_prices(symbol, start_date, end_date)
        if not series.empty:
            duration = time.time() - start_time
            logger.info(f"[MarketData] FinMind fetched {len(series)} days for {symbol} ({duration:.2f}s)")
            return series

    # Priority 2: yfinance (Default for US and fallback for TW)
    try:
        yf_symbol = _to_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)
        # ticker.history with auto_adjust=True returns adjusted Close for splits/dividends
        hist = await asyncio.to_thread(ticker.history, start=start_date, end=end_date, auto_adjust=True)
        duration = time.time() - start_time
        if hist.empty:
            logger.info(f"[MarketData] No yfinance data for {symbol} ({duration:.2f}s)")
            return pd.Series(dtype=float)
            
        # Standardize index: remove timezone and normalize to date
        if hist.index.tz is not None:
            hist.index = hist.index.tz_convert("UTC").tz_localize(None)
        hist.index = hist.index.normalize()
        
        logger.info(f"[MarketData] yfinance fetched {len(hist)} days for {symbol} ({duration:.2f}s)")
        return hist["Close"].rename(symbol)
    except Exception as e:
        logger.error(f"[MarketData] yfinance error for {symbol}: {e}")
        return pd.Series(dtype=float)


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
                {"symbol": row["symbol"], "name": row["name"], "category": "tw_etf"}
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
                {"symbol": row["symbol"], "name": row["name"], "category": "tw_etf"}
                for row in res.data
            ]
    except Exception as e:
        logger.error(f"[MarketData] Live TWSE sync also failed: {e}")

    # Last-resort minimal fallback
    logger.warning("[MarketData] Returning minimal hardcoded TW ETF fallback.")
    return [
        {"symbol": "0050", "name": "元大台灣50", "category": "tw_etf"},
        {"symbol": "0056", "name": "元大高股息", "category": "tw_etf"},
        {"symbol": "00878", "name": "國泰永續高股息", "category": "tw_etf"},
        {"symbol": "006208", "name": "富邦台50", "category": "tw_etf"},
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
                {"symbol": row["symbol"], "name": row["name"], "category": "us_etf"}
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
                {"symbol": row["symbol"], "name": row["name"], "category": "us_etf"}
                for row in res.data
            ]
    except Exception as e:
        logger.error(f"[MarketData] Live NASDAQ sync also failed: {e}")

    # Last-resort minimal fallback
    logger.warning("[MarketData] Returning minimal hardcoded US ETF fallback.")
    return [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "category": "us_etf"},
        {"symbol": "QQQ", "name": "Invesco QQQ (Nasdaq-100)", "category": "us_etf"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market", "category": "us_etf"},
        {"symbol": "VOO", "name": "Vanguard S&P 500", "category": "us_etf"},
        {"symbol": "IWM", "name": "iShares Russell 2000", "category": "us_etf"},
        {"symbol": "GLD", "name": "SPDR Gold Shares", "category": "us_etf"},
        {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond", "category": "us_etf"},
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
