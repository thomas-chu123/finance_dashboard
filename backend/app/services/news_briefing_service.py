"""
AI 每日市場早報主編排服務 — 協調 Brave Search + Gemini / Tavily / SearXNG + Ollama + Supabase 寫入.

提供商由 .env 中的 AI_SUMMARY 環境變數控制：
  AI_SUMMARY=BRAVE_GEMINI    (預設) — 使用 Brave Search 取新聞 + Gemini 生成摘要
  AI_SUMMARY=TAVILY          — 使用 Tavily Search API（一次呼叫同時完成搜尋和摘要）
  AI_SUMMARY=SEARXNG_OLLAMA  — 使用自架 SearXNG 搜尋 + Ollama Direct API 生成摘要（v3）
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.config import get_settings
from app.database import get_supabase
from app.services.brave_search_service import search_news
from app.services.gemini_service import generate_market_summary
from app.services.tavily_service import search_and_summarize as tavily_search_and_summarize

logger = logging.getLogger(__name__)
settings = get_settings()

# Brave Search 免費方案限制：每次排程最多處理 20 個 unique symbols
MAX_SYMBOLS_PER_SESSION = 20

# 對應三個排程時間點（Asia/Taipei）
VALID_SESSION_HOURS = (8, 13, 18)


# 依 category 補強搜尋語意，降低抓到同名非金融內容的機率。
CATEGORY_FINANCE_HINTS: dict[str, str] = {
    "tw_etf": "台股 ETF 台灣 股票 基金",
    "us_etf": "美股 ETF 美國 股票 基金",
    "exchange": "外匯 匯率 金融 貨幣",  # 預設外匯提示（會被動態覆蓋）
    "index": "指數 大盤 股市",
    "vix": "VIX 波動率 恐慌指數",
    "oil": "原油 油價 能源 期貨",
    "crypto": "加密貨幣 比特幣 以太幣",
    "rate": "利率 央行 殖利率",
    "interest_rate": "利率 央行 殖利率",
}

# 外匯 ticker 到中文貨幣名稱的映射（用於改進搜尋提示）
CURRENCY_NAMES: dict[str, str] = {
    "USD": "美元",
    "TWD": "台幣",
    "JPY": "日圓",
    "EUR": "歐元",
    "GBP": "英鎊",
    "CNY": "人民幣",
    "HKD": "港幣",
    "SGD": "新加坡幣",
    "AUD": "澳幣",
    "CAD": "加幣",
    "CHF": "瑞士法郎",
    "NZD": "紐西蘭幣",
    "INR": "印度盧比",
    "RMB": "人民幣",
    "KRW": "韓圓",
    "SEK": "瑞典克朗",
    "NOK": "挪威克朗",
    "MXN": "墨西哥披索",
    "ZAR": "南非蘭特",
    "BRL": "巴西雷亞爾",
    "RUB": "俄羅斯盧布",
    "TRY": "土耳其里拉",
}


def _parse_exchange_pair(symbol: str) -> tuple[str, str] | None:
    """
    解析外匯 ticker (如 TWDJPY=X) 為 (base_curr, quote_curr)。
    
    常見格式：XXX[YYY] 其中 XXX 和 YYY 各為 3 字母貨幣代碼，加上 =X 後綴。
    
    Returns:
        (base_code, quote_code) 如 ("TWD", "JPY")，或 None 若無法解析
    """
    base_symbol = symbol.replace("=X", "").upper()
    if len(base_symbol) != 6:
        return None
    base_curr = base_symbol[:3]
    quote_curr = base_symbol[3:6]
    return (base_curr, quote_curr)


def _build_finance_hint(category: str, symbol: str = "") -> str:
    """依類別回傳搜尋提示詞（含中英文金融詞）."""
    key = (category or "").strip().lower()
    
    # 若為外匯類別且 symbol 可解析，動態生成貨幣對提示
    if key == "exchange" and symbol:
        pair = _parse_exchange_pair(symbol)
        if pair:
            base_code, quote_code = pair
            base_name = CURRENCY_NAMES.get(base_code, base_code)
            quote_name = CURRENCY_NAMES.get(quote_code, quote_code)
            # 避免出現「美元 美元」這類重複
            if base_name != quote_name:
                return f"外匯 匯率 {base_name} {quote_name} finance market"
    
    hint = CATEGORY_FINANCE_HINTS.get(key)
    if hint:
        return f"{hint} finance market"
    return "金融 市場 股票 ETF 指數 finance market"


def _build_search_query(symbol: str, symbol_name: str, category: str) -> str:
    """組合搜尋字串：name + symbol + category hint（避免重複）."""
    finance_hint = _build_finance_hint(category, symbol=symbol)
    if symbol_name == symbol:
        return f"{symbol_name} {finance_hint}"
    return f"{symbol_name} {symbol} {finance_hint}"


def _get_nearest_session_time() -> datetime:
    """
    計算最近一次有效排程時間（08:00、13:00 或 18:00 Asia/Taipei）.

    Returns:
        最近整點排程的 UTC datetime
    """
    # Asia/Taipei = UTC+8
    taipei_offset = timedelta(hours=8)
    now_utc = datetime.now(timezone.utc)
    now_taipei = now_utc + taipei_offset

    # 找最近已過的排程時間
    today_sessions = [
        now_taipei.replace(hour=h, minute=0, second=0, microsecond=0)
        for h in VALID_SESSION_HOURS
    ]
    past_sessions = [t for t in today_sessions if t <= now_taipei]

    if past_sessions:
        nearest_taipei = max(past_sessions)
    else:
        # 今天尚無排程執行，取前一天 18:00
        yesterday = now_taipei - timedelta(days=1)
        nearest_taipei = yesterday.replace(hour=18, minute=0, second=0, microsecond=0)

    # 轉回 UTC
    return nearest_taipei - taipei_offset


async def run_market_briefing_session(override_session_time: datetime | None = None) -> dict:
    """
    執行一次市場早報排程：
      1. 查詢 tracked_indices 中所有 is_active=True 的唯一 symbol
      2. 計算本次 session_time（若 override_session_time 提供則使用之，否則計算最近排程時間）
      3. 對每個 symbol 呼叫設定的搜尋 + AI 摘要提供商
      4. Upsert 結果至 market_briefings 表
      5. 回傳統計 {"total": n, "success": n, "failed": n}

    Args:
        override_session_time: 若提供，強制使用此時間戳記（用於手動觸發，方便前端 polling 追蹤）

    Returns:
        {"total": int, "success": int, "failed": int}
    """
    sb = get_supabase()
    session_time = override_session_time if override_session_time is not None else _get_nearest_session_time()
    session_hour = (session_time + timedelta(hours=8)).hour  # 轉回 Taipei hour 供 prompt 使用

    logger.info(f"[Briefing] 排程開始，session_time={session_time.isoformat()}")

    # 1. 查詢所有 is_active=True 的唯一 symbol
    try:
        res = sb.table("tracked_indices").select("symbol, name, category").eq("is_active", True).execute()
    except Exception as e:
        logger.error(f"[Briefing] 查詢 tracked_indices 失敗: {e}")
        return {"total": 0, "success": 0, "failed": 0}

    if not res.data:
        logger.info("[Briefing] 無 is_active=True 的追蹤項目，跳過排程")
        return {"total": 0, "success": 0, "failed": 0}

    # 去重（同 symbol 可能被多位使用者追蹤）
    seen: set[str] = set()
    symbols: list[dict] = []
    for row in res.data:
        sym = row.get("symbol", "")
        if sym and sym not in seen:
            seen.add(sym)
            symbols.append({
                "symbol": sym,
                "name": row.get("name", sym),
                "category": row.get("category", "us_etf"),
            })

    # 限制上限
    if len(symbols) > MAX_SYMBOLS_PER_SESSION:
        logger.warning(
            f"[Briefing] unique symbol 數量 {len(symbols)} 超過上限 {MAX_SYMBOLS_PER_SESSION}，"
            "截斷超額 symbols"
        )
        symbols = symbols[:MAX_SYMBOLS_PER_SESSION]

    total = len(symbols)
    success_count = 0
    failed_count = 0

    use_tavily = settings.ai_summary.upper() == "TAVILY"
    use_searxng_ollama = settings.ai_summary.upper() == "SEARXNG_OLLAMA"

    if use_tavily:
        provider_label = "Tavily"
    elif use_searxng_ollama:
        provider_label = "SearXNG+Ollama"
    else:
        provider_label = "Brave+Gemini"
    logger.info(f"[Briefing] 使用摘要提供商：{provider_label}")

    # 2. 逐個 symbol 處理
    for item in symbols:
        symbol = item["symbol"]
        symbol_name = item["name"]
        category = item.get("category", "us_etf")
        try:
            search_query = _build_search_query(symbol, symbol_name, category)

            if use_tavily:
                # --- Tavily 路徑：搜尋 + 摘要一次完成 ---
                news_items, summary_text = await tavily_search_and_summarize(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    query=search_query,
                    session_hour=session_hour,
                )
            elif use_searxng_ollama:
                # --- SearXNG + Ollama Direct 路徑（v3）---
                from app.services.searxng_service import search_news as searxng_search_news
                from app.services.ollama_service import generate_market_summary as ollama_generate
                news_items = await searxng_search_news(query=search_query, count=3)
                if not news_items:
                    # 保底：SearXNG 被 403 或無結果時，改由 Brave 補新聞來源。
                    logger.warning(
                        f"[Briefing] SearXNG 無結果，改用 Brave fallback symbol={symbol}"
                    )
                    news_items = await search_news(query=search_query, count=3)
                summary_text = await ollama_generate(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    news_items=news_items,
                    session_hour=session_hour,
                )
                # Ollama 無 rate limit，不需 sleep(7)
            else:
                # --- Brave + Gemini 路徑（原有邏輯）---
                news_items = await search_news(
                    query=search_query,
                    count=3,
                )

                # 生成 AI 摘要
                summary_text = await generate_market_summary(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    news_items=news_items,
                    session_hour=session_hour,
                )

                # Gemini free tier 限制 10 RPM，每次呼叫後等 7 秒（≈ 8.5 RPM）
                if news_items:
                    await asyncio.sleep(7)

            status = "completed" if summary_text else "failed"
            error_message = None if summary_text else f"{provider_label} 回傳空摘要"

            # Upsert 至 market_briefings
            sb.table("market_briefings").upsert(
                {
                    "session_time": session_time.isoformat(),
                    "symbol": symbol,
                    "symbol_name": symbol_name,
                    "news_json": news_items,
                    "summary_text": summary_text,
                    "status": status,
                    "error_message": error_message,
                },
                on_conflict="session_time,symbol",
            ).execute()

            if status == "completed":
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"[Briefing] 處理 {symbol} 失敗: {e}")
            failed_count += 1
            # 記錄失敗狀態
            try:
                sb.table("market_briefings").upsert(
                    {
                        "session_time": session_time.isoformat(),
                        "symbol": symbol,
                        "symbol_name": symbol_name,
                        "news_json": [],
                        "summary_text": None,
                        "status": "failed",
                        "error_message": str(e),
                    },
                    on_conflict="session_time,symbol",
                ).execute()
            except Exception as db_err:
                logger.error(f"[Briefing] 寫入失敗狀態至 DB 也失敗 {symbol}: {db_err}")

        # 保護 Brave+Gemini rate limit；Tavily 不需要此延遲但保留最小間隔
        await asyncio.sleep(1 if not use_tavily else 0.2)

    stats = {"total": total, "success": success_count, "failed": failed_count}
    logger.info(f"[Briefing] 排程完成: {stats}")
    return stats
