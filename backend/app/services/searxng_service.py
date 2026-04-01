"""
SearXNG 自架搜尋服務 — 取代 brave_search_service（新聞搜尋部分）.

端點：https://search.skynetapp.org/search
認證：無（公開 HTTPS 端點）
重試策略：指數退避（1s, 2s, 4s）應對暫時性網路故障與速率限制
"""
import logging
import re
import html
import httpx
import asyncio
from app.config import get_settings

logger = logging.getLogger(__name__)


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
    headers: dict,
    max_retries: int = 3,
    timeout: float = 20.0,
) -> httpx.Response | None:
    """
    帶指數退避重試的 HTTP GET。

    當遇到臨時性錯誤（502, 503, timeout）時，自動重試；
    成功 (200) 或永久失敗 (4xx except 429) 時直接返回。

    Args:
        client: httpx.AsyncClient
        url: 請求 URL
        params: 查詢參數
        headers: HTTP 頭
        max_retries: 最多重試次數（含首次）
        timeout: 單次請求超時秒數

    Returns:
        httpx.Response 若成功，或 None 若所有重試皆失敗
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=timeout)
            
            # 200 直接返回
            if resp.status_code == 200:
                return resp
            
            # 429 (rate limit) / 502 / 503 / 504 應重試
            should_retry = resp.status_code in (429, 502, 503, 504)
            
            if should_retry and attempt < max_retries:
                wait_sec = 2 ** (attempt - 1)  # 1s, 2s, 4s, ...
                logger.warning(
                    f"[SearXNG] HTTP {resp.status_code} 將在 {wait_sec}s 後重試 "
                    f"(attempt {attempt}/{max_retries}) q='{params.get('q', '')[:60]}'"
                )
                await asyncio.sleep(wait_sec)
                continue
            
            # 其他 4xx 或無重試了 → 返回此次響應
            return resp
            
        except (httpx.TimeoutException, asyncio.TimeoutError) as e:
            if attempt < max_retries:
                wait_sec = 2 ** (attempt - 1)
                logger.warning(
                    f"[SearXNG] Timeout/ConnectionError，將在 {wait_sec}s 後重試 "
                    f"(attempt {attempt}/{max_retries}) q='{params.get('q', '')[:60]}'"
                )
                await asyncio.sleep(wait_sec)
                continue
            logger.error(f"[SearXNG] 所有重試皆超時 q='{params.get('q', '')[:60]}': {e}")
            return None
            
        except Exception as e:
            logger.error(f"[SearXNG] HTTP 請求異常 (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait_sec = 2 ** (attempt - 1)
                await asyncio.sleep(wait_sec)
                continue
            return None
    
    return None


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
                resp = await _fetch_with_retry(
                    client=client,
                    url=f"{base_url}/search",
                    params=params,
                    headers=browser_headers,
                    max_retries=3,
                    timeout=20.0,
                )
                
                if resp is None:
                    logger.warning(
                        f"[SearXNG] JSON-attempt={idx} 所有重試皆失敗 "
                        f"q='{params.get('q', '')[:80]}' categories={params.get('categories', 'N/A')} "
                        f"time_range={params.get('time_range', 'N/A')}"
                    )
                    continue
                
                if resp.status_code != 200:
                    logger.warning(
                        f"[SearXNG] JSON-attempt={idx} HTTP {resp.status_code} "
                        f"query='{params.get('q', '')[:80]}' categories={params.get('categories', 'N/A')} "
                        f"time_range={params.get('time_range', 'N/A')}"
                    )
                    continue

                content_type = (resp.headers.get("content-type") or "").lower()
                if "application/json" in content_type:
                    payload = resp.json()
                    all_results = payload.get("results", [])
                    results = all_results[:count]
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
                    
                    logger.info(
                        f"[SearXNG] JSON-attempt={idx} query='{query}' "
                        f"actual_q='{params.get('q', '')[:80]}' "
                        f"categories={params.get('categories', 'N/A')} time_range={params.get('time_range', 'N/A')} "
                        f"→ total={len(all_results)} results, filtered={len(news_items)} items"
                    )
                    if news_items:
                        return news_items
                else:
                    news_items = _parse_html_results(resp.text, count)
                    logger.info(
                        f"[SearXNG] JSON-attempt={idx} (HTML response) query='{query}' "
                        f"actual_q='{params.get('q', '')[:80]}' "
                        f"→ parsed {len(news_items)} items from HTML"
                    )
                    if news_items:
                        return news_items

            # JSON API 可能被站台策略封鎖，最後改走 HTML 頁面再解析結果
            logger.info(f"[SearXNG] 所有 JSON 嘗試皆無可用結果或被擋，開始 HTML fallback...")
            for idx, q in enumerate(queries, start=1):
                html_resp = await _fetch_with_retry(
                    client=client,
                    url=f"{base_url}/search",
                    params={"q": q, "language": "zh-TW", "time_range": "day"},
                    headers=browser_headers,
                    max_retries=3,
                    timeout=20.0,
                )
                
                if html_resp is None:
                    logger.warning(
                        f"[SearXNG] HTML-fallback={idx} 所有重試皆失敗 q='{q[:80]}'"
                    )
                    continue
                
                if html_resp.status_code != 200:
                    logger.warning(
                        f"[SearXNG] HTML-fallback={idx} HTTP {html_resp.status_code} "
                        f"q='{q[:80]}'"
                    )
                    continue

                news_items = _parse_html_results(html_resp.text, count)
                logger.info(
                    f"[SearXNG] HTML-fallback={idx} query='{query}' "
                    f"actual_q='{q[:80]}' → parsed {len(news_items)} items from HTML"
                )
                if news_items:
                    return news_items

        logger.error(
            f"[SearXNG] 所有嘗試皆失敗（JSON + HTML fallback 皆為 0 or 被擋）query='{query}'"
        )
        return []

    except Exception as e:
        logger.error(f"[SearXNG] 搜尋失敗 query='{query}': {e}")
        return []
