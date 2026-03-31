"""
SearXNG 自架搜尋服務 — 取代 brave_search_service（新聞搜尋部分）.

端點：https://search.skynetapp.org/search
認證：無（公開 HTTPS 端點）
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


async def search_news(query: str, count: int = 3) -> list[dict]:
    """
    呼叫 SearXNG JSON API 搜尋新聞.

    Args:
        query: 搜尋關鍵字（例如 "VTI ETF stock fund"）
        count: 回傳最多幾則新聞（預設 3）

    Returns:
        新聞列表，每筆格式：
        [{"title": str, "url": str, "description": str, "published_date": str}]
        API 失敗或 base_url 未設定時回傳空 list

    Examples:
        >>> items = await search_news("VTI ETF stock", count=3)
        >>> # [{"title": "...", "url": "...", "description": "...", "published_date": "..."}]
    """
    settings = get_settings()
    base_url = settings.searxng_base_url
    if not base_url:
        logger.warning("[SearXNG] searxng_base_url 未設定，跳過搜尋")
        return []

    params = {
        "q": query,
        "format": "json",
        "categories": "news",
        "language": "zh-TW",
        "time_range": "day",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{base_url}/search", params=params)

        if resp.status_code != 200:
            logger.error(f"[SearXNG] HTTP {resp.status_code} for query='{query}': {resp.text[:200]}")
            return []

        results = resp.json().get("results", [])[:count]
        news_items = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                # SearXNG 使用 content 欄位；對應 Brave Search 的 description
                "description": item.get("content", ""),
                "published_date": item.get("publishedDate", ""),
            }
            for item in results
        ]
        logger.info(f"[SearXNG] query='{query}' → {len(news_items)} 則新聞")
        return news_items

    except Exception as e:
        logger.error(f"[SearXNG] 搜尋失敗 query='{query}': {e}")
        return []
