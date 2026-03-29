"""
Google Gemini API 服務 — 生成市場新聞摘要（使用 httpx REST 呼叫）.
"""
import asyncio
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-lite:generateContent"
)

SESSION_LABEL_MAP = {
    8: "開盤前早報",
    13: "午間快報",
    18: "收盤後晚報",
}


def _build_prompt(symbol: str, symbol_name: str, news_items: list[dict], session_label: str) -> str:
    """建立送給 Gemini 的中文摘要 Prompt."""
    news_blocks = []
    for i, item in enumerate(news_items, start=1):
        title = item.get("title", "（無標題）")
        description = item.get("description", "（無描述）")
        news_blocks.append(f"新聞 {i}：{title}\n摘要：{description}")

    news_text = "\n\n".join(news_blocks)
    count = len(news_items)

    return (
        f"你是一位專業的金融市場分析師。"
        f"以下是關於 {symbol_name}（{symbol}）在 {session_label} 的最新 {count} 則新聞：\n\n"
        f"{news_text}\n\n"
        "請根據上述新聞，以繁體中文撰寫一段 100-150 字的市場動態摘要。\n"
        "格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。"
    )


async def generate_market_summary(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_hour: int = 8,
) -> str:
    """
    呼叫 Gemini 1.5 Flash API 生成繁體中文市場摘要.

    Args:
        symbol: 股票/ETF 代碼
        symbol_name: 中文名稱
        news_items: 新聞列表（來自 search_news）
        session_hour: 排程小時（8/13/18），用於 prompt 標籤

    Returns:
        100-150 字繁體中文摘要；API 失敗時回傳空字串
    """
    api_key = settings.gemini_api_key
    if not api_key:
        logger.warning("[Gemini] API key 未設定，跳過摘要生成")
        return ""

    if not news_items:
        logger.info(f"[Gemini] {symbol} 無新聞，跳過摘要生成")
        return ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")
    prompt = _build_prompt(symbol, symbol_name, news_items, session_label)

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 429 指數退避重試（最多 3 次）
            for attempt in range(3):
                resp = await client.post(
                    GEMINI_URL,
                    params={"key": api_key},
                    json=payload,
                )
                if resp.status_code == 429:
                    wait = 15 * (2 ** attempt)  # 15s → 30s → 60s
                    logger.warning(f"[Gemini] 429 rate limit for {symbol}，等候 {wait}s 後重試（第 {attempt + 1} 次）")
                    await asyncio.sleep(wait)
                    continue
                break

        if resp.status_code != 200:
            logger.error(f"[Gemini] HTTP {resp.status_code} for {symbol}: {resp.text[:300]}")
            return ""

        data = resp.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        logger.info(f"[Gemini] {symbol} 摘要生成完成（{len(text)} 字）")
        return text.strip()

    except Exception as e:
        logger.error(f"[Gemini] 摘要生成失敗 {symbol}: {e}")
        return ""
