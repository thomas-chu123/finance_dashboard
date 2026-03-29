"""
Tavily Search API 服務 — 一次呼叫完成「新聞搜尋 + AI 摘要」.

Tavily 的 `include_answer=True` 參數會在搜尋結果上直接生成 AI 合成摘要，
因此不需額外呼叫 Gemini，也不受 Gemini 10 RPM 限制。
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TAVILY_SEARCH_URL = "https://api.tavily.com/search"

SESSION_LABEL_MAP = {
    8: "開盤前早報",
    13: "午間快報",
    18: "收盤後晚報",
}


async def search_and_summarize(
    symbol: str,
    symbol_name: str,
    query: str,
    session_hour: int = 8,
    max_results: int = 3,
) -> tuple[list[dict], str]:
    """
    呼叫 Tavily Search API，一次完成新聞搜尋與 AI 摘要生成.

    Args:
        symbol:       股票/ETF 代碼（例如 "VTI"）
        symbol_name:  中文或英文名稱（例如 "先鋒全美ETF"）
        query:        搜尋關鍵字（由呼叫方組合 symbol + finance_hint）
        session_hour: 排程時間點（8 / 13 / 18），附加至摘要語境
        max_results:  搜尋結果數量（預設 3）

    Returns:
        (news_items, summary_text)
        news_items:   新聞列表，格式相容 brave_search_service 回傳值
                      [{"title": str, "url": str, "description": str, "published_date": str}]
        summary_text: Tavily 生成的 AI 摘要；失敗時回傳空字串
    """
    api_key = settings.tavily_search_api_key
    if not api_key:
        logger.warning("[Tavily] API key 未設定，跳過搜尋與摘要")
        return [], ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")

    # 將 query 包裹在繁體中文指令中：
    #   前置中文要求 → Tavily answer 生成時會遵循語言指示
    #   後置原始英文關鍵字 → 確保搜尋命中率不下降
    localized_query = (
        f"請以繁體中文撰寫100到150字的{session_label}市場摘要，"
        f"分析 {symbol_name}（{symbol}）的最新市場動態與投資要點。"
        f"搜尋關鍵字：{query}"
    )

    payload = {
        "api_key": api_key,
        "query": localized_query,
        "search_depth": "basic",
        "topic": "finance",
        "include_answer": "advanced",
        "max_results": max_results,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(TAVILY_SEARCH_URL, json=payload)

        if resp.status_code != 200:
            logger.error(
                f"[Tavily] HTTP {resp.status_code} for symbol={symbol}: {resp.text[:300]}"
            )
            return [], ""

        data = resp.json()

        # 將 Tavily results 轉換成相容 news_items 格式
        news_items: list[dict] = []
        for item in data.get("results", [])[:max_results]:
            news_items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", ""),
                "published_date": item.get("published_date", ""),
            })

        # Tavily answer 作為 AI 摘要
        summary_text: str = (data.get("answer") or "").strip()

        logger.info(
            f"[Tavily] symbol={symbol} → {len(news_items)} 篇新聞，"
            f"摘要長度={len(summary_text)} 字"
        )
        return news_items, summary_text

    except Exception as e:
        logger.error(f"[Tavily] 搜尋摘要失敗 symbol={symbol}: {e}")
        return [], ""
        return [], ""
