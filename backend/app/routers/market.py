"""Market data router — live quotes and notification test."""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import get_supabase
from app.services.email_service import send_email, build_alert_email
from app.services.line_service import send_line_message, build_alert_message

router = APIRouter(prefix="/api/market", tags=["market"])

# Default watch-list shown on dashboard quote strip
DEFAULT_SYMBOLS = [
    {"symbol": "SPY",     "name": "S&P 500 ETF"},
    {"symbol": "QQQ",     "name": "Nasdaq 100 ETF"},
    {"symbol": "VTI",     "name": "Total Market ETF"},
    {"symbol": "GLD",     "name": "Gold ETF"},
    {"symbol": "^VIX",    "name": "VIX 恐慌指數"},
    {"symbol": "CL=F",    "name": "原油期貨"},
    {"symbol": "0050.TW", "name": "元大台灣50"},
    {"symbol": "0056.TW", "name": "元大高股息"},
]


async def _fetch_quote(meta: dict) -> dict:
    symbol = meta["symbol"]
    # Infer category for get_quote_data
    sym_upper = symbol.upper().replace(".TW", "").replace(".TWO", "")
    if ".TW" in symbol or ".TWO" in symbol:
        category = "tw_etf"
    elif symbol in ("^VIX", "VIX"):
        category = "vix"
    elif symbol in ("CL=F", "BZ=F", "OIL", "BRENT"):
        category = "oil"
    elif "=X" in symbol.upper():
        category = "exchange"
    elif symbol.upper() in ("TAIEX", "WTX&"):
        category = "index"
    else:
        category = "us_etf"
    try:
        from app.services.market_data import get_quote_data
        data = await get_quote_data(symbol, category)
        return {
            "symbol": symbol,
            "name": meta["name"],
            "category": category,
            "price": data.get("price"),
            "change": data.get("change"),
            "prev_close": data.get("prev_close"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None if data.get("success") else "Fetch failed"
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "name": meta["name"],
            "category": category,
            "price": None,
            "change": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


from pydantic import BaseModel
from typing import List

class QuoteMeta(BaseModel):
    symbol: str
    name: str

@router.get("/quotes")
async def get_quotes(symbols: Optional[str] = Query(None)):
    """Fetch live prices. Pass comma-separated symbols or use defaults."""
    if symbols:
        syms = [s.strip() for s in symbols.split(",") if s.strip()]
        metas = [{"symbol": s, "name": s} for s in syms]
    else:
        metas = DEFAULT_SYMBOLS
    results = await asyncio.gather(*[_fetch_quote(m) for m in metas])
    return list(results)

@router.post("/quotes")
async def get_quotes_batch(metas: List[QuoteMeta]):
    """Fetch live prices for a specific list of symbol/name dicts."""
    results = await asyncio.gather(*[_fetch_quote(m.model_dump()) for m in metas])
    return list(results)


from app.services.market_data import fetch_tw_etf_list, fetch_us_etf_list, get_index_list

@router.get("/symbols")
async def get_available_symbols():
    """Fetch all available symbols for the live quotes widget."""
    tw_etfs = await fetch_tw_etf_list()
    us_etfs = await fetch_us_etf_list()
    indices = get_index_list()
    return {
        "tw_etf": tw_etfs,
        "us_etf": us_etfs,
        "index": indices
    }

@router.get("/symbol-catalog")
async def get_symbol_catalog():
    """Fetch the complete symbol catalog with Yahoo Finance mappings.
    
    This endpoint returns a unified catalog of all supported symbols,
    including their Yahoo Finance mappings, display names (zh/en),
    and categories. This serves as the Single Source of Truth (SSOT)
    for symbol management across the frontend.
    
    Returns:
        dict: Symbol catalog keyed by symbol code
        {
            "VIX": {
                "symbol": "VIX",
                "yahoo_symbol": "^VIX",
                "name_zh": "...",
                "name_en": "...",
                "category": "vix",
                "domain": "finance.yahoo.com"
            },
            ...
        }
    """
    from app.services.market_data import SYMBOL_CATALOG
    return SYMBOL_CATALOG

# ─── Notification test endpoint ────────────────────────────────────────────────
test_router = APIRouter(prefix="/api/tracking", tags=["test-alert"])


@test_router.post("/{tracking_id}/test-alert")
async def test_alert(tracking_id: str):
    """Manually fire a test notification for a tracked index (with RSI support)."""
    sb = get_supabase()

    row_resp = sb.table("tracked_indices").select(
        "*, profiles(email, display_name, line_user_id, notify_email, notify_line)"
    ).eq("id", tracking_id).single().execute()

    if not row_resp.data:
        raise HTTPException(status_code=404, detail="Tracked index not found")

    item = row_resp.data
    profile = item.get("profiles") or {}
    symbol = item["symbol"]
    name = item.get("name", symbol)
    category = item.get("category", "index")
    current_price = item.get("current_price") or item.get("trigger_price") or 0
    trigger_price = item.get("trigger_price") or current_price
    channel = item.get("notify_channel", "email")
    direction = item.get("trigger_direction", "above")
    
    # RSI 數據
    trigger_mode = item.get("trigger_mode", "price")
    current_rsi = item.get("current_rsi")
    rsi_below = item.get("rsi_below")
    rsi_above = item.get("rsi_above")

    # Truncate prices to 2 decimal places (discard everything after 2 decimals, not rounding)
    current_price = int(current_price * 100) / 100
    trigger_price = int(trigger_price * 100) / 100

    results = {"email": None, "line": None}

    # Email
    if channel in ("email", "both") and profile.get("notify_email") and profile.get("email"):
        try:
            subject, body = build_alert_email(
                symbol, name, category, current_price, trigger_price, direction, tracking_id,
                trigger_mode=trigger_mode, current_rsi=current_rsi, rsi_below=rsi_below, rsi_above=rsi_above
            )
            ok = await send_email(profile["email"], subject, body)
            results["email"] = "sent" if ok else "failed (SMTP error)"
        except Exception as e:
            results["email"] = f"failed: {e}"

    # LINE
    if channel in ("line", "both") and profile.get("notify_line") and profile.get("line_user_id"):
        try:
            msg = build_alert_message(
                symbol, name, current_price, trigger_price, direction, tracking_id,
                trigger_mode=trigger_mode, current_rsi=current_rsi, rsi_below=rsi_below, rsi_above=rsi_above
            )
            resp = await send_line_message(profile["line_user_id"], msg)
            results["line"] = "sent" if resp.get("success") else f"failed: {resp.get('error')}"
        except Exception as e:
            results["line"] = f"failed: {e}"

    return {"status": "ok", "results": results, "symbol": symbol}
