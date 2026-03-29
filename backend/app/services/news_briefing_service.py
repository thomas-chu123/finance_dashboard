"""
AI 每日市場早報主編排服務 — 協調 Brave Search + Gemini + Supabase 寫入.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.database import get_supabase
from app.services.brave_search_service import search_news
from app.services.gemini_service import generate_market_summary

logger = logging.getLogger(__name__)

# Brave Search 免費方案限制：每次排程最多處理 20 個 unique symbols
MAX_SYMBOLS_PER_SESSION = 20

# 對應三個排程時間點（Asia/Taipei）
VALID_SESSION_HOURS = (8, 13, 18)


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


async def run_market_briefing_session() -> dict:
    """
    執行一次市場早報排程：
      1. 查詢 tracked_indices 中所有 is_active=True 的唯一 symbol
      2. 計算本次 session_time
      3. 對每個 symbol 呼叫 Brave Search + Gemini
      4. Upsert 結果至 market_briefings 表
      5. 回傳統計 {"total": n, "success": n, "failed": n}

    Returns:
        {"total": int, "success": int, "failed": int}
    """
    sb = get_supabase()
    session_time = _get_nearest_session_time()
    session_hour = (session_time + timedelta(hours=8)).hour  # 轉回 Taipei hour 供 prompt 使用

    logger.info(f"[Briefing] 排程開始，session_time={session_time.isoformat()}")

    # 1. 查詢所有 is_active=True 的唯一 symbol
    try:
        res = sb.table("tracked_indices").select("symbol, name").eq("is_active", True).execute()
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
            symbols.append({"symbol": sym, "name": row.get("name", sym)})

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

    # 2. 逐個 symbol 處理
    for item in symbols:
        symbol = item["symbol"]
        symbol_name = item["name"]
        try:
            # 搜尋新聞（避免 symbol_name == symbol 時產生重複字串）
            search_query = symbol_name if symbol_name == symbol else f"{symbol_name} {symbol}"
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
            error_message = None if summary_text else "Gemini 回傳空摘要"

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

        # 保護 Gemini rate limit（15 RPM）
        await asyncio.sleep(1)

    stats = {"total": total, "success": success_count, "failed": failed_count}
    logger.info(f"[Briefing] 排程完成: {stats}")
    return stats
