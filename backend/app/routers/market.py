"""Market data router — live quotes and notification test."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from difflib import SequenceMatcher
from fastapi import APIRouter, HTTPException, Query
from app.database import get_supabase
from app.services.email_service import send_email, build_alert_email
from app.services.line_service import send_line_message, build_alert_message

logger = logging.getLogger(__name__)

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
    elif sym_upper.isdigit() and 4 <= len(sym_upper) <= 6:
        # Pure numeric code stored without .TW suffix (e.g. "0050" from legacy profile)
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


from app.services.market_data import fetch_tw_etf_list, fetch_us_etf_list, get_index_list, get_fund_list

@router.get("/symbols")
async def get_available_symbols():
    """Fetch all available symbols for the live quotes widget."""
    tw_etfs = await fetch_tw_etf_list()
    us_etfs = await fetch_us_etf_list()
    indices = get_index_list()
    funds = await get_fund_list()
    return {
        "tw_etf": tw_etfs,
        "us_etf": us_etfs,
        "index": indices,
        "funds": funds
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


def _calculate_match_score(query: str, symbol_data: dict) -> float:
    """計算查詢字串與符號數據的相似度分值。
    
    優先匹配策略：
    1. Symbol 前綴匹配 (最高權重，如 VT* 匹配 VTI)
    2. Symbol 包含匹配 (次高權重)
    3. 中文名稱包含匹配 (高權重，支持中文搜尋)
    4. 英文名稱包含匹配 (中等權重)
    5. 模糊相似度 (最低權重，防止 VT 匹配 VIX)
    """
    q_lower = query.lower()
    q_original = query  # 保存原始查詢（用於中文匹配）
    
    # 1. Symbol 前綴匹配 (精確開頭匹配)
    symbol = symbol_data.get("symbol", "").lower()
    if symbol.startswith(q_lower):
        return 0.95  # 最高分
    
    # 2. Symbol 包含匹配 (如 .TW 結尾)
    if q_lower in symbol:
        return 0.85
    
    # 3. 中文名稱包含匹配（支持原始中文查詢）
    name_zh = symbol_data.get("name_zh", "")
    name_zh_lower = name_zh.lower()
    
    # 支持原始中文搜尋（如 "元大" 匹配 "元大台灣50"）
    if q_original in name_zh:
        return 0.80  # 精確中文包含
    
    # 降級到小寫比較（假設不涉及大小寫轉換的中文）
    if q_lower in name_zh_lower:
        return 0.75
    
    # 4. 英文名稱包含匹配
    name_en = symbol_data.get("name_en", "").lower()
    if q_lower in name_en:
        return 0.60
    
    # 5. 模糊相似度（備選方案）
    # 只在上述精確匹配都失敗時才使用
    symbol_score = SequenceMatcher(None, q_lower, symbol).ratio()
    name_zh_score = SequenceMatcher(None, q_lower, name_zh_lower).ratio()
    name_en_score = SequenceMatcher(None, q_lower, name_en).ratio()
    
    # 加權計分（使用更嚴格的閾值）
    total_score = (symbol_score * 3.0) + (name_zh_score * 2.0) + (name_en_score * 1.0)
    fuzzy_score = total_score / 6.0  # 正規化 (0.0 - 1.0)
    
    # 只有當模糊相似度較高時才返回（防止誤比對）
    return fuzzy_score if fuzzy_score > 0.6 else 0.0


async def _fetch_latest_price(symbol: str, category: str) -> tuple:
    """獲取符號的最新價格和漲跌。
    
    Returns:
        (price, change_pct): 價格和漲跌百分比，若失敗則為 (None, None)
    """
    try:
        from app.services.market_data import get_quote_data
        data = await get_quote_data(symbol, category)
        if data.get("success"):
            return (data.get("price"), data.get("change_pct"))
    except Exception as e:
        logger.debug(f"Failed to fetch price for {symbol}: {e}")
    return (None, None)


@router.get("/search")
async def search_symbols(
    q: str = Query("", min_length=0),
    category: Optional[str] = Query(None),
    limit: int = Query(15, ge=1, le=50)
):
    """搜尋指數/基金/股票，支持按名稱、代碼、類別篩選。
    
    Args:
        q: 搜尋關鍵字 (支持 symbol、name_zh、name_en 模糊匹配)
        category: 篩選類別 (tw_etf, us_etf, fund, index, vix, oil, exchange, 等)
        limit: 返回結果數量 (1-50，預設 15)
    
    Returns:
        dict: {
            "results": [
                {
                    "symbol": "0050.TW",
                    "yahoo_symbol": "0050.TW",
                    "name_zh": "元大台灣50",
                    "name_en": "Yuanta Taiwan 50",
                    "category": "tw_etf",
                    "price": 156.25,
                    "change_pct": 0.97
                },
                ...
            ],
            "total": 3
        }
    """
    from app.services.market_data import SYMBOL_CATALOG, fetch_tw_etf_list
    
    # 若查詢字串為空，返回空結果
    if not q or len(q.strip()) == 0:
        return {"results": [], "total": 0}
    
    q = q.strip()
    results = []
    
    # 合併來自多個來源的符號
    all_symbols = []
    
    # 1. 靜態 SYMBOL_CATALOG (全球指數、期貨等)
    all_symbols.extend(SYMBOL_CATALOG.values())
    
    # 2. 台灣 ETF 列表 (動態從資料庫)
    try:
        tw_etfs = await fetch_tw_etf_list()
        all_symbols.extend(tw_etfs)
    except Exception as e:
        logger.warning(f"Failed to fetch Taiwan ETF list: {e}")
    
    # 遍歷所有符號，計算相似度
    for symbol_data in all_symbols:
        # 應用類別篩選
        if category and symbol_data.get("category") != category:
            continue
        
        # 計算相似度分值
        score = _calculate_match_score(q, symbol_data)
        
        # 使用相似度閾值 0.3 過濾結果（精確匹配得分高於 0.6，模糊匹配也需要 > 0.3）
        if score > 0.3:
            results.append((symbol_data, score))
    
    # 按相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 限制返回結果數量
    results = results[:limit]
    
    # 並行獲取最新價格（可選，若失敗不影響搜尋結果）
    response_items = []
    for item, _ in results:
        price, change_pct = await _fetch_latest_price(
            item.get("yahoo_symbol", item.get("symbol")),
            item.get("category", "us_etf")
        )
        
        response_items.append({
            "symbol": item.get("symbol"),
            "yahoo_symbol": item.get("yahoo_symbol"),
            "name_zh": item.get("name_zh"),
            "name_en": item.get("name_en"),
            "category": item.get("category"),
            "price": price,
            "change_pct": change_pct
        })
    
    return {
        "results": response_items,
        "total": len(response_items)
    }

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

    # 記錄測試警報到 alert_logs
    channel_used = [ch for ch in ("email", "line") if results.get(ch) == "sent"]
    success = bool(channel_used)
    try:
        sb.table("alert_logs").insert({
            "user_id": item["user_id"],
            "tracked_index_id": tracking_id,
            "symbol": symbol,
            "trigger_price": item.get("trigger_price"),
            "current_price": current_price,
            "current_rsi": current_rsi,
            "trigger_mode": trigger_mode,
            "channel": ",".join(channel_used) if channel_used else channel,
            "status": "sent" if success else "failed",
        }).execute()
    except Exception as log_err:
        logger.error(f"[TestAlert] Failed to save alert_log for {symbol}: {log_err}")

    return {"status": "ok", "results": results, "symbol": symbol}
