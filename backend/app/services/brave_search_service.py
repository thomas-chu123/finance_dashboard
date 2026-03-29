"""
Brave Search News API 服務 — 搜尋指定 symbol 的最新新聞.
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BRAVE_NEWS_URL = "https://api.search.brave.com/res/v1/news/search"


async def search_news(query: str, count: int = 3) -> list[dict]:
    """
    使用 Brave Search News API 搜尋最新新聞.

    Args:
        query: 搜尋關鍵字（例如 "台積電 TSM"）
        count: 回傳新聞數量（預設 3）

    Returns:
        新聞列表，每筆格式：
        [{"title": str, "url": str, "description": str, "published_date": str}]
        API 失敗或 key 未設定時回傳空 list
    """
    api_key = settings.brave_search_api_key
    if not api_key:
        logger.warning("[BraveSearch] API key 未設定，跳過搜尋")
        return []

    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "count": count,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(BRAVE_NEWS_URL, headers=headers, params=params)

        if resp.status_code != 200:
            logger.error(f"[BraveSearch] HTTP {resp.status_code} for query='{query}': {resp.text[:200]}")
            return []

        data = resp.json()
        results = data.get("results", [])

        news_items = []
        for item in results[:count]:
            news_items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "published_date": item.get("age", ""),
            })

        logger.info(f"[BraveSearch] query='{query}' → {len(news_items)} 則新聞")
        return news_items

    except Exception as e:
        logger.error(f"[BraveSearch] 搜尋失敗 query='{query}': {e}")
        return []
