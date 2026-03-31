"""
SearXNG 自架搜尋服務 — 取代 brave_search_service（新聞搜尋部分）.

端點：https://search.skynetapp.org/search
認證：無（公開 HTTPS 端點）
"""
import logging
import re
import html
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_ascii_fallback_query(query: str) -> str:
    """提取 ASCII token 作為降級查詢，降低 WAF 對非英文關鍵字攔截風險。"""
    tokens = [t for t in re.split(r"\s+", query.strip()) if t]
    ascii_tokens = [t for t in tokens if all(ord(ch) < 128 for ch in t)]
    if ascii_tokens:
        # 保留原 token 順序並去重
        dedup: list[str] = []
        seen: set[str] = set()
        for t in ascii_tokens:
            k = t.lower()
            if k not in seen:
                seen.add(k)
                dedup.append(t)
        return " ".join(dedup)
    return query


def _parse_html_results(html_text: str, count: int) -> list[dict]:
    """從 SearXNG HTML 結果頁擷取前幾筆可用連結。"""
    # 以搜尋結果常見的 `<a href="...">title</a>` 解析，並過濾站內導覽連結。
    anchors = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.IGNORECASE | re.DOTALL)
    items: list[dict] = []
    seen: set[str] = set()

    for url, raw_title in anchors:
        if not url or url.startswith("/") or "search.skynetapp.org" in url:
            continue
        if url in seen:
            continue

        title = re.sub(r"<[^>]+>", "", raw_title)
        title = html.unescape(title).strip()
        if not title:
            continue

        seen.add(url)
        items.append(
            {
                "title": title,
                "url": url,
                "description": "",
                "published_date": "",
            }
        )
        if len(items) >= count:
            break

    return items


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

    browser_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    # 403 時逐步降級參數，提升可用性
    queries = [query]
    ascii_query = _build_ascii_fallback_query(query)
    if ascii_query != query:
        queries.append(ascii_query)

    attempt_params: list[dict[str, str]] = []
    for q in queries:
        attempt_params.extend([
            {
                "q": q,
                "format": "json",
                "categories": "finance",
                "language": "zh-TW",
                "time_range": "day",
            },
            {
                "q": q,
                "format": "json",
                "language": "zh-TW",
                "time_range": "day",
            },
            {
                "q": q,
                "format": "json",
                "categories": "news",
                "language": "zh-TW",
            },
            {
                "q": q,
                "format": "json",
            },
        ])

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for idx, params in enumerate(attempt_params, start=1):
                resp = await client.get(f"{base_url}/search", params=params, headers=browser_headers)
                if resp.status_code != 200:
                    logger.warning(
                        f"[SearXNG] attempt={idx} HTTP {resp.status_code} "
                        f"query='{params.get('q', '')[:80]}' params={list(params.keys())}"
                    )
                    # 403 走下一輪降級；其他錯誤也繼續嘗試
                    continue

                content_type = (resp.headers.get("content-type") or "").lower()
                if "application/json" in content_type:
                    payload = resp.json()
                    results = payload.get("results", [])[:count]
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
                else:
                    news_items = _parse_html_results(resp.text, count)

                logger.info(
                    f"[SearXNG] query='{query}' attempt={idx} "
                    f"actual_q='{params.get('q', '')[:80]}' → {len(news_items)} 則新聞"
                )
                return news_items

            # JSON API 可能被站台策略封鎖，最後改走 HTML 頁面再解析結果
            for idx, q in enumerate(queries, start=1):
                html_resp = await client.get(
                    f"{base_url}/search",
                    params={"q": q, "language": "zh-TW", "time_range": "day"},
                    headers=browser_headers,
                )
                if html_resp.status_code != 200:
                    logger.warning(
                        f"[SearXNG] html_fallback attempt={idx} HTTP {html_resp.status_code} "
                        f"q='{q[:80]}'"
                    )
                    continue

                news_items = _parse_html_results(html_resp.text, count)
                logger.info(
                    f"[SearXNG] html_fallback query='{query}' attempt={idx} "
                    f"actual_q='{q[:80]}' → {len(news_items)} 則新聞"
                )
                if news_items:
                    return news_items

        logger.error(f"[SearXNG] 所有嘗試皆失敗 query='{query}'")
        return []

    except Exception as e:
        logger.error(f"[SearXNG] 搜尋失敗 query='{query}': {e}")
        return []
