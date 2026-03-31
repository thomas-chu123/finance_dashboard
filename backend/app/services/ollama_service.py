"""
Ollama Direct API 摘要服務 — 取代 gemini_service.

端點：http://192.168.0.26:11434/v1/chat/completions（OpenAI 相容格式）
認證：無（Ollama Direct 不需要認證）
模型：gpt-oss:20b（由 OLLAMA_MODEL 環境變數控制）

注意：此服務直連內網 Ollama 實例，不透過 OpenWebUI proxy。
後端伺服器必須與 192.168.0.26 在同一網段才能存取。
"""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

SESSION_LABEL_MAP = {
    8: "開盤前早報",
    13: "午間快報",
    18: "收盤後晚報",
}


def _build_prompt(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_label: str,
) -> str:
    """建立送給 Ollama 的繁體中文摘要 Prompt."""
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
        "請根據上述新聞，以繁體中文（非簡體中文）撰寫一段 100-150 字的市場動態摘要。\n"
        "格式：純文字，無需標題，包含：(1) 主要市場動態 (2) 潛在影響 (3) 投資者關注要點。"
    )


async def generate_market_summary(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_hour: int = 8,
) -> str:
    """
    呼叫 Ollama gpt-oss:20b 生成繁體中文市場摘要.

    Args:
        symbol: 股票/ETF 代碼（例如 "VTI"）
        symbol_name: 中文名稱（例如 "先鋒整體市場ETF"）
        news_items: 由 searxng_service.search_news 回傳的新聞 list
        session_hour: 排程小時（8/13/18），用於 prompt 標籤

    Returns:
        100-150 字繁體中文摘要字串；失敗時回傳空字串 ""

    Examples:
        >>> summary = await generate_market_summary("VTI", "先鋒整體市場ETF", news_items, 8)
        >>> # "美股市場今日開盤前..."
    """
    settings = get_settings()
    base_url = settings.ollama_base_url
    model = settings.ollama_model

    if not base_url:
        logger.warning("[Ollama] ollama_base_url 未設定，跳過摘要生成")
        return ""
    if not news_items:
        logger.info(f"[Ollama] {symbol} 無新聞，跳過摘要生成")
        return ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")
    prompt = _build_prompt(symbol, symbol_name, news_items, session_label)

    # 使用 OpenAI 相容 /v1/chat/completions（Ollama ≥ 0.1.14 原生支援）
    # 不傳 Authorization header：Ollama Direct 無需認證
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 400,
        "stream": False,
    }

    try:
        # timeout=120s：20B 模型首次推理（冷啟動）可能需要 60-90s
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        if resp.status_code != 200:
            logger.error(f"[Ollama] HTTP {resp.status_code} for {symbol}: {resp.text[:200]}")
            return ""

        choices = resp.json().get("choices", [])
        if not choices:
            logger.error(f"[Ollama] 回應無 choices，symbol={symbol}")
            return ""

        summary = choices[0].get("message", {}).get("content", "").strip()
        logger.info(f"[Ollama] {symbol} 摘要生成成功（{len(summary)} 字）")
        return summary

    except Exception as e:
        logger.error(f"[Ollama] 摘要生成失敗 symbol={symbol}: {e}")
        return ""
