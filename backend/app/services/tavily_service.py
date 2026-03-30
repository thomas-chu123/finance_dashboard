"""
Tavily Search API 服務 — 一次呼叫完成「新聞搜尋 + AI 摘要」.

Tavily 的 `include_answer=True` 參數會在搜尋結果上直接生成 AI 合成摘要，
因此不需額外呼叫 Gemini，也不受 Gemini 10 RPM 限制。
"""
import asyncio
import datetime
import logging
import re
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def _format_citations(raw_answer: str) -> str:
    """將 Tavily answer 中的 【URL】 引用標記轉為編號來源註記格式.

    輸出範例::

        市場今日波動加劇[1]，科技股受賣壓影響明顯[2]。

        參考來源：
        [1] https://example.com/news/1
        [2] https://example.com/news/2
    """
    urls: list[str] = []

    def _replace(match: re.Match) -> str:
        url = match.group(1)
        if url not in urls:
            urls.append(url)
        return f"[{urls.index(url) + 1}]"

    text = re.sub(r"【(https?://[^】]*)】", _replace, raw_answer).strip()

    if urls:
        refs = "\n".join(f"[{i + 1}] {u}" for i, u in enumerate(urls))
        text = f"{text}\n\n參考來源：\n{refs}"

    return text


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

    year_of_today = datetime.datetime.now().year

    # 結構化指令：明確要求字數、段落結構、繁體中文
    # 後置英文關鍵字確保 Tavily 搜尋命中率不下降
    localized_query = (
        f"請以繁體中文撰寫 150 至 200 字的詳細{session_label}市場分析報告，"
        f"針對 {symbol_name}（{symbol}）涵蓋以下三個面向，以完整段落呈現，勿使用條列：\n"
        f"(1) 近期主要市場動態與價格走勢；\n"
        f"(2) 驅動因素（總體經濟、產業趨勢、政策等）；\n"
        f"(3) 投資者應關注的機會與風險。\n"
        f"搜尋關鍵字：{query}\n"
        f"{year_of_today} 年內的新聞為主"
    )

    payload = {
        "api_key": api_key,
        "query": localized_query,
        "search_depth": "basic",     # 深度爬取頁面完整內文
        "topic": "news",
        "include_answer": "basic",    # 啟用詳盡 AI 合成摘要
        "include_raw_content": False,     # 傳入完整頁面文字作為分析素材
        "time_range": "week",             # 搜尋過去 24 小時內的新聞
        "max_results": max_results,                # 更多來源 → 更豐富的分析依據
    }

    # ── 內部單次請求（含可重試例外的判斷） ────────────────────────────
    async def _do_request(q: str) -> tuple[list[dict], str]:
        """發送一次 Tavily 請求；HTTP 5xx / 429 / 連線問題時拋出例外，讓 retry 層處理。"""
        current_payload = {**payload, "query": q}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(TAVILY_SEARCH_URL, json=current_payload)

        if resp.status_code in (429, 500, 502, 503, 504):
            # 可重試的 HTTP 狀態碼
            raise httpx.HTTPStatusError(
                f"HTTP {resp.status_code}",
                request=resp.request,
                response=resp,
            )
        if resp.status_code != 200:
            logger.error(
                f"[Tavily] HTTP {resp.status_code} for symbol={symbol}: {resp.text[:300]}"
            )
            return [], ""

        data = resp.json()
        news: list[dict] = []
        for item in data.get("results", [])[:max_results]:
            news.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", ""),
                "published_date": item.get("published_date", ""),
            })
        raw_answer: str = (data.get("answer") or "").strip()
        summary = _format_citations(raw_answer)
        return news, summary

    # ── Retry 包裝（最多 3 次，指數退避 1 / 2 / 4 秒） ─────────────────
    MAX_RETRIES = 3
    RETRYABLE = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.RemoteProtocolError,
        httpx.HTTPStatusError,
    )

    news_items: list[dict] = []
    summary_text: str = ""
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            news_items, summary_text = await _do_request(localized_query)
            last_error = None
            break  # 成功，跳出 retry 迴圈
        except RETRYABLE as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = 2 ** (attempt - 1)  # 1s → 2s → 4s
                logger.warning(
                    f"[Tavily] symbol={symbol} 第 {attempt} 次失敗，"
                    f"{wait}s 後重試: {e}"
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    f"[Tavily] symbol={symbol} 已重試 {MAX_RETRIES} 次仍失敗: {e}"
                )
        except Exception as e:
            logger.error(f"[Tavily] 搜尋摘要失敗 symbol={symbol}: {e}")
            return [], ""

    if last_error is not None:
        return [], ""

    # ── Fallback：若繁中結構化 prompt 無摘要，改用精簡英文 query 再試一次 ──
    if not summary_text:
        fallback_query = f"{symbol} {symbol_name} stock news {datetime.datetime.now().year}"
        logger.info(f"[Tavily] symbol={symbol} 摘要為空，嘗試英文 fallback query")
        try:
            news_items, summary_text = await _do_request(fallback_query)
        except Exception as e:
            logger.warning(f"[Tavily] symbol={symbol} fallback 也失敗: {e}")

    logger.info(
        f"[Tavily] symbol={symbol} → {len(news_items)} 篇新聞，"
        f"摘要長度={len(summary_text)} 字"
    )
    return news_items, summary_text
